"""Scraper de la Biblioteca de Anuncios de Facebook.

Devuelve los N anuncios activos con mayor tiempo en circulación para una
combinación de país + palabra clave (nicho).

Uso:
    python scripts/fb_ads_scraper.py \\
        --country CL \\
        --query "cetogenica" \\
        --top 10 \\
        --out top_ads.json

Requisitos:
    pip install playwright python-dateutil
    playwright install chromium

Notas:
    - La Ad Library API oficial de Meta solo expone anuncios politicos/sociales,
      por eso este scraper consume el frontend publico.
    - Facebook cambia el DOM con frecuencia; los selectores aqui usan texto
      visible ("Library ID", "Started running on") que ha sido estable.
    - Respeta los Terminos de Servicio de Meta y la legislacion local antes de
      automatizar consultas masivas.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlencode

from dateutil import parser as dateparser
from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright


AD_LIBRARY_BASE = "https://www.facebook.com/ads/library/"

# Localizaciones del texto "Started running on" que muestra la Biblioteca.
START_PATTERNS = [
    re.compile(r"Started running on\s+(.+?)(?:\s*[·•]|$)", re.IGNORECASE),
    re.compile(r"Comenzó a publicarse el\s+(.+?)(?:\s*[·•]|$)", re.IGNORECASE),
    re.compile(r"Empezó a publicarse el\s+(.+?)(?:\s*[·•]|$)", re.IGNORECASE),
]
LIBRARY_ID_PATTERN = re.compile(r"(?:Library ID|ID de la biblioteca)[:\s]+(\d+)", re.IGNORECASE)


@dataclass
class Ad:
    library_id: str
    advertiser: str
    started_on: str  # ISO date
    days_running: int
    ad_text: str
    url: str


def build_url(country: str, query: str) -> str:
    params = {
        "active_status": "active",
        "ad_type": "all",
        "country": country,
        "q": query,
        "search_type": "keyword_unordered",
        "media_type": "all",
    }
    return f"{AD_LIBRARY_BASE}?{urlencode(params)}"


def dismiss_cookie_banner(page: Page) -> None:
    for label in ("Allow all cookies", "Permitir todas las cookies", "Only allow essential cookies"):
        try:
            page.get_by_role("button", name=re.compile(label, re.IGNORECASE)).first.click(timeout=2000)
            return
        except PWTimeout:
            continue
        except Exception:
            continue


def scroll_until_stable(page: Page, max_rounds: int = 40, settle_ms: int = 1500) -> None:
    """Hace scroll hasta que la altura del documento deja de crecer."""
    last_height = 0
    for _ in range(max_rounds):
        page.mouse.wheel(0, 20000)
        page.wait_for_timeout(settle_ms)
        height = page.evaluate("document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height


def parse_started_date(text: str) -> datetime | None:
    for pat in START_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                return dateparser.parse(m.group(1), fuzzy=True, dayfirst=True)
            except (ValueError, OverflowError):
                continue
    return None


def extract_ads(page: Page) -> list[Ad]:
    # Cada tarjeta de anuncio renderiza el texto "Library ID". Tomamos los
    # ancestros que contienen ese marcador para aislar la tarjeta completa.
    cards = page.locator("div", has_text=re.compile(r"Library ID|ID de la biblioteca")).all()
    seen: set[str] = set()
    ads: list[Ad] = []
    today = datetime.now(timezone.utc).date()

    for card in cards:
        try:
            text = card.inner_text(timeout=1000)
        except PWTimeout:
            continue

        lid_match = LIBRARY_ID_PATTERN.search(text)
        if not lid_match:
            continue
        library_id = lid_match.group(1)
        if library_id in seen:
            continue

        started = parse_started_date(text)
        if not started:
            continue

        # Heuristica para el nombre del anunciante: primera linea no vacia.
        advertiser = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        # Texto del anuncio: lineas tras el bloque de metadatos.
        body_lines = [
            ln.strip()
            for ln in text.splitlines()
            if ln.strip()
            and "Library ID" not in ln
            and "ID de la biblioteca" not in ln
            and not parse_started_date(ln)
        ]
        ad_text = " ".join(body_lines[1:6])[:500]

        seen.add(library_id)
        ads.append(
            Ad(
                library_id=library_id,
                advertiser=advertiser[:120],
                started_on=started.date().isoformat(),
                days_running=(today - started.date()).days,
                ad_text=ad_text,
                url=f"{AD_LIBRARY_BASE}?id={library_id}",
            )
        )

    return ads


def scrape(country: str, query: str, top: int, headless: bool) -> list[Ad]:
    url = build_url(country, query)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="es-CL",
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        dismiss_cookie_banner(page)
        try:
            page.wait_for_selector("text=/Library ID|ID de la biblioteca/i", timeout=15000)
        except PWTimeout:
            print("No se encontraron anuncios para esa consulta.", file=sys.stderr)
            browser.close()
            return []

        scroll_until_stable(page)
        ads = extract_ads(page)
        browser.close()

    ads.sort(key=lambda a: a.days_running, reverse=True)
    return ads[:top]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", default="CL", help="Codigo ISO de pais (default: CL)")
    parser.add_argument("--query", required=True, help="Palabra clave del nicho")
    parser.add_argument("--top", type=int, default=10, help="Cantidad de anuncios a devolver")
    parser.add_argument("--out", help="Ruta de archivo JSON para guardar resultados")
    parser.add_argument("--no-headless", action="store_true", help="Mostrar el navegador")
    args = parser.parse_args(list(argv) if argv is not None else None)

    ads = scrape(args.country, args.query, args.top, headless=not args.no_headless)

    payload = [asdict(a) for a in ads]
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Guardados {len(payload)} anuncios en {args.out}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
