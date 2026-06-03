"""
Reordena un Excel de resultados Kino: pasa de "números consecutivos"
(formato imagen 2) a "cada número en su columna del 1 al 25 con color"
(formato imagen 1).

Uso:
    python kino_reorder.py archivo_origen.xlsx archivo_destino.xlsx
    python kino_reorder.py archivo_origen.xlsx archivo_destino.xlsx --hoja "Hoja1" --fila-inicio 5

Requisitos:
    pip install openpyxl
"""
import argparse
import sys
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


# Paleta de 25 colores (uno por número), inspirada en la imagen de referencia.
COLORS = {
    1:  "FFFFFF", 2:  "E74C3C", 3:  "27AE60", 4:  "2C3E50", 5:  "8E44AD",
    6:  "3498DB", 7:  "E91E63", 8:  "F1C40F", 9:  "7F8C8D", 10: "1ABC9C",
    11: "F39C12", 12: "16A085", 13: "00BCD4", 14: "9B59B6", 15: "FFEB3B",
    16: "000000", 17: "E67E22", 18: "795548", 19: "C0392B", 20: "2980B9",
    21: "1ABC9C", 22: "27AE60", 23: "9B59B6", 24: "F39C12", 25: "F1C40F",
}

# Si el color de fondo es muy oscuro, usamos texto blanco.
DARK_NUMBERS = {2, 4, 13, 16, 17, 18, 19, 20, 23}


def fill_for(num: int) -> PatternFill:
    return PatternFill(start_color=COLORS[num], end_color=COLORS[num], fill_type="solid")


def font_for(num: int) -> Font:
    color = "FFFFFF" if num in DARK_NUMBERS else "000000"
    return Font(bold=True, color=color)


def thin_border() -> Border:
    side = Side(style="thin", color="999999")
    return Border(left=side, right=side, top=side, bottom=side)


def parse_int(value):
    """Acepta '01', 1, '1', etc. Devuelve int o None."""
    if value is None or value == "":
        return None
    try:
        n = int(str(value).strip())
        if 1 <= n <= 25:
            return n
    except (ValueError, TypeError):
        pass
    return None


def reorder(src_path: str, dst_path: str, sheet_name: str | None, start_row: int):
    wb_src = load_workbook(src_path, data_only=True)
    ws_src = wb_src[sheet_name] if sheet_name else wb_src.active

    wb_dst = Workbook()
    ws_dst = wb_dst.active
    ws_dst.title = "Kino ordenado"

    # ---- Encabezados ----
    ws_dst.cell(row=1, column=1, value="Pozo estimado").font = Font(bold=True)
    ws_dst.cell(row=1, column=2, value="Fecha").font = Font(bold=True)
    ws_dst.cell(row=1, column=3, value="Sorteo").font = Font(bold=True)
    ws_dst.cell(row=1, column=4, value="Números Sorteados Kino").font = Font(bold=True)
    ws_dst.cell(row=1, column=29, value="Números Sorteados Alargue").font = Font(bold=True)

    # Fila 2: numeración 1..25 para Kino y 1..25 para Alargue
    for n in range(1, 26):
        c = ws_dst.cell(row=2, column=3 + n, value=n)
        c.fill = fill_for(n)
        c.font = font_for(n)
        c.alignment = Alignment(horizontal="center")
        c.border = thin_border()

        c2 = ws_dst.cell(row=2, column=28 + n, value=n)
        c2.fill = fill_for(n)
        c2.font = font_for(n)
        c2.alignment = Alignment(horizontal="center")
        c2.border = thin_border()

    # ---- Filas de datos ----
    # Layout origen esperado (basado en imagen 2):
    #   col D (4) = Pozo, col E (5) = Fecha, col F (6) = Sorteo
    #   col G..U (7..21) = 15 números Kino
    #   col V..AE (22..31) = 10 números Alargue
    out_row = 3
    for row in ws_src.iter_rows(min_row=start_row, values_only=True):
        if not row or len(row) < 7:
            continue

        pozo = row[3] if len(row) > 3 else None
        fecha = row[4] if len(row) > 4 else None
        sorteo = row[5] if len(row) > 5 else None

        if not sorteo and not fecha:
            continue

        kino_nums = [parse_int(row[i]) for i in range(6, min(21, len(row)))]
        alargue_nums = [parse_int(row[i]) for i in range(21, min(31, len(row)))]

        kino_nums = [n for n in kino_nums if n]
        alargue_nums = [n for n in alargue_nums if n]

        # Si la fila no tiene ningún número Kino, la saltamos (sorteo futuro vacío)
        if not kino_nums:
            continue

        ws_dst.cell(row=out_row, column=1, value=pozo)
        ws_dst.cell(row=out_row, column=2, value=fecha)
        ws_dst.cell(row=out_row, column=3, value=sorteo)

        for n in kino_nums:
            c = ws_dst.cell(row=out_row, column=3 + n, value=n)
            c.fill = fill_for(n)
            c.font = font_for(n)
            c.alignment = Alignment(horizontal="center")
            c.border = thin_border()

        for n in alargue_nums:
            c = ws_dst.cell(row=out_row, column=28 + n, value=n)
            c.fill = fill_for(n)
            c.font = font_for(n)
            c.alignment = Alignment(horizontal="center")
            c.border = thin_border()

        out_row += 1

    # Anchos de columna
    ws_dst.column_dimensions["A"].width = 12
    ws_dst.column_dimensions["B"].width = 11
    ws_dst.column_dimensions["C"].width = 8
    for col_idx in range(4, 54):
        ws_dst.column_dimensions[ws_dst.cell(row=1, column=col_idx).column_letter].width = 4

    wb_dst.save(dst_path)
    print(f"OK -> {dst_path} ({out_row - 3} sorteos procesados)")


def main():
    ap = argparse.ArgumentParser(description="Reordena Excel de Kino a formato por número.")
    ap.add_argument("origen", help="Excel de entrada (.xlsx)")
    ap.add_argument("destino", help="Excel de salida (.xlsx)")
    ap.add_argument("--hoja", default=None, help="Nombre de la hoja (por defecto: la activa)")
    ap.add_argument("--fila-inicio", type=int, default=5,
                    help="Fila donde empiezan los datos (default 5)")
    args = ap.parse_args()

    try:
        reorder(args.origen, args.destino, args.hoja, args.fila_inicio)
    except FileNotFoundError:
        print(f"No encontré el archivo: {args.origen}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
