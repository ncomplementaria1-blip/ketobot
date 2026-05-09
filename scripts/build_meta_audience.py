"""Genera un CSV listo para subir como Custom Audience en Meta Ads.

Lee la base de pacientes original y produce un archivo con columnas
email,phone,fn,ln en el formato exacto que Meta espera (lowercase,
sin tildes, teléfono internacional sin separadores).

Uso:
    python scripts/build_meta_audience.py <input.csv> <output.csv>
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata


PHONE_DIGITS_RE = re.compile(r"\D")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_text(value: str) -> str:
    cleaned = (value or "").strip().lower()
    nfkd = unicodedata.normalize("NFKD", cleaned)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_phone(value: str) -> str:
    digits = PHONE_DIGITS_RE.sub("", value or "")
    if not digits:
        return ""
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("56"):
        return digits
    if len(digits) == 9 and digits.startswith("9"):
        return "56" + digits
    if len(digits) == 8:
        return "569" + digits
    return digits


def normalize_email(value: str) -> str:
    email = (value or "").strip().lower()
    return email if EMAIL_RE.match(email) else ""


def build(input_path: str, output_path: str) -> None:
    seen_emails: set[str] = set()
    written = 0
    skipped_no_email = 0
    skipped_dupes = 0

    with open(input_path, encoding="latin-1") as fin, open(
        output_path, "w", encoding="utf-8", newline=""
    ) as fout:
        reader = csv.DictReader(fin, delimiter=";")
        writer = csv.DictWriter(fout, fieldnames=["email", "phone", "fn", "ln"])
        writer.writeheader()

        for row in reader:
            email = normalize_email(row.get("Email", ""))
            if not email:
                skipped_no_email += 1
                continue
            if email in seen_emails:
                skipped_dupes += 1
                continue
            seen_emails.add(email)

            writer.writerow(
                {
                    "email": email,
                    "phone": normalize_phone(row.get("Telefono", "")),
                    "fn": normalize_text(row.get("Nombre", "")),
                    "ln": normalize_text(row.get("Apellido", "")),
                }
            )
            written += 1

    print(f"Filas escritas:     {written}")
    print(f"Filas sin email:    {skipped_no_email}")
    print(f"Duplicados:         {skipped_dupes}")
    print(f"Salida:             {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    build(sys.argv[1], sys.argv[2])
