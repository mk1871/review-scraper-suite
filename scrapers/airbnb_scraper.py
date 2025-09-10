# scrapers/airbnb_scraper.py

import logging
from typing import List

from playwright.sync_api import sync_playwright

from config.selectors import AIRBNB_SELECTORS
from models.review import Review
from .base_scraper import BaseScraper  # Importación relativa

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str):
        super().__init__(floor)
        self.url = url

    def _open_date_filter(self, page):
        """
        Localiza y hace clic en el selector de fechas para abrir el calendario.
        """
        print("📅 Buscando selector de fechas...")
        try:
            # Usamos el selector del archivo de configuración
            date_selector_container = page.wait_for_selector(
                AIRBNB_SELECTORS['date_filter_container'],
                timeout=10000
            )
            print("✅ Selector de fechas encontrado.")

            # Buscamos el botón dentro del contenedor
            filter_button = date_selector_container.query_selector(
                'button'  # Podríamos también añadir esto al selectors.py si es estable
            )
            if filter_button:
                print("👆 Haciendo clic en el botón del selector de fechas...")
                filter_button.click()
                print("✅ Clic realizado. Panel de fechas debería estar abierto.")
            else:
                print("❌ No se encontró el botón dentro del selector de fechas.")

        except Exception as e:
            print(f"❌ Error al intentar abrir el filtro de fechas: {e}")

    def scrape(self) -> List[Review]:
        print("🔌 Conectando a Chrome en modo remoto...")
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Conectado a Chrome")
                context = browser.contexts[0]
                page = context.new_page()

                print(f"🌍 Navegando a: {self.url}")
                page.goto(self.url)

                # --- NUEVO: Probar interacción con fechas ---
                self._open_date_filter(page)
                # --- FIN NUEVO ---

                # Pausa para observar en el navegador
                print("⏳ Pausando 10 segundos para observar...")
                page.wait_for_timeout(10000)  # 10 segundos
                #
                # # Esperar a que cargue el contenedor de reseñas
                # page.wait_for_selector(AIRBNB_SELECTORS['reviews_container'], timeout=15000)
                # print("✅ Contenedor de reseñas encontrado")
                #
                # reviews_elements = page.query_selector_all(AIRBNB_SELECTORS['review_items'])
                # print(f"📝 Encontradas {len(reviews_elements)} reseñas")
                #
                # for i, elem in enumerate(reviews_elements):
                #     try:
                #         print(f"  → Procesando reseña {i + 1}...")
                #
                #         # Extraer datos
                #         review_date_str = elem.query_selector(AIRBNB_SELECTORS['review_date']).inner_text()
                #         check_in_date_str = elem.query_selector(AIRBNB_SELECTORS['check_in_date']).inner_text()
                #         rating_str = elem.query_selector(AIRBNB_SELECTORS['rating']).inner_text()
                #         guest_name = elem.query_selector(AIRBNB_SELECTORS['guest_name']).inner_text()
                #         full_comment = elem.query_selector(AIRBNB_SELECTORS['full_comment']).inner_text()
                #
                #         # Parsear fechas
                #         review_date = datetime.strptime(review_date_str.strip(), "%d/%m/%Y").date()
                #         check_in_date = datetime.strptime(check_in_date_str.strip(), "%d/%m/%Y").date()
                #
                #         # Formatear valoración
                #         rating = f"{int(rating_str)}*"
                #
                #         # Extraer quejas y sugerencias (si existen)
                #         complaints_elem = elem.query_selector(AIRBNB_SELECTORS['complaints'])
                #         complaints_summary = complaints_elem.inner_text() if complaints_elem else ""
                #
                #         suggestions_elem = elem.query_selector(AIRBNB_SELECTORS['suggestions'])
                #         suggestions = suggestions_elem.inner_text() if suggestions_elem else ""
                #
                #         # Crear objeto Review
                #         review = Review(
                #             review_date=review_date,
                #             check_in_date=check_in_date,
                #             platform="Airbnb",
                #             rating=rating,
                #             guest_name=guest_name,
                #             floor=self.floor,
                #             complaints_summary=complaints_summary,
                #             suggestions=suggestions,
                #             full_comment=full_comment,
                #             added_date=None
                #         )
                #         self.add_review(review)
                #         print(f"    ✅ Reseña de {guest_name} añadida")
                #
                #     except Exception as e:
                #         logger.error(f"❌ Error al procesar reseña {i + 1}: {e}")
                #         continue

                browser.close()
                return self.reviews

            except Exception as e:
                logger.error(f"❌ Error al conectar con Chrome: {e}")
                raise
