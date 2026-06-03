"""
Analizador AVANZADO de Kino (Chile).

Lee el archivo oficial de estadisticas ("estadisticaskino.xlsx", hoja "Kino")
y produce:
  - Excel de analisis (frecuencias, sorteos ordenados con colores, pares, sugerencias)
  - Graficos PNG (frecuencia por numero, atraso actual, frecuencia por decada)
  - Test de aleatoriedad chi-cuadrado (demuestra si el sorteo es justo)

Uso:
    python kino_avanzado.py estadisticaskino.xlsx salida/
        (crea salida/kino_analisis.xlsx y salida/*.png)

Requisitos:
    pip install openpyxl pandas matplotlib scipy

NOTA HONESTA: el Kino es azar puro. Esto es analisis estadistico descriptivo
del pasado; NO predice resultados ni mejora la probabilidad de ganar.
"""
import argparse
import os
import random
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import chisquare
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

PALETTE = {
    1:  ("B8D8E8", "000000"), 2:  ("E63946", "000000"), 3:  ("A8E6A3", "000000"),
    4:  ("F2C879", "000000"), 5:  ("7B3FA0", "FFFFFF"), 6:  ("1ABC9C", "000000"),
    7:  ("FF8FCF", "000000"), 8:  ("2980B9", "FFFFFF"), 9:  ("7F8C8D", "000000"),
    10: ("A98E33", "FFFFFF"), 11: ("F1C40F", "000000"), 12: ("C8A2D8", "000000"),
    13: ("1ABEDB", "000000"), 14: ("5DADE2", "000000"), 15: ("F39C12", "000000"),
    16: ("1A1A1A", "FFFFFF"), 17: ("EC407A", "FFFFFF"), 18: ("C5E1A5", "000000"),
    19: ("8B7500", "FFFFFF"), 20: ("C0392B", "FFFFFF"), 21: ("00BCD4", "000000"),
    22: ("BDBDBD", "000000"), 23: ("4DD0E1", "000000"), 24: ("D7B98E", "FFFFFF"),
    25: ("F8BBD0", "000000"),
}
HEX = {n: "#" + PALETTE[n][0] for n in PALETTE}

CENTER = Alignment(horizontal="center", vertical="center")
_side = Side(style="thin", color="BBBBBB")
BORDER = Border(left=_side, right=_side, top=_side, bottom=_side)


def style_num(cell, n):
    bg, fg = PALETTE[n]
    cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    cell.font = Font(bold=True, color=fg)
    cell.alignment = CENTER
    cell.border = BORDER


def parse_int(v):
    if v is None or v == "":
        return None
    try:
        n = int(str(v).strip())
        return n if 1 <= n <= 25 else None
    except (ValueError, TypeError):
        return None


def parse_year(fecha):
    """Extrae el anio de una fecha tipo '19-09-1990' o datetime."""
    if fecha is None:
        return None
    s = str(fecha)
    for part in s.replace("/", "-").split("-"):
        part = part.strip()
        if len(part) == 4 and part.isdigit():
            return int(part)
    # datetime
    try:
        return fecha.year
    except AttributeError:
        return None


def read_draws(path, sheet):
    wb = load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else (wb["Kino"] if "Kino" in wb.sheetnames else wb.active)
    draws = []
    for row in ws.iter_rows(values_only=True):
        if not row or len(row) < 3 or not isinstance(row[0], (int, float)):
            continue
        nums = [parse_int(v) for v in row[2:18]]
        nums = [n for n in nums if n]
        if nums:
            draws.append({"sorteo": int(row[0]), "fecha": row[1],
                          "anio": parse_year(row[1]), "nums": nums})
    return draws


def build_stats(draws):
    freq = Counter()
    for d in draws:
        for n in d["nums"]:
            freq[n] += 1
    total = len(draws)
    gap = {}
    for n in range(1, 26):
        g = 0
        for d in reversed(draws):
            if n in d["nums"]:
                break
            g += 1
        gap[n] = g
    return freq, total, gap


def pair_counts(draws, top=20):
    pairs = Counter()
    for d in draws:
        s = sorted(d["nums"])
        for i in range(len(s)):
            for j in range(i + 1, len(s)):
                pairs[(s[i], s[j])] += 1
    return pairs.most_common(top)


