"""Cambia el número de WhatsApp vinculado a la Página de Facebook 'Keto Oficial Chile Y Mundo'.

Uso:
    pip install playwright && playwright install chromium
    export FB_EMAIL='...' FB_PASSWORD='...'
    python facebook_navigate.py

Variables de entorno opcionales:
    FB_PAGE_NAME      Nombre de la página (default: 'Keto Oficial Chile Y Mundo')
    NEW_WA_NUMBER     Número nuevo en E.164 (default: '+56936475173')
    OLD_WA_NUMBER     Número viejo a desvincular (default: '+56940744890')
    ROUTE             'A' = Configuración de la Página, 'B' = Business Suite (default: 'A')

El script pausa en el paso del código SMS: ingresalo a mano en el browser y presioná
'Resume' en el Playwright Inspector para continuar.
"""
import os
import sys

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

FB_EMAIL = os.environ.get("FB_EMAIL")
FB_PASSWORD = os.environ.get("FB_PASSWORD")
PAGE_NAME = os.environ.get("FB_PAGE_NAME", "Keto Oficial Chile Y Mundo")
NEW_NUMBER = os.environ.get("NEW_WA_NUMBER", "+56936475173")
OLD_NUMBER = os.environ.get("OLD_WA_NUMBER", "+56940744890")
ROUTE = os.environ.get("ROUTE", "A").upper()


def login(page: Page) -> None:
    page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    try:
        page.get_by_role("button", name="Allow all cookies").click(timeout=3000)
    except PWTimeout:
        pass
    page.locator("#email").fill(FB_EMAIL)
    page.locator("#pass").fill(FB_PASSWORD)
    page.locator("button[name='login']").click()
    page.wait_for_load_state("networkidle")
    if "checkpoint" in page.url or "two_step" in page.url:
        print("⚠️  Facebook pide verificación adicional. Completala a mano en el browser.")
        page.pause()


def switch_to_page_profile(page: Page) -> None:
    page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    page.get_by_role("link", name="Your profile").click()
    page.get_by_role("link", name=f"Switch into {PAGE_NAME}").click()
    page.wait_for_load_state("networkidle")


def route_a(page: Page) -> None:
    switch_to_page_profile(page)
    page.goto("https://www.facebook.com/settings", wait_until="domcontentloaded")
    page.get_by_role("link", name="WhatsApp").first.click()
    page.wait_for_load_state("networkidle")

    print(f"🔍 Buscando número viejo {OLD_NUMBER} para desvincular…")
    old_entry = page.get_by_text(OLD_NUMBER.replace("+", ""), exact=False).first
    if old_entry.is_visible():
        old_entry.click()
        try:
            page.get_by_role("button", name="Unlink").click(timeout=3000)
            page.get_by_role("button", name="Confirm").click(timeout=3000)
        except PWTimeout:
            print("ℹ️  No encontré botón 'Unlink' — puede que ya esté desvinculado.")

    print(f"➕ Conectando número nuevo {NEW_NUMBER}…")
    page.get_by_role("button", name="Connect WhatsApp").click()
    page.locator("input[type='tel']").fill(NEW_NUMBER)
    page.get_by_role("button", name="Send code").click()


def route_b(page: Page) -> None:
    page.goto("https://business.facebook.com/", wait_until="domcontentloaded")
    page.get_by_role("link", name="Settings").click()
    page.get_by_role("link", name="Accounts").click()
    page.get_by_role("link", name="WhatsApp Business").click()
    page.get_by_role("button", name="Add").click()
    page.locator("input[type='tel']").fill(NEW_NUMBER)
    page.get_by_role("button", name="Send code").click()


def main() -> int:
    if not FB_EMAIL or not FB_PASSWORD:
        print("ERROR: definí FB_EMAIL y FB_PASSWORD en el entorno.", file=sys.stderr)
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        context = browser.new_context(locale="es-CL")
        page = context.new_page()

        login(page)
        (route_a if ROUTE == "A" else route_b)(page)

        print("\n📱 Meta mandó el código SMS al Samsung. Ingresalo en el browser.")
        print("   Presioná 'Resume' en el Playwright Inspector cuando termines.\n")
        page.pause()

        print("✅ Listo. Verificá en business.facebook.com que el número quedó conectado.")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
