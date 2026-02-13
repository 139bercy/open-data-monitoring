import os
from io import BytesIO

from playwright.async_api import async_playwright

from domain.datasets.aggregate import Dataset


class PlaywrightReportGenerator:
    """
    Générateur de rapport utilisant Playwright pour capturer la version optimisée
    pour l'impression de la page frontend.
    """

    def __init__(self, base_url: str = None):
        # En développement, on cible le serveur Vite
        self.base_url = base_url or os.getenv("FRONTEND_URL", "http://localhost:5173")

    async def generate_audit_report(self, dataset: Dataset) -> BytesIO:
        """
        Navigue vers la route du rapport frontend et exporte en PDF.
        """
        async with async_playwright() as p:
            # Lancement en mode headless
            browser = await p.chromium.launch(headless=True)

            # Configuration du contexte pour simuler un écran standard
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800}, user_agent="OpenDataMonitoring-Bot/1.0"
            )

            page = await context.new_page()

            # Debug: Capture console logs from the frontend
            page.on("console", lambda msg: print(f"PLAYWRIGHT CONSOLE [{msg.type}]: {msg.text}"))
            page.on("pageerror", lambda err: print(f"PLAYWRIGHT ERROR: {err}"))

            # URL de la page de rapport dédiée
            report_url = f"{self.base_url}/reports/audit/{dataset.id}"

            try:
                # On attend que le réseau soit inactif (fin des chargements API)
                print(f"PLAYWRIGHT navigating to: {report_url}")
                await page.goto(report_url, wait_until="networkidle", timeout=30000)

                # On s'assure que le contenu principal est visible via l'ID spécifique
                await page.wait_for_selector("#report-main-title", timeout=15000)

                # Petit délai supplémentaire pour s'assurer que les graphiques/animations (si présents) se stabilisent
                await page.wait_for_timeout(1000)

                # Export au format A4 avec les styles @media print
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