def chi_test(freq, total, n_per_draw_avg):
    """Chi-cuadrado: ¿las frecuencias se desvian de lo esperado por azar?"""
    observed = [freq[n] for n in range(1, 26)]
    expected_each = sum(observed) / 25
    expected = [expected_each] * 25
    chi, p = chisquare(observed, expected)
    return chi, p, expected_each


# ---------- Graficos ----------
def chart_frequency(freq, total, path):
    nums = list(range(1, 26))
    vals = [freq[n] for n in nums]
    plt.figure(figsize=(11, 5))
    plt.bar([str(n) for n in nums], vals, color=[HEX[n] for n in nums], edgecolor="#444")
    plt.axhline(sum(vals) / 25, color="red", linestyle="--", linewidth=1,
                label="Promedio (lo esperado por azar)")
    plt.title(f"Frecuencia de cada número — {total} sorteos")
    plt.xlabel("Número"); plt.ylabel("Veces que salió")
    plt.legend(); plt.tight_layout()
    plt.savefig(path, dpi=120); plt.close()


def chart_gap(gap, path):
    nums = sorted(range(1, 26), key=lambda n: -gap[n])
    vals = [gap[n] for n in nums]
    plt.figure(figsize=(11, 5))
    plt.bar([str(n) for n in nums], vals, color=[HEX[n] for n in nums], edgecolor="#444")
    plt.title("Atraso actual: sorteos seguidos SIN salir (de mayor a menor)")
    plt.xlabel("Número"); plt.ylabel("Sorteos sin aparecer")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()


def chart_decade(draws, path):
    rows = []
    for d in draws:
        if d["anio"]:
            decade = (d["anio"] // 10) * 10
            for n in d["nums"]:
                rows.append({"decada": f"{decade}s", "num": n})
    if not rows:
        return False
    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index="num", columns="decada", aggfunc="size", fill_value=0)
    # Normalizar por sorteos de cada decada para comparar % de aparicion
    pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100
    pivot_pct.plot(kind="bar", figsize=(13, 6), width=0.8)
    plt.title("Aparición relativa por número en cada década (%)")
    plt.xlabel("Número"); plt.ylabel("% del total de esa década")
    plt.tight_layout(); plt.savefig(path, dpi=120); plt.close()
    return True


# ---------- Hojas Excel ----------
def sheet_frecuencias(ws, freq, total, gap, chi, p, expected_each):
    ws.title = "Frecuencias"
    ws["A1"] = f"Frecuencias de Kino — {total} sorteos"
    ws["A1"].font = Font(bold=True, size=12)
    ws["A2"] = (f"Test chi-cuadrado: χ²={chi:.2f}, p={p:.3f}  →  "
                + ("sorteo COMPATIBLE con azar justo (no hay números privilegiados)"
                   if p > 0.05 else "se detecta desviación (revisar datos)"))
    ws["A2"].font = Font(italic=True)
    for c, h in enumerate(["Número", "Veces", "% aparición", "Sorteos sin salir"], start=1):
        cell = ws.cell(row=4, column=c, value=h); cell.font = Font(bold=True)
        cell.alignment = CENTER; cell.border = BORDER
    for i, n in enumerate(sorted(range(1, 26), key=lambda n: -freq[n]), start=5):
        style_num(ws.cell(row=i, column=1, value=n), n)
        ws.cell(row=i, column=2, value=freq[n]).alignment = CENTER
        ws.cell(row=i, column=3, value=round(freq[n] / total * 100, 2)).alignment = CENTER
        ws.cell(row=i, column=4, value=gap[n]).alignment = CENTER
    for col, w in zip("ABCD", (10, 12, 14, 18)):
        ws.column_dimensions[col].width = w


def sheet_sorteos(wb, draws):
    ws = wb.create_sheet("Sorteos ordenados")
    ws.cell(row=1, column=1, value="Sorteo").font = Font(bold=True)
    ws.cell(row=1, column=2, value="Fecha").font = Font(bold=True)
    for n in range(1, 26):
        style_num(ws.cell(row=1, column=2 + n, value=n), n)
    for i, d in enumerate(draws, start=2):
        ws.cell(row=i, column=1, value=d["sorteo"]).alignment = CENTER
        ws.cell(row=i, column=2, value=str(d["fecha"])).alignment = CENTER
        for n in d["nums"]:
            style_num(ws.cell(row=i, column=2 + n, value=n), n)
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 12
    for col_idx in range(3, 28):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 4
    ws.freeze_panes = "C2"


