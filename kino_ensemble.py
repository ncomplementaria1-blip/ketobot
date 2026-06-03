"""
Sistema de ensemble Kino — implementa el brief de Alejandra.

18+ modelos:
  Clásicos: frecuencias en 6 ventanas + DUE + Bayesiano + Markov 1°
  ML: HMM, XGBoost, MLP, RNN custom NumPy, Grafo (PageRank+Eigenvector)
  Evolutivo: Algoritmo Genético × 3 pesos distintos
  Temporal: Condicional al día de la semana

Consolida con:
  ★★★ Super-Consenso Ensemble (promedio ponderado normalizado)
  ★ Consenso por Votación (top-14 más votados)

Salida: Excel matricial con columnas negras separadoras cada 5 números.

HONESTIDAD MATEMÁTICA (sección 7 del brief):
  - χ² de uniformidad p ≈ 0.97 → sorteo justo, sin sesgos
  - Modelos ML hacen overfitting sobre ruido
  - Ninguna combinación supera 1/4.457.400 (probabilidad real)
  - Sistema 7-9 aciertos = compatible con azar puro (media 7.84)
"""
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from scipy import stats as sst
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

# ==================== CONFIG ====================
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "analisis_kino", "kino_data.json")
OUT = os.path.join(BASE, "analisis_kino", "kino_3235_ensemble.xlsx")

TARGET_SORTEO = 3235
N_DRAW = 14
N_MAX = 25
STABLE_START = 1000  # filtro de período estable

PALETTE = {
    1: ("B8D8E8", "000000"), 2: ("E63946", "000000"), 3: ("A8E6A3", "000000"),
    4: ("F2C879", "000000"), 5: ("7B3FA0", "FFFFFF"), 6: ("1ABC9C", "000000"),
    7: ("FF8FCF", "000000"), 8: ("2980B9", "FFFFFF"), 9: ("7F8C8D", "000000"),
    10: ("A98E33", "FFFFFF"), 11: ("F1C40F", "000000"), 12: ("C8A2D8", "000000"),
    13: ("1ABEDB", "000000"), 14: ("5DADE2", "000000"), 15: ("F39C12", "000000"),
    16: ("1A1A1A", "FFFFFF"), 17: ("EC407A", "FFFFFF"), 18: ("C5E1A5", "000000"),
    19: ("8B7500", "FFFFFF"), 20: ("C0392B", "FFFFFF"), 21: ("00BCD4", "000000"),
    22: ("BDBDBD", "000000"), 23: ("4DD0E1", "000000"), 24: ("D7B98E", "FFFFFF"),
    25: ("F8BBD0", "000000"),
}

# ==================== DATA ====================
def day_of_week(sorteo):
    return ["domingo", "miercoles", "viernes"][sorteo % 3]


def load_draws():
    with open(DATA, encoding="utf-8") as f:
        draws = json.load(f)
    draws.sort(key=lambda d: d["sorteo"])
    return draws


def to_matrix(draws):
    """Matriz binaria N_sorteos x 25."""
    M = np.zeros((len(draws), N_MAX), dtype=np.int8)
    for i, d in enumerate(draws):
        for n in d["nums"]:
            M[i, n - 1] = 1
    return M


def safe_norm(x):
    x = np.asarray(x, dtype=float)
    rng = x.max() - x.min()
    return (x - x.min()) / (rng + 1e-9) if rng > 0 else np.full_like(x, 0.5)


def top14(scores):
    return sorted((np.argsort(-np.asarray(scores))[:N_DRAW] + 1).tolist())


# ==================== MODELOS CLÁSICOS ====================
def freq_window(M, window=None):
    Mw = M[-window:] if window else M
    return Mw.sum(axis=0)


def gaps(M):
    g = np.zeros(N_MAX, dtype=int)
    for n in range(N_MAX):
        col = M[:, n]
        idx_last = np.where(col == 1)[0]
        g[n] = (len(M) - 1 - idx_last[-1]) if len(idx_last) else len(M)
    return g


