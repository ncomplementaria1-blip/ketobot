"""Scraper de la Facebook Ads Library.

Usa la API oficial de Meta (`/ads_archive`) para obtener los anuncios activos
con más tiempo de publicación en un país y nicho dado.

Requisitos:
- Variable de entorno FB_ACCESS_TOKEN: token de acceso de usuario o sistema con
  permiso `ads_read`. Obténlo en https://developers.facebook.com/tools/explorer/
  (la app debe estar aprobada para Ad Library API; el flujo está documentado en
  https://www.facebook.com/ads/library/api/).

Uso:
    python fb_ads_scraper.py
    python fb_ads_scraper.py --country CL --query "nutrición cetogénica" --limit 10
    python fb_ads_scraper.py --output ads.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Iterable, Iterator

import requests
from dotenv import load_dotenv

GRAPH_API_VERSION = os.getenv("FB_GRAPH_API_VERSION", "v21.0")
ADS_ARCHIVE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/ads_archive"

DEFAULT_FIELDS = [
    "id",
    "page_id",
    "page_name",
    "ad_creation_time",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_creative_link_captions",
    "ad_snapshot_url",
    "publisher_platforms",
    "languages",
]

# Términos por defecto para el nicho "Nutrición cetogénica" en español chileno.
DEFAULT_KETO_QUERY = (
    '"dieta keto" OR "dieta cetogénica" OR "nutrición cetogénica" OR keto'
)


@dataclass
class Ad:
    id: str
    page_id: str | None
    page_name: str | None
    ad_delivery_start_time: str | None
    ad_delivery_stop_time: str | None
    days_active: int | None
    ad_snapshot_url: str | None
    creative_body: str | None
    languages: list[str] | None
    publisher_platforms: list[str] | None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    # Meta returns ISO 8601, e.g. "2024-03-15T18:30:00+0000".
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _days_active(start: str | None, stop: str | None) -> int | None:
    start_dt = _parse_dt(start)
    if start_dt is None:
        return None
    end_dt = _parse_dt(stop) or datetime.now(tz=timezone.utc)
    return (end_dt - start_dt).days


def _normalize(raw: dict) -> Ad:
    bodies = raw.get("ad_creative_bodies") or []
    return Ad(
        id=raw["id"],
        page_id=raw.get("page_id"),
        page_name=raw.get("page_name"),
        ad_delivery_start_time=raw.get("ad_delivery_start_time"),
        ad_delivery_stop_time=raw.get("ad_delivery_stop_time"),
        days_active=_days_active(
            raw.get("ad_delivery_start_time"), raw.get("ad_delivery_stop_time")
        ),
        ad_snapshot_url=raw.get("ad_snapshot_url"),
        creative_body=bodies[0] if bodies else None,
        languages=raw.get("languages"),
        publisher_platforms=raw.get("publisher_platforms"),
    )


def fetch_ads(
    access_token: str,
    country: str = "CL",
    search_terms: str = DEFAULT_KETO_QUERY,
    fields: Iterable[str] = DEFAULT_FIELDS,
    page_size: int = 100,
    max_pages: int = 20,
    session: requests.Session | None = None,
) -> Iterator[dict]:
    """Itera por todos los anuncios activos que matchean la búsqueda.

    Hace paginación siguiendo `paging.next` hasta agotar resultados o llegar a
    `max_pages` (cota de seguridad para no consumir cuota).
    """
    sess = session or requests.Session()
    params = {
        "access_token": access_token,
        "ad_reached_countries": json.dumps([country]),
        "ad_active_status": "ACTIVE",
        "ad_type": "ALL",
        "search_terms": search_terms,
        "fields": ",".join(fields),
        "limit": page_size,
    }

    url = ADS_ARCHIVE_URL
    pages = 0
    while url and pages < max_pages:
        resp = sess.get(url, params=params if pages == 0 else None, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        for item in payload.get("data", []):
            yield item
        url = payload.get("paging", {}).get("next")
        pages += 1


def top_longest_running(
    access_token: str,
    country: str = "CL",
    search_terms: str = DEFAULT_KETO_QUERY,
    limit: int = 10,
    **fetch_kwargs,
) -> list[Ad]:
    """Devuelve los `limit` anuncios activos con más días en circulación."""
    ads = [
        _normalize(raw)
        for raw in fetch_ads(
            access_token,
            country=country,
            search_terms=search_terms,
            **fetch_kwargs,
        )
    ]
    ads.sort(key=lambda a: a.days_active or -1, reverse=True)
    return ads[:limit]


def _print_table(ads: list[Ad]) -> None:
    if not ads:
        print("Sin resultados.")
        return
    print(f"\n{'#':>2}  {'Días':>5}  {'Página':<35}  Snapshot")
    print("-" * 100)
    for i, ad in enumerate(ads, 1):
        page = (ad.page_name or "?")[:33]
        days = ad.days_active if ad.days_active is not None else "?"
        print(f"{i:>2}  {days:>5}  {page:<35}  {ad.ad_snapshot_url or ''}")
    print()


def main(argv: list[str] | None = None) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", default="CL", help="ISO code (default: CL)")
    parser.add_argument(
        "--query",
        default=DEFAULT_KETO_QUERY,
        help="Términos de búsqueda (default: nicho keto en español)",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--output",
        help="Ruta opcional para guardar el resultado completo en JSON",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Tope de páginas a recorrer en la API (cota de cuota)",
    )
    args = parser.parse_args(argv)

    token = os.getenv("FB_ACCESS_TOKEN")
    if not token:
        print(
            "ERROR: falta FB_ACCESS_TOKEN. Configúralo en .env o como variable "
            "de entorno. Ver instrucciones en la cabecera de este archivo.",
            file=sys.stderr,
        )
        return 2

    ads = top_longest_running(
        token,
        country=args.country,
        search_terms=args.query,
        limit=args.limit,
        max_pages=args.max_pages,
    )

    _print_table(ads)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump([asdict(a) for a in ads], fh, ensure_ascii=False, indent=2)
        print(f"Guardado en {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
