"""
Analizador de Kino (Chile).

Lee el archivo oficial de estadisticas ("estadisticaskino.xlsx", hoja "Kino")
y genera un Excel de analisis con LOS MISMOS COLORES por numero que usa el
usuario, con estas hojas:

  1) "Frecuencias"        -> ranking de cada numero 1..25 (veces, %, atraso)
  2) "Sorteos ordenados"  -> cada sorteo con su numero puesto en su columna 1..25
  3) "Sugerencias"        -> combinaciones generadas (calientes / frias / aleatoria)

Uso:
    python kino_analizar.py estadisticaskino.xlsx kino_analisis.xlsx
    python kino_analizar.py estadisticaskino.xlsx kino_analisis.xlsx --hoja Kino

Requisitos:
    pip install openpyxl

NOTA HONESTA: el Kino es azar puro. Esto es analisis estadistico descriptivo
del pasado, NO predice resultados futuros ni mejora la probabilidad de ganar.
"""
import argparse
import random
import sys
from collections import Counter
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

# Paleta exacta extraida del archivo del usuario (fondo, fuente) por numero.
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


def read_draws(path, sheet):
    """Devuelve lista de (sorteo, fecha, [numeros]). Detecta la fila de inicio."""
    wb = load_workbook(path, data_only=True)
    ws = wb[sheet] if sheet else wb["Kino"] if "Kino" in wb.sheetnames else wb.active
    draws = []
    for row in ws.iter_rows(values_only=True):
        if not row or len(row) < 3:
            continue
        sorteo = row[0]
        fecha = row[1]
        # Solo filas cuyo primer valor es numerico (numero de sorteo) y col 3 numerica
        if not isinstance(sorteo, (int, float)):
            continue
        nums = []
        for v in row[2:18]:
            n = parse_int(v)
            if n:
                nums.append(n)
        if nums:
            draws.append((int(sorteo), fecha, nums))
    return draws


def build_stats(draws):
    freq = Counter()
    for _, _, nums in draws:
        for n in nums:
            freq[n] += 1
    total = len(draws)
    gap = {}
    for n in range(1, 26):
        g = 0
        for _, _, nums in reversed(draws):
            if n in nums:
                break
            g += 1
        gap[n] = g
    return freq, total, gap


def sheet_frecuencias(wb, freq, total, gap):
    ws = wb.active
    ws.title = "Frecuencias"
    ws["A1"] = f"Frecuencias de Kino — {total} sorteos analizados"
    ws["A1"].font = Font(bold=True, size=12)
    headers = ["Número", "Veces salió", "% aparición", "Sorteos sin salir"]
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=c, value=h)
        cell.font = Font(bold=True)
        cell.alignment = CENTER
        cell.border = BORDER
    ranked = sorted(range(1, 26), key=lambda n: -freq[n])
    for i, n in enumerate(ranked, start=4):
        c1 = ws.cell(row=i, column=1, value=n); style_num(c1, n)
        ws.cell(row=i, column=2, value=freq[n]).alignment = CENTER
        ws.cell(row=i, column=3, value=round(freq[n] / total * 100, 2)).alignment = CENTER
        ws.cell(row=i, column=4, value=gap[n]).alignment = CENTER
    for col, w in zip("ABCD", (10, 14, 14, 18)):
        ws.column_dimensions[col].width = w


def sheet_sorteos(wb, draws):
    ws = wb.create_sheet("Sorteos ordenados")
    ws.cell(row=1, column=1, value="Sorteo").font = Font(bold=True)
    ws.cell(row=1, column=2, value="Fecha").font = Font(bold=True)
    for n in range(1, 26):
        c = ws.cell(row=1, column=2 + n, value=n)
        style_num(c, n)
    for i, (sorteo, fecha, nums) in enumerate(draws, start=2):
        ws.cell(row=i, column=1, value=sorteo).alignment = CENTER
        ws.cell(row=i, column=2, value=fecha).alignment = CENTER
        for n in nums:
            style_num(ws.cell(row=i, column=2 + n, value=n), n)
    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 12
    for col_idx in range(3, 28):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 4
    ws.freeze_panes = "C2"


def sheet_sugerencias(wb, freq):
    ws = wb.create_sheet("Sugerencias")
    ws["A1"] = "Combinaciones sugeridas (NO predicen resultados — solo referencia)"
    ws["A1"].font = Font(bold=True, color="C0392B")
    ranked = sorted(range(1, 26), key=lambda n: -freq[n])
    combos = [
        ("14 más calientes", sorted(ranked[:14])),
        ("14 más frías", sorted(ranked[-14:])),
        ("Aleatoria 1", sorted(random.sample(range(1, 26), 14))),
        ("Aleatoria 2", sorted(random.sample(range(1, 26), 14))),
        ("Mezcla calientes+frías", sorted(ranked[:7] + ranked[-7:])),
    ]
    row = 3
    for label, nums in combos:
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        for j, n in enumerate(nums, start=2):
            style_num(ws.cell(row=row, column=j, value=n), n)
        row += 1
    ws.column_dimensions["A"].width = 24
    for col_idx in range(2, 17):
        ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 4


def main():
    ap = argparse.ArgumentParser(description="Analiza el historico de Kino y genera Excel con colores.")
    ap.add_argument("origen", help="Archivo oficial de estadisticas (.xlsx)")
    ap.add_argument("destino", help="Excel de salida con el analisis (.xlsx)")
    ap.add_argument("--hoja", default=None, help="Hoja a leer (default: 'Kino')")
    args = ap.parse_args()

    try:
        draws = read_draws(args.origen, args.hoja)
    except FileNotFoundError:
        print(f"No encontré el archivo: {args.origen}", file=sys.stderr)
        sys.exit(1)

    if not draws:
        print("No encontré sorteos. Revisa la hoja con --hoja.", file=sys.stderr)
        sys.exit(1)

    freq, total, gap = build_stats(draws)
    ranked = sorted(range(1, 26), key=lambda n: -freq[n])

    print(f"Sorteos analizados: {total}")
    print(f"Desde sorteo {draws[0][0]} ({draws[0][1]}) hasta {draws[-1][0]} ({draws[-1][1]})")
    print(f"Calientes (top 7): {ranked[:7]}")
    print(f"Frías (bottom 7) : {ranked[-7:][::-1]}")

    wb = Workbook()
    sheet_frecuencias(wb, freq, total, gap)
    sheet_sorteos(wb, draws)
    sheet_sugerencias(wb, freq)
    wb.save(args.destino)
    print(f"OK -> {args.destino}")


if __name__ == "__main__":
    main()