def due_score(M):
    g = gaps(M)
    p = M.mean(axis=0)
    expected_gap = (1 - p) / p
    return g - expected_gap


def bayesian_score(p_global, p_500, p_300, p_100, p_markov, g):
    g_norm = safe_norm(g)
    return (0.20 * safe_norm(p_global) + 0.25 * safe_norm(p_500) +
            0.20 * safe_norm(p_300) + 0.15 * safe_norm(p_100) +
            0.10 * safe_norm(p_markov) + 0.10 * g_norm)


def markov_1st(M, last_draw):
    """P(j en t+1 | i en t), promediado sobre los i del último sorteo."""
    co = np.zeros((N_MAX, N_MAX))
    base = M[:-1].sum(axis=0)
    for t in range(len(M) - 1):
        for i in np.where(M[t] == 1)[0]:
            for j in np.where(M[t + 1] == 1)[0]:
                co[i, j] += 1
    transition = co / (base[:, None] + 1e-9)
    scores = np.zeros(N_MAX)
    for i in [n - 1 for n in last_draw]:
        scores += transition[i]
    return scores / max(1, len(last_draw))


# ==================== MODELOS ML ====================
def hmm_scores(M):
    from hmmlearn.hmm import GaussianHMM
    feats = np.column_stack([
        M.sum(axis=1),
        np.array([sum(1 for j in range(N_MAX) if M[i, j] and (j + 1) <= 12) for i in range(len(M))]),
        np.array([sum(1 for j in range(N_MAX) if M[i, j] and (j + 1) % 2 == 1) for i in range(len(M))]),
    ]).astype(float)
    try:
        model = GaussianHMM(n_components=5, covariance_type="diag",
                            n_iter=20, random_state=42)
        model.fit(feats)
        states = model.predict(feats)
        last_state = states[-1]
        in_state = M[states == last_state]
        return in_state.mean(axis=0) if len(in_state) else M.mean(axis=0)
    except Exception:
        return M.mean(axis=0)


def xgb_scores(M, window=10):
    import xgboost as xgb
    X, Y = [], []
    for t in range(window, len(M)):
        X.append(M[t - window:t].flatten())
        Y.append(M[t])
    X = np.array(X, dtype=np.float32); Y = np.array(Y, dtype=np.int32)
    scores = np.zeros(N_MAX)
    last_window = M[-window:].flatten().reshape(1, -1).astype(np.float32)
    for n in range(N_MAX):
        if Y[:, n].sum() == 0 or Y[:, n].sum() == len(Y):
            scores[n] = Y[:, n].mean()
            continue
        clf = xgb.XGBClassifier(
            n_estimators=60, max_depth=4, learning_rate=0.1,
            use_label_encoder=False, eval_metric="logloss", verbosity=0,
            n_jobs=1, random_state=42,
        )
        clf.fit(X, Y[:, n])
        scores[n] = clf.predict_proba(last_window)[0, 1]
    return scores


def mlp_scores(M, window=15):
    from sklearn.neural_network import MLPClassifier
    X, Y = [], []
    for t in range(window, len(M)):
        X.append(M[t - window:t].flatten())
        Y.append(M[t])
    X = np.array(X, dtype=np.float32); Y = np.array(Y, dtype=np.int32)
    last_window = M[-window:].flatten().reshape(1, -1).astype(np.float32)
    try:
        clf = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=100,
                            random_state=42, early_stopping=True)
        clf.fit(X, Y)
        proba = np.array([
            (clf.predict_proba(last_window)[i][0, 1] if clf.predict_proba(last_window)[i].shape[1] == 2 else 0.5)
            for i in range(N_MAX)
        ])
        return proba
    except Exception:
        return M.mean(axis=0)


