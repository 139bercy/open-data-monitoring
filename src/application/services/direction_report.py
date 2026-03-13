import os
from io import BytesIO

from playwright.async_api import async_playwright


class DirectionReportGenerator:
    """
    Générateur de rapport utilisant Playwright pour capturer la version optimisée
    pour l'impression de la page de synthèse de direction frontend.
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("FRONTEND_URL", "http://localhost:5173")

    async def generate_direction_summary_report(self, direction: str, token: str = None) -> BytesIO:
        """
        Navigue vers la route du rapport direction frontend et exporte en PDF.
        """
        async with async_playwright() as p:
            # Lancement en mode headless
            browser = await p.chromium.launch(headless=True)

            # Configuration du contexte pour simuler un écran standard
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800}, user_agent="OpenDataMonitoring-Bot/1.0"
            )

            # Injection du token dans le localStorage pour l'authentification frontend
            if token:
                await context.add_init_script(f"localStorage.setItem('odm_token', '{token}');")

            page = await context.new_page()

            # Debug: Capture console logs from the frontend
            page.on("console", lambda msg: print(f"PLAYWRIGHT CONSOLE [{msg.type}]: {msg.text}"))
            page.on("pageerror", lambda err: print(f"PLAYWRIGHT ERROR: {err}"))

            # URl encodée de la page de rapport dédiée
            import urllib.parse

            encoded_direction = urllib.parse.quote(direction)
            report_url = f"{self.base_url}/reports/direction-summary/{encoded_direction}"

            try:
                # On attend que le réseau soit inactif (fin des chargements API)
                print(f"PLAYWRIGHT navigating to: {report_url}")
                await page.goto(report_url, wait_until="networkidle", timeout=30000)

                # TODO: S'assurer que "#report-ready" est présent sur le frontend
                # Pour l'instant on attend juste le titre principal
                try:
                    await page.wait_for_selector("h1", timeout=15000)
                except Exception as e:
                    print(f"Warning: h1 selector not found, proceeding anyway. {e}")

                # Petit délai supplémentaire
                await page.wait_for_timeout(1000)

                # Emulate print media for DSFR
                await page.emulate_media(media="print")

                # Export au format A4 avec print_background pour DSFR
                pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0cm", "right": "0cm", "bottom": "0cm", "left": "0cm"},
                    display_header_footer=False,
                    scale=1.0,
                )
            finally:
                await browser.close()

            return BytesIO(pdf_bytes)
