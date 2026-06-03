"""
App web interactiva de análisis de Kino (Chile).

Incluye:
  - Frecuencias de cada número (con filtro por año)
  - Patrones por sorteo (suma, pares/impares, altos/bajos, consecutivos)
  - Probabilidades reales de ganar (calculadora honesta)
  - Buscador de combinaciones (en qué sorteos salió X)
  - Generador de combinaciones de referencia

Uso:
    pip install flask
    python kino_app.py
    -> abre http://127.0.0.1:8000 en el navegador

Los datos se leen de analisis_kino/kino_data.json (generado del archivo oficial).

NOTA HONESTA: el Kino es azar puro. Esto es análisis descriptivo del pasado;
NO predice resultados ni mejora la probabilidad de ganar.
"""
import json
import math
import os
import random
from collections import Counter

from flask import Flask, request, render_template_string

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE, "analisis_kino", "kino_data.json")

PALETTE = {
    1: "B8D8E8", 2: "E63946", 3: "A8E6A3", 4: "F2C879", 5: "7B3FA0",
    6: "1ABC9C", 7: "FF8FCF", 8: "2980B9", 9: "7F8C8D", 10: "A98E33",
    11: "F1C40F", 12: "C8A2D8", 13: "1ABEDB", 14: "5DADE2", 15: "F39C12",
    16: "1A1A1A", 17: "EC407A", 18: "C5E1A5", 19: "8B7500", 20: "C0392B",
    21: "00BCD4", 22: "BDBDBD", 23: "4DD0E1", 24: "D7B98E", 25: "F8BBD0",
}
DARK_FG = {5, 8, 10, 16, 17, 19, 20, 24}

with open(DATA_PATH, encoding="utf-8") as f:
    DRAWS = json.load(f)

YEARS = sorted({d["anio"] for d in DRAWS if d["anio"]})

app = Flask(__name__)


def filtered(year=None):
    if year:
        return [d for d in DRAWS if d["anio"] == year]
    return DRAWS


def frequencies(draws):
    freq = Counter()
    for d in draws:
        for n in d["nums"]:
            freq[n] += 1
    return freq


def gaps():
    g = {}
    for n in range(1, 26):
        c = 0
        for d in reversed(DRAWS):
            if n in d["nums"]:
                break
            c += 1
        g[n] = c
    return g