def rnn_custom_scores(M, window=20, hidden=32, epochs=3, lr=0.01):
    """RNN simple en NumPy puro."""
    rng = np.random.default_rng(42)
    Wxh = rng.standard_normal((N_MAX, hidden)) * 0.1
    Whh = rng.standard_normal((hidden, hidden)) * 0.1
    Why = rng.standard_normal((hidden, N_MAX)) * 0.1
    bh = np.zeros(hidden); by = np.zeros(N_MAX)

    def sigmoid(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

    seqs = [(M[t - window:t], M[t]) for t in range(window, len(M))]
    for _ in range(epochs):
        for X, y in seqs:
            h = np.zeros(hidden)
            for x in X:
                h = np.tanh(x @ Wxh + h @ Whh + bh)
            logits = h @ Why + by
            pred = sigmoid(logits)
            dlogits = pred - y
            Why -= lr * np.outer(h, dlogits)
            by -= lr * dlogits

    h = np.zeros(hidden)
    for x in M[-window:]:
        h = np.tanh(x @ Wxh + h @ Whh + bh)
    return sigmoid(h @ Why + by)


def graph_scores(M):
    import networkx as nx
    p = M.mean(axis=0)
    co = (M.T @ M).astype(float) / len(M)
    lift = np.zeros_like(co)
    for i in range(N_MAX):
        for j in range(N_MAX):
            if i != j and p[i] > 0 and p[j] > 0:
                lift[i, j] = co[i, j] / (p[i] * p[j])
    G = nx.from_numpy_array(lift)
    pr = nx.pagerank(G, weight="weight")
    ec = nx.eigenvector_centrality_numpy(G, weight="weight")
    pr_arr = np.array([pr[i] for i in range(N_MAX)])
    ec_arr = np.array([ec[i] for i in range(N_MAX)])
    return safe_norm(pr_arr) + safe_norm(ec_arr)


# ==================== TEMPORAL ====================
def day_filtered_freq(draws, day_target, window=None):
    M_day = np.array([
        [1 if (n + 1) in d["nums"] else 0 for n in range(N_MAX)]
        for d in draws if day_of_week(d["sorteo"]) == day_target
    ])
    if window and len(M_day) > window:
        M_day = M_day[-window:]
    return M_day.sum(axis=0) if len(M_day) else np.zeros(N_MAX)


# ==================== GENÉTICO ====================
def genetic(M, freq, recent_freq, p_markov, weights, seed=42, pop=120, gens=100):
    rng = random.Random(seed)
    co = (M.T @ M).astype(float) / len(M)
    p_global = M.mean(axis=0)

    def fitness(combo):
        s = sum(combo); n_par = sum(1 for x in combo if x % 2 == 0)
        n_baj = sum(1 for x in combo if x <= 12)
        n_con = sum(1 for i in range(len(combo) - 1) if combo[i + 1] - combo[i] == 1)
        # rangos válidos: suma 150-212, par 5-9, bajos 5-9, consec 5-9
        f_suma = 1.0 if 150 <= s <= 212 else 0.4
        f_pi = 1.0 if 5 <= n_par <= 9 else 0.4
        f_ba = 1.0 if 5 <= n_baj <= 9 else 0.4
        f_co = 1.0 if 5 <= n_con <= 9 else 0.6
        f_fr = sum(freq[c - 1] for c in combo) / (sum(sorted(freq)[-N_DRAW:]) + 1e-9)
        f_re = sum(recent_freq[c - 1] for c in combo) / (sum(sorted(recent_freq)[-N_DRAW:]) + 1e-9)
        f_mk = sum(p_markov[c - 1] for c in combo) / (sum(sorted(p_markov)[-N_DRAW:]) + 1e-9)
        f_lf = sum(co[a - 1, b - 1] for i, a in enumerate(combo) for b in combo[i + 1:]) / (N_DRAW * (N_DRAW - 1) / 2)
        w = weights
        return (w["suma"] * f_suma + w["pi"] * f_pi + w["ba"] * f_ba + w["co"] * f_co
                + w["freq"] * f_fr + w["rec"] * f_re + w["mk"] * f_mk + w["lift"] * f_lf)

    def random_combo():
        return sorted(rng.sample(range(1, N_MAX + 1), N_DRAW))

    def mutate(c):
        c = list(c); out = rng.choice(c)
        rem = [n for n in range(1, N_MAX + 1) if n not in c]
        c.remove(out); c.append(rng.choice(rem))
        return sorted(c)

    def cross(a, b):
        common = list(set(a) & set(b))
        rest = list(set(a) | set(b) - set(common))
        rng.shuffle(rest)
        need = N_DRAW - len(common)
        return sorted(common + rest[:need])

    population = [random_combo() for _ in range(pop)]
    for _ in range(gens):
        scored = sorted(population, key=fitness, reverse=True)
        elite = scored[:pop // 4]
        children = []
        while len(children) < pop - len(elite):
            a, b = rng.sample(elite, 2)
            child = cross(a, b)
            if rng.random() < 0.3:
                child = mutate(child)
            children.append(child)
        population = elite + children
    return sorted(population, key=fitness, reverse=True)[0]


# ==================== ESTRUCTURA ====================
def validate(combo):
    s = sum(combo); n_par = sum(1 for x in combo if x % 2 == 0)
    n_baj = sum(1 for x in combo if x <= 12)
    n_con = sum(1 for i in range(len(combo) - 1) if combo[i + 1] - combo[i] == 1)
    return {
        "suma": s, "pares": n_par, "impares": N_DRAW - n_par,
        "bajos": n_baj, "altos": N_DRAW - n_baj, "consec": n_con,
        "valid": 150 <= s <= 212 and 5 <= n_par <= 9 and 5 <= n_baj <= 9 and 5 <= n_con <= 9,
    }


# ==================== EXCEL MATRICIAL ====================
CENTER = Alignment(horizontal="center", vertical="center")
SIDE = Side(style="thin", color="888888")
BORDER = Border(left=SIDE, right=SIDE, top=SIDE, bottom=SIDE)
BLACK = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
SEPARATOR_COLS = [3, 9, 15, 21, 27]  # col B = 2, luego separadores ANTES de cada bloque

# Layout: A=método, B=separador opcional, C..G=1..5, H=sep, I..M=6..10, N=sep,
# O..S=11..15, T=sep, U..Y=16..20, Z=sep, AA..AE=21..25, AF=total
def col_for_num(n):
    """Devuelve la columna 1-based para el número n con layout del brief."""
    group = (n - 1) // 5; pos = (n - 1) % 5
    return 3 + group * 6 + pos  # 3..7, 9..13, 15..19, 21..25, 27..31


SEP = [8, 14, 20, 26]
LAST = 31


def style_num(cell, n):
    bg, fg = PALETTE[n]
    cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    cell.font = Font(bold=True, color=fg, name="Arial")
    cell.alignment = CENTER; cell.border = BORDER


def paint_sep(ws, row):
    for c in SEP:
        ws.cell(row=row, column=c).fill = BLACK


def header_row(ws, row, label_a="Estrategia"):
    ws.cell(row=row, column=1, value=label_a).font = Font(bold=True, color="FFFFFF", name="Arial")
    ws.cell(row=row, column=1).fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
    ws.cell(row=row, column=1).alignment = CENTER
    for n in range(1, 26):
        style_num(ws.cell(row=row, column=col_for_num(n), value=n), n)
    paint_sep(ws, row)
    ws.cell(row=row, column=LAST + 1, value="Total").font = Font(bold=True)


def write_combo(ws, row, label, nums, row_fill=None):
    cell = ws.cell(row=row, column=1, value=label)
    cell.font = Font(bold=True, name="Arial")
    cell.alignment = Alignment(vertical="center")
    if row_fill:
        cell.fill = PatternFill(start_color=row_fill, end_color=row_fill, fill_type="solid")
    for n in nums:
        style_num(ws.cell(row=row, column=col_for_num(n), value=n), n)
    paint_sep(ws, row)
    ws.cell(row=row, column=LAST + 1, value=len(nums)).alignment = CENTER


def set_widths(ws):
    ws.column_dimensions["A"].width = 32
    for c in range(3, LAST + 1):
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = 4
    for c in SEP:
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = 1.5
    ws.column_dimensions[ws.cell(row=1, column=LAST + 1).column_letter].width = 6


# ==================== MAIN ====================
def main():
    print(">> Cargando datos...")
    draws_all = load_draws()
    draws = [d for d in draws_all if d["sorteo"] >= STABLE_START]
    M = to_matrix(draws)
    print(f"   {len(draws_all)} sorteos totales, {len(draws)} en período estable (>= {STABLE_START})")

    last_sorteo = draws[-1]["sorteo"]
    day_target = day_of_week(TARGET_SORTEO)
    print(f"   Último conocido: {last_sorteo}. Predicción para {TARGET_SORTEO} ({day_target})")

    print(">> Frecuencias por ventana...")
    f_all = freq_window(M)
    f_1000 = freq_window(M, 1000); f_500 = freq_window(M, 500)
    f_300 = freq_window(M, 300); f_100 = freq_window(M, 100); f_50 = freq_window(M, 50)
    g = gaps(M); due = due_score(M)
    last_nums = draws[-1]["nums"]

    print(">> Markov 1° orden...")
    p_mk = markov_1st(M, last_nums)
    p_bayes = bayesian_score(f_all, f_500, f_300, f_100, p_mk, g)

    print(">> HMM...")
    p_hmm = hmm_scores(M)
    print(">> XGBoost (25 binarios)...")
    p_xgb = xgb_scores(M)
    print(">> MLP red neuronal...")
    p_mlp = mlp_scores(M)
    print(">> RNN custom NumPy...")
    p_rnn = rnn_custom_scores(M)
    print(">> Análisis de grafo (PageRank + Eigenvector)...")
    p_graph = graph_scores(M)

    print(f">> Condicional al día '{day_target}'...")
    f_day = day_filtered_freq(draws, day_target)
    f_day_recent = day_filtered_freq(draws, day_target, window=50)

    print(">> Ensemble super-consenso...")
    ensemble = (
        0.10 * safe_norm(f_all) + 0.10 * safe_norm(f_500) +
        0.08 * safe_norm(f_300) + 0.06 * safe_norm(f_100) +
        0.08 * safe_norm(p_mk) + 0.08 * safe_norm(p_hmm) +
        0.12 * safe_norm(p_xgb) + 0.12 * safe_norm(p_mlp) +
        0.08 * safe_norm(p_graph) + 0.08 * safe_norm(p_rnn) +
        0.05 * safe_norm(f_day) + 0.05 * safe_norm(f_day_recent)
    )
    super_consenso = top14(ensemble)

    print(">> Consenso por votación...")
    methods_top14 = {
        "freq_all": top14(f_all), "freq_1000": top14(f_1000), "freq_500": top14(f_500),
        "freq_300": top14(f_300), "freq_100": top14(f_100), "freq_50": top14(f_50),
        "DUE": top14(due), "Bayesiano": top14(p_bayes), "Markov": top14(p_mk),
        "HMM": top14(p_hmm), "XGBoost": top14(p_xgb), "MLP": top14(p_mlp),
        "RNN": top14(p_rnn), "Grafo": top14(p_graph),
        f"Dia_{day_target}": top14(f_day), f"Dia_{day_target}_50": top14(f_day_recent),
    }
    votes = Counter()
    for nums in methods_top14.values():
        votes.update(nums)
    voting_consenso = sorted([n for n, _ in votes.most_common(N_DRAW)])

    print(">> Algoritmo genético × 3...")
    rec_freq = freq_window(M, 50)
    ga_weights = [
        {"name": "GA-Frecuencias", "suma": 2, "pi": 1, "ba": 1, "co": 1, "freq": 8, "rec": 4, "mk": 6, "lift": 3},
        {"name": "GA-Recientes",   "suma": 2, "pi": 1, "ba": 1, "co": 1, "freq": 3, "rec": 10, "mk": 6, "lift": 3},
        {"name": "GA-Markov",      "suma": 2, "pi": 1, "ba": 1, "co": 1, "freq": 5, "rec": 5, "mk": 12, "lift": 4},
    ]
    ga_results = []
    for w in ga_weights:
        combo = genetic(M, f_all, rec_freq, p_mk, w, seed=w["name"].__hash__() & 0xFFFF)
        ga_results.append((w["name"], combo))

    print(">> 5 Calientes / 5 Fríos...")
    hot5 = top14(ensemble)[:5]
    cold_scores = -ensemble
    cold5 = sorted((np.argsort(cold_scores)[:5] + 1).tolist())[::1][:5]

    print(">> χ² de uniformidad (auditoría)...")
    expected = M.sum() / N_MAX
    chi2, pval = sst.chisquare(f_all, [expected] * N_MAX)
    print(f"   χ² = {chi2:.2f}, p = {pval:.4f}  ({'uniforme' if pval > 0.05 else 'sesgo!'})")

    # ============ EXCEL ============
    print(">> Generando Excel matricial...")
    wb = Workbook()
    ws = wb.active; ws.title = "Predicciones"
    ws.cell(row=1, column=1, value=f"Kino — Sorteo {TARGET_SORTEO} ({day_target})").font = Font(bold=True, size=14, name="Arial")
    ws.cell(row=2, column=1, value=f"χ²={chi2:.2f}, p={pval:.3f} → sorteo uniforme, ningún modelo supera azar real").font = Font(italic=True, color="666666", name="Arial")
    header_row(ws, 4)

    row = 5
    write_combo(ws, row, "★★★ SUPER-CONSENSO ENSEMBLE", super_consenso, row_fill="FFC000"); row += 1
    write_combo(ws, row, "★ CONSENSO POR VOTACIÓN", voting_consenso, row_fill="FFE699"); row += 1
    write_combo(ws, row, f"★ Condicional día {day_target}", top14(f_day), row_fill="E2EFDA"); row += 1
    # Calientes y fríos como filas matriciales
    write_combo(ws, row, "🔥 5 CALIENTES (top ensemble)", hot5, row_fill="C6EFCE"); row += 1
    write_combo(ws, row, "❄️ 5 FRÍOS (bottom ensemble)", cold5, row_fill="FFC7CE"); row += 1
    row += 1
    write_combo(ws, row, "Frec. HOT all-time", top14(f_all)); row += 1
    write_combo(ws, row, "Frec. HOT últ. 1000", top14(f_1000)); row += 1
    write_combo(ws, row, "Frec. HOT últ. 500", top14(f_500)); row += 1
    write_combo(ws, row, "Frec. HOT últ. 300", top14(f_300)); row += 1
    write_combo(ws, row, "Frec. HOT últ. 100", top14(f_100)); row += 1
    write_combo(ws, row, "Frec. HOT últ. 50", top14(f_50)); row += 1
    write_combo(ws, row, "DUE (atrasados)", top14(due)); row += 1
    write_combo(ws, row, "Score Bayesiano", top14(p_bayes)); row += 1
    write_combo(ws, row, "Markov 1° orden", top14(p_mk)); row += 1
    row += 1
    write_combo(ws, row, "HMM (5 estados)", top14(p_hmm), row_fill="BDD7EE"); row += 1
    write_combo(ws, row, "XGBoost (25 binarios)", top14(p_xgb), row_fill="BDD7EE"); row += 1
    write_combo(ws, row, "MLP Red Neuronal", top14(p_mlp), row_fill="BDD7EE"); row += 1
    write_combo(ws, row, "RNN custom NumPy", top14(p_rnn), row_fill="BDD7EE"); row += 1
    write_combo(ws, row, "Grafo (PageRank+EigenC)", top14(p_graph), row_fill="BDD7EE"); row += 1
    row += 1
    for name, combo in ga_results:
        write_combo(ws, row, name, combo, row_fill="C6E0B4"); row += 1
    set_widths(ws)

    # Hoja 2: Estructura/validación
    ws2 = wb.create_sheet("Estructura")
    ws2["A1"] = "Validación estructural de las combinaciones"
    ws2["A1"].font = Font(bold=True, size=12)
    headers = ["Combinación", "Suma", "Pares", "Impares", "Bajos(1-12)", "Altos(13-25)", "Consec", "¿Válida?"]
    for c, h in enumerate(headers, start=1):
        cell = ws2.cell(row=3, column=c, value=h); cell.font = Font(bold=True); cell.alignment = CENTER
    target_combos = [
        ("Super-Consenso", super_consenso), ("Votación", voting_consenso),
        ("Cond. " + day_target, top14(f_day)),
    ] + [(n, c) for n, c in ga_results]
    for i, (name, combo) in enumerate(target_combos, start=4):
        v = validate(combo)
        ws2.cell(row=i, column=1, value=name)
        for c, k in enumerate(["suma", "pares", "impares", "bajos", "altos", "consec"], start=2):
            ws2.cell(row=i, column=c, value=v[k]).alignment = CENTER
        cell = ws2.cell(row=i, column=8, value="✓ OK" if v["valid"] else "⚠ atípica")
        cell.fill = PatternFill(start_color="C6EFCE" if v["valid"] else "FFC7CE", end_color="C6EFCE" if v["valid"] else "FFC7CE", fill_type="solid")
    for col, w in zip("ABCDEFGH", (24, 8, 8, 10, 12, 12, 10, 12)):
        ws2.column_dimensions[col].width = w

    # Hoja 3: Calientes/Fríos detalle
    ws3 = wb.create_sheet("5C 5F detalle")
    ws3["A1"] = "Top 5 Calientes / Top 5 Fríos por ensemble"
    ws3["A1"].font = Font(bold=True, size=12)
    for c, h in enumerate(["Puesto", "N°", "Score ensemble", "Frec. histórica %", "Atraso"], start=1):
        cell = ws3.cell(row=3, column=c, value=h); cell.font = Font(bold=True); cell.alignment = CENTER
    ranked_idx = np.argsort(-ensemble)
    rr = 4
    ws3.cell(row=rr, column=1, value="🔥 CALIENTES").font = Font(bold=True); rr += 1
    for i, idx in enumerate(ranked_idx[:5], start=1):
        n = int(idx + 1)
        ws3.cell(row=rr, column=1, value=i).alignment = CENTER
        style_num(ws3.cell(row=rr, column=2, value=n), n)
        ws3.cell(row=rr, column=3, value=round(float(ensemble[idx]), 4)).alignment = CENTER
        ws3.cell(row=rr, column=4, value=round(float(M.mean(axis=0)[idx]) * 100, 2)).alignment = CENTER
        ws3.cell(row=rr, column=5, value=int(g[idx])).alignment = CENTER
        rr += 1
    rr += 1
    ws3.cell(row=rr, column=1, value="❄️ FRÍOS").font = Font(bold=True); rr += 1
    for i, idx in enumerate(ranked_idx[-5:][::-1], start=1):
        n = int(idx + 1)
        ws3.cell(row=rr, column=1, value=i).alignment = CENTER
        style_num(ws3.cell(row=rr, column=2, value=n), n)
        ws3.cell(row=rr, column=3, value=round(float(ensemble[idx]), 4)).alignment = CENTER
        ws3.cell(row=rr, column=4, value=round(float(M.mean(axis=0)[idx]) * 100, 2)).alignment = CENTER
        ws3.cell(row=rr, column=5, value=int(g[idx])).alignment = CENTER
        rr += 1
    for col, w in zip("ABCDE", (12, 8, 18, 18, 10)):
        ws3.column_dimensions[col].width = w

    # Hoja 4: Últimos 60 sorteos matricial
    ws4 = wb.create_sheet("Últimos 60")
    header_row(ws4, 1, label_a="Sorteo")
    for i, d in enumerate(draws[-60:], start=2):
        ws4.cell(row=i, column=1, value=d["sorteo"]).alignment = CENTER
        for n in d["nums"]:
            style_num(ws4.cell(row=i, column=col_for_num(n), value=n), n)
        paint_sep(ws4, i)
    set_widths(ws4); ws4.column_dimensions["A"].width = 8

    wb.save(OUT)
    print(f">> OK -> {OUT}")
    print(f"   Super-Consenso: {super_consenso}")
    print(f"   Votación: {voting_consenso}")


if __name__ == "__main__":
    main()