def sheet_pares(wb, pairs):
    ws = wb.create_sheet("Pares frecuentes")
    ws["A1"] = "Pares de números que más salieron juntos"
    ws["A1"].font = Font(bold=True, size=12)
    for c, h in enumerate(["#", "Núm A", "Núm B", "Veces juntos"], start=1):
        cell = ws.cell(row=3, column=c, value=h); cell.font = Font(bold=True)
        cell.alignment = CENTER; cell.border = BORDER
    for i, ((a, b), cnt) in enumerate(pairs, start=4):
        ws.cell(row=i, column=1, value=i - 3).alignment = CENTER
        style_num(ws.cell(row=i, column=2, value=a), a)
        style_num(ws.cell(row=i, column=3, value=b), b)
        ws.cell(row=i, column=4, value=cnt).alignment = CENTER
    for col, w in zip("ABCD", (6, 8, 8, 14)):
        ws.column_dimensions[col].width = w


def sheet_sugerencias(wb, freq, gap, next_sorteo):
    ws = wb.create_sheet("Sugerencias")
    ws["A1"] = f"Combinaciones de referencia para sorteo {next_sorteo} — NO predicen nada"
    ws["A1"].font = Font(bold=True, color="C0392B")
    ranked = sorted(range(1, 26), key=lambda n: -freq[n])
    atrasados = sorted(range(1, 26), key=lambda n: -gap[n])
    random.seed(next_sorteo)
    combos = [
        ("Calientes", sorted(ranked[:14])),
        ("Frías", sorted(ranked[-14:])),
        ("Atrasados", sorted(atrasados[:14])),
        ("Mixta", sorted(set(ranked[:7] + atrasados[:7]))),
        ("Azar puro", sorted(random.sample(range(1, 26), 14))),
    ]
    row = 3
    for label, nums in combos:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        for j, n in enumerate(nums, start=2):
            style_num(ws.cell(row=row, column=j, value=n), n)
        row += 1
    ws.column_dimensions["A"].width = 14
    for col_idx in range(2, 17):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 4


def main():
    ap = argparse.ArgumentParser(description="Analizador avanzado de Kino.")
    ap.add_argument("origen", help="Archivo oficial de estadisticas (.xlsx)")
    ap.add_argument("salida", help="Carpeta de salida")
    ap.add_argument("--hoja", default=None, help="Hoja a leer (default 'Kino')")
    args = ap.parse_args()

    try:
        draws = read_draws(args.origen, args.hoja)
    except FileNotFoundError:
        print(f"No encontré el archivo: {args.origen}", file=sys.stderr)
        sys.exit(1)
    if not draws:
        print("No encontré sorteos. Revisa la hoja con --hoja.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.salida, exist_ok=True)
    freq, total, gap = build_stats(draws)
    pairs = pair_counts(draws)
    avg_per = sum(freq.values()) / total
    chi, p, expected_each = chi_test(freq, total, avg_per)
    next_sorteo = draws[-1]["sorteo"] + 1

    # Graficos
    chart_frequency(freq, total, os.path.join(args.salida, "frecuencia.png"))
    chart_gap(gap, os.path.join(args.salida, "atraso.png"))
    has_dec = chart_decade(draws, os.path.join(args.salida, "por_decada.png"))

    # Excel
    wb = Workbook()
    sheet_frecuencias(wb.active, freq, total, gap, chi, p, expected_each)
    sheet_sorteos(wb, draws)
    sheet_pares(wb, pairs)
    sheet_sugerencias(wb, freq, gap, next_sorteo)
    xlsx = os.path.join(args.salida, "kino_analisis.xlsx")
    wb.save(xlsx)

    print(f"Sorteos analizados: {total} (del {draws[0]['sorteo']} al {draws[-1]['sorteo']})")
    print(f"Test chi-cuadrado: chi2={chi:.2f}, p={p:.3f}",
          "-> compatible con azar justo" if p > 0.05 else "-> hay desviacion")
    print(f"Calientes: {sorted(range(1,26), key=lambda n:-freq[n])[:7]}")
    print(f"Par más frecuente: {pairs[0][0]} ({pairs[0][1]} veces)")
    print(f"Generado: {xlsx}")
    print(f"Gráficos: frecuencia.png, atraso.png" + (", por_decada.png" if has_dec else ""))


if __name__ == "__main__":
    main()