def patterns(draws):
    sums, odds, lows, consec = [], [], [], []
    for d in draws:
        nums = d["nums"]
        sums.append(sum(nums))
        odds.append(sum(1 for n in nums if n % 2 == 1))
        lows.append(sum(1 for n in nums if n <= 13))
        c = sum(1 for i in range(len(nums) - 1) if nums[i + 1] - nums[i] == 1)
        consec.append(c)
    n = len(draws) or 1
    return {
        "sum_avg": round(sum(sums) / n, 1),
        "sum_min": min(sums) if sums else 0,
        "sum_max": max(sums) if sums else 0,
        "odd_avg": round(sum(odds) / n, 1),
        "low_avg": round(sum(lows) / n, 1),
        "consec_avg": round(sum(consec) / n, 2),
        "sum_dist": Counter((s // 20) * 20 for s in sums),
    }


def win_probabilities():
    """Hipergeométrica: 14 sorteados de 25, jugador marca 14.
    P(acertar k) = C(14,k)*C(11,14-k)/C(25,14)."""
    total = math.comb(25, 14)
    rows = []
    for k in range(8, 15):
        ways = math.comb(14, k) * math.comb(11, 14 - k)
        p = ways / total
        rows.append({"k": k, "p": p,
                     "one_in": round(1 / p) if p > 0 else None})
    return total, rows


def search_combo(nums):
    nums = set(nums)
    exact, partial = [], []
    for d in DRAWS:
        inter = nums & set(d["nums"])
        if len(inter) == len(nums) and nums:
            exact.append(d)
        if len(inter) >= max(1, len(nums) - 2):
            partial.append((d, len(inter)))
    partial.sort(key=lambda x: -x[1])
    return exact, partial[:30]


PAGE = """
<!doctype html><html lang=es><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Análisis Kino</title>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f4f6f8;color:#222}
 header{background:#1A1A1A;color:#fff;padding:14px 20px}
 header h1{margin:0;font-size:20px}
 nav{background:#2980B9;padding:0 10px}
 nav a{display:inline-block;color:#fff;padding:12px 16px;text-decoration:none;font-size:14px}
 nav a:hover,nav a.active{background:#1f6391}
 .wrap{max-width:1000px;margin:20px auto;padding:0 16px}
 .card{background:#fff;border-radius:10px;padding:18px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
 .ball{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
   border-radius:50%;font-weight:700;margin:2px;font-size:13px;border:1px solid #0002}
 .bar{height:18px;border-radius:4px;display:inline-block;vertical-align:middle}
 table{border-collapse:collapse;width:100%;font-size:14px}
 th,td{padding:6px 8px;border-bottom:1px solid #eee;text-align:left}
 th{background:#fafafa}
 .warn{background:#fff3cd;border:1px solid #ffe69c;padding:12px;border-radius:8px;font-size:14px}
 input,select,button{padding:8px;border-radius:6px;border:1px solid #ccc;font-size:14px}
 button{background:#2980B9;color:#fff;border:0;cursor:pointer}
 .muted{color:#777;font-size:13px}
</style></head><body>
<header><h1>🎰 Análisis Kino — {{total}} sorteos ({{ydesde}}–{{yhasta}})</h1></header>
<nav>
 <a href="/" class="{{'active' if page=='freq' else ''}}">Frecuencias</a>
 <a href="/patrones" class="{{'active' if page=='pat' else ''}}">Patrones</a>
 <a href="/probabilidades" class="{{'active' if page=='prob' else ''}}">Probabilidades</a>
 <a href="/buscador" class="{{'active' if page=='search' else ''}}">Buscador</a>
 <a href="/generador" class="{{'active' if page=='gen' else ''}}">Generador</a>
</nav>
<div class=wrap>
<div class=warn>⚠️ El Kino es azar puro. Esto es análisis del pasado: <b>no predice resultados ni mejora tu probabilidad de ganar.</b> Juega con responsabilidad.</div>
{{ body|safe }}
</div></body></html>
"""


def ball(n):
    bg = PALETTE[n]
    fg = "fff" if n in DARK_FG else "000"
    return f'<span class="ball" style="background:#{bg};color:#{fg}">{n}</span>'


def render(page, body):
    return render_template_string(
        PAGE, page=page, body=body, total=len(DRAWS),
        ydesde=YEARS[0], yhasta=YEARS[-1])


@app.route("/")
def freq_page():
    year = request.args.get("year", type=int)
    draws = filtered(year)
    freq = frequencies(draws)
    g = gaps()
    maxv = max(freq.values()) if freq else 1
    ranked = sorted(range(1, 26), key=lambda n: -freq[n])
    opts = '<option value="">Todos los años</option>' + "".join(
        f'<option value="{y}" {"selected" if y==year else ""}>{y}</option>' for y in YEARS)
    rows = ""
    for n in ranked:
        w = int(freq[n] / maxv * 300)
        rows += (f"<tr><td>{ball(n)}</td><td>{freq[n]}</td>"
                 f"<td>{round(freq[n]/len(draws)*100,1) if draws else 0}%</td>"
                 f'<td><span class="bar" style="width:{w}px;background:#{PALETTE[n]}"></span></td>'
                 f"<td>{g[n]}</td></tr>")
    body = f"""
    <div class=card>
     <form method=get>Filtrar por año: <select name=year onchange="this.form.submit()">{opts}</select></form>
     <p class=muted>{len(draws)} sorteos en la selección. "Atraso" = sorteos seguidos sin salir (global).</p>
     <table><tr><th>N°</th><th>Veces</th><th>%</th><th>Frecuencia</th><th>Atraso</th></tr>{rows}</table>
    </div>"""
    return render("freq", body)


@app.route("/patrones")
def pat_page():
    p = patterns(DRAWS)
    dist = sorted(p["sum_dist"].items())
    maxd = max(p["sum_dist"].values()) if p["sum_dist"] else 1
    drows = "".join(
        f'<tr><td>{lo}-{lo+19}</td><td>{c}</td>'
        f'<td><span class="bar" style="width:{int(c/maxd*300)}px;background:#2980B9"></span></td></tr>'
        for lo, c in dist)
    body = f"""
    <div class=card><h3>Patrones promedio por sorteo</h3>
     <table>
      <tr><th>Métrica</th><th>Valor</th></tr>
      <tr><td>Suma de los 14 números (promedio)</td><td>{p['sum_avg']}</td></tr>
      <tr><td>Suma mínima / máxima histórica</td><td>{p['sum_min']} / {p['sum_max']}</td></tr>
      <tr><td>Cantidad de impares (promedio)</td><td>{p['odd_avg']} de 14</td></tr>
      <tr><td>Números bajos 1–13 (promedio)</td><td>{p['low_avg']} de 14</td></tr>
      <tr><td>Pares consecutivos (promedio)</td><td>{p['consec_avg']}</td></tr>
     </table>
     <p class=muted>Útil para saber si una combinación "se parece" a las típicas, no para predecir.</p>
    </div>
    <div class=card><h3>Distribución de la suma total</h3>
     <table><tr><th>Rango de suma</th><th>Sorteos</th><th></th></tr>{drows}</table>
    </div>"""
    return render("pat", body)


@app.route("/probabilidades")
def prob_page():
    total, rows = win_probabilities()
    trows = "".join(
        f"<tr><td>Acertar {r['k']} de 14</td><td>1 en {r['one_in']:,}</td>"
        f"<td>{r['p']*100:.6f}%</td></tr>" for r in reversed(rows))
    body = f"""
    <div class=card><h3>Tu probabilidad real de ganar</h3>
     <p>El Kino sortea 14 números de 25 y tú marcas 14. Combinaciones posibles: <b>{total:,}</b>.</p>
     <table><tr><th>Resultado</th><th>Probabilidad</th><th>%</th></tr>{trows}</table>
     <p class=warn>Acertar los 14 es <b>1 en {total:,}</b>. Para comparar: tienes muchísima más chance
     de que te caiga un rayo. Ninguna estrategia cambia estos números.</p>
    </div>"""
    return render("prob", body)


@app.route("/buscador")
def search_page():
    raw = request.args.get("nums", "").strip()
    body_extra = ""
    if raw:
        try:
            nums = sorted({int(x) for x in raw.replace(",", " ").split() if 1 <= int(x) <= 25})
        except ValueError:
            nums = []
        if nums:
            exact, partial = search_combo(nums)
            balls = "".join(ball(n) for n in nums)
            prows = "".join(
                f"<tr><td>{d['sorteo']}</td><td>{d['fecha']}</td><td>{k} aciertos</td></tr>"
                for d, k in partial)
            body_extra = f"""
            <div class=card><h3>Resultados para {balls}</h3>
             <p>Sorteos donde salieron <b>todos</b> esos números juntos: <b>{len(exact)}</b></p>
             <p class=muted>Mejores coincidencias (máx 30):</p>
             <table><tr><th>Sorteo</th><th>Fecha</th><th>Coincidencias</th></tr>{prows}</table>
            </div>"""
    body = f"""
    <div class=card>
     <h3>Buscador de combinaciones</h3>
     <form method=get>
      Escribe números separados por espacio o coma (1–25):<br><br>
      <input name=nums value="{raw}" size=40 placeholder="ej: 5 10 12 4 8">
      <button type=submit>Buscar</button>
     </form>
    </div>{body_extra}"""
    return render("search", body)


@app.route("/generador")
def gen_page():
    freq = frequencies(DRAWS)
    g = gaps()
    ranked = sorted(range(1, 26), key=lambda n: -freq[n])
    atras = sorted(range(1, 26), key=lambda n: -g[n])
    next_s = DRAWS[-1]["sorteo"] + 1
    random.seed()
    combos = [
        ("Calientes (más salidos)", sorted(ranked[:14])),
        ("Frías (menos salidos)", sorted(ranked[-14:])),
        ("Atrasados", sorted(atras[:14])),
        ("Azar puro", sorted(random.sample(range(1, 26), 14))),
    ]
    blocks = "".join(
        f"<p><b>{label}:</b><br>{''.join(ball(n) for n in nums)}</p>" for label, nums in combos)
    body = f"""
    <div class=card><h3>Combinaciones de referencia (sorteo {next_s})</h3>
     {blocks}
     <p class=warn>Recuerda: las 4 tienen <b>exactamente la misma probabilidad</b> de ganar.
     Recarga la página para nuevas combinaciones al azar.</p>
    </div>"""
    return render("gen", body)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Abre http://127.0.0.1:{port} en tu navegador")
    app.run(host="127.0.0.1", port=port, debug=False)
