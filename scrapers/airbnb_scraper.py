# scrapers/airbnb_scraper.py

from playwright.sync_api import sync_playwright
from .base_scraper import BaseScraper  # Importación relativa
from models.review import Review
from config.selectors import AIRBNB_SELECTORS
import logging
from datetime import datetime, date
from typing import List
import time

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str):
        super().__init__(floor)
        self.url = url

    def scrape(self) -> List[Review]:
        print("🔌 Conectando a Chrome en modo remoto...")
        with sync_playwright() as p:
            try:
                # Conectarse a la instancia de Chrome ya abierta
                browser = p.chromium.connect_over_cdp("http://localhost:9222")
                print("✅ Conectado a Chrome")

                # Usar el primer contexto disponible (tu perfil)
                context = browser.contexts[0]
                page = context.new_page()

                print(f"🌍 Navegando a: {self.url}")
                page.goto(self.url)

                # Esperar a que cargue el contenedor de reseñas
                page.wait_for_selector(AIRBNB_SELECTORS['reviews_container'], timeout=15000)
                print("✅ Contenedor de reseñas encontrado")

                reviews_elements = page.query_selector_all(AIRBNB_SELECTORS['review_items'])
                print(f"📝 Encontradas {len(reviews_elements)} reseñas")

                for i, elem in enumerate(reviews_elements):
                    try:
                        print(f"  → Procesando reseña {i + 1}...")

                        # Extraer datos
                        review_date_str = elem.query_selector(AIRBNB_SELECTORS['review_date']).inner_text()
                        check_in_date_str = elem.query_selector(AIRBNB_SELECTORS['check_in_date']).inner_text()
                        rating_str = elem.query_selector(AIRBNB_SELECTORS['rating']).inner_text()
                        guest_name = elem.query_selector(AIRBNB_SELECTORS['guest_name']).inner_text()
                        full_comment = elem.query_selector(AIRBNB_SELECTORS['full_comment']).inner_text()

                        # Parsear fechas
                        review_date = datetime.strptime(review_date_str.strip(), "%d/%m/%Y").date()
                        check_in_date = datetime.strptime(check_in_date_str.strip(), "%d/%m/%Y").date()

                        # Formatear valoración
                        rating = f"{int(rating_str)}*"

                        # Extraer quejas y sugerencias (si existen)
                        complaints_elem = elem.query_selector(AIRBNB_SELECTORS['complaints'])
                        complaints_summary = complaints_elem.inner_text() if complaints_elem else ""

                        suggestions_elem = elem.query_selector(AIRBNB_SELECTORS['suggestions'])
                        suggestions = suggestions_elem.inner_text() if suggestions_elem else ""

                        # Crear objeto Review
                        review = Review(
                            review_date=review_date,
                            check_in_date=check_in_date,
                            platform="Airbnb",
                            rating=rating,
                            guest_name=guest_name,
                            floor=self.floor,
                            complaints_summary=complaints_summary,
                            suggestions=suggestions,
                            full_comment=full_comment,
                            added_date=None
                        )
                        self.add_review(review)
                        print(f"    ✅ Reseña de {guest_name} añadida")

                    except Exception as e:
                        logger.error(f"❌ Error al procesar reseña {i + 1}: {e}")
                        continue

                browser.close()
                return self.reviews

            except Exception as e:
                logger.error(f"❌ Error al conectar con Chrome: {e}")
                raise