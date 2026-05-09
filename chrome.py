"""Integración con Chrome vía Playwright.

Provee dos capacidades:
- scrape_ketooficial(): extrae los precios actuales del sitio público.
- whatsapp_web_send(): envía un mensaje de WhatsApp usando WhatsApp Web,
  reutilizando la sesión persistida (escaneo único de QR).

Requiere instalar el navegador una vez:
    playwright install chromium
"""

import os
import re
from contextlib import contextmanager
from urllib.parse import quote

from playwright.sync_api import sync_playwright

KETOOFICIAL_URL = os.getenv("KETOOFICIAL_URL", "https://ketooficial.com/dieta-keto/")
WHATSAPP_PROFILE_DIR = os.getenv("WHATSAPP_PROFILE_DIR", ".wa_profile")
CHROME_HEADLESS = os.getenv("CHROME_HEADLESS", "true").lower() == "true"


@contextmanager
def _browser(headless=None):
    if headless is None:
        headless = CHROME_HEADLESS
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        try:
            yield context
        finally:
            context.close()
            browser.close()


def scrape_ketooficial(url=KETOOFICIAL_URL, timeout_ms=15000):
    """Devuelve un dict {meses: precio_clp} con los precios listados en el sitio."""
    with _browser() as context:
        page = context.new_page()
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        text = page.inner_text("body")

    prices = {}
    for months, amount in re.findall(
        r"(\d)\s*mes(?:es)?[^$]{0,40}\$\s*([\d\.]+)", text, flags=re.IGNORECASE
    ):
        try:
            prices[int(months)] = int(amount.replace(".", ""))
        except ValueError:
            continue
    return prices


def whatsapp_web_send(to, message, profile_dir=WHATSAPP_PROFILE_DIR, timeout_ms=60000):
    """Envía `message` al número `to` (formato internacional sin '+') usando WhatsApp Web.

    La primera ejecución requiere escanear el código QR; el perfil queda
    persistido en `profile_dir` para futuras sesiones.
    """
    os.makedirs(profile_dir, exist_ok=True)
    url = f"https://web.whatsapp.com/send?phone={quote(to)}&text={quote(message)}"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile_dir, headless=False
        )
        page = context.new_page()
        page.goto(url, timeout=timeout_ms)
        page.wait_for_selector('div[contenteditable="true"][data-tab="10"]', timeout=timeout_ms)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        context.close()
