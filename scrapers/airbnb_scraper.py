# scrapers/airbnb_scraper.py (SCRAPING COMPLETO)

import logging
import re
from datetime import datetime, date
from typing import List, Optional, Tuple

from playwright.sync_api import sync_playwright, Page

from config.selectors import AIRBNB_SELECTORS
from models.review import Review
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str, start_date: str = None, end_date: str = None):
        super().__init__(floor)
        self.url = url
        self.start_date = start_date or "2025-07-01"
        self.end_date = end_date or date.today().strftime("%Y-%m-%d")
        self.scraped_reviews = set()  # Para evitar duplicados

    def _log_step(self, message: str, level: str = "info"):
        log_method = getattr(logger, level)
        log_method(f"[{self.floor}] {message}")

    def _calculate_days_from_today(self, target_date: str) -> int:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        today = date.today()
        delta = (target - today).days - 1  # Ajuste para Airbnb
        return delta

    def _build_url_with_date_range(self, start_date: str, end_date: str) -> str:
        ds_start = self._calculate_days_from_today(start_date)
        ds_end = self._calculate_days_from_today(end_date)

        # URL para vista de limpieza
        base_url = self.url.replace('/overall/', '/cleanliness/')
        if '/reviews?' not in base_url:
            base_url = base_url + '/reviews?'
        else:
            base_url = base_url.split('?')[0] + '?'

        return f"{base_url}ds-start={ds_start}&ds-end={ds_end}"

    def _parse_stay_dates(self, date_text: str) -> Tuple[Optional[date], Optional[date]]:
        """Convierte texto de fechas a objetos date"""
        try:
            # Patrones: "15–16 ago 2025" o "29 may–1 jun 2025"
            patterns = [
                r'(\d{1,2})[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',
                r'(\d{1,2})\s+(\w+)[–\-](\d{1,2})\s+(\w+)\s+(\d{4})'
            ]

            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    if len(match.groups()) == 4:
                        # Formato: 15–16 ago 2025
                        start_day, end_day, month_str, year = match.groups()
                        start_month = month_str
                        end_month = month_str
                    else:
                        # Formato: 29 may–1 jun 2025
                        start_day, start_month, end_day, end_month, year = match.groups()

                    # Convertir nombres de meses a números
                    months_es = {
                        'ene': 1, 'enero': 1, 'feb': 2, 'febrero': 2, 'mar': 3, 'marzo': 3,
                        'abr': 4, 'abril': 4, 'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6,
                        'jul': 7, 'julio': 7, 'ago': 8, 'agosto': 8, 'sep': 9, 'septiembre': 9,
                        'oct': 10, 'octubre': 10, 'nov': 11, 'noviembre': 11, 'dic': 12, 'diciembre': 12
                    }

                    start_month_num = months_es.get(start_month.lower(), 1)
                    end_month_num = months_es.get(end_month.lower(), 1)

                    check_in = date(int(year), start_month_num, int(start_day))
                    check_out = date(int(year), end_month_num, int(end_day))

                    return check_in, check_out

        except Exception as e:
            self._log_step(f"Error parseando fechas '{date_text}': {e}", "warning")

        return None, None

    def _extract_rating(self, element) -> str:
        """Extrae la valoración numérica del elemento de rating"""
        try:
            # Buscar el número en el texto del aria-label
            aria_label = element.get_attribute('aria-label') or ''
            match = re.search(r'(\d+)', aria_label)
            if match:
                return f"{match.group(1)}*"

            # Alternativa: buscar en los spans internos
            rating_span = element.query_selector('span[aria-hidden="true"]')
            if rating_span:
                return f"{rating_span.inner_text().strip()}*"

        except Exception as e:
            self._log_step(f"Error extrayendo rating: {e}", "warning")

        return "N/A"

    def _scrape_reviews_page(self, page: Page) -> int:
        """Extrae todas las reseñas de la página actual"""
        reviews_count = 0

        try:
            review_containers = page.query_selector_all(AIRBNB_SELECTORS['review_container'])
            self._log_step(f"Encontrados {len(review_containers)} contenedores de reseña")

            for container in review_containers:
                try:
                    # Extraer datos de la reseña
                    guest_name_elem = container.query_selector(AIRBNB_SELECTORS['guest_name'])
                    dates_elem = container.query_selector(AIRBNB_SELECTORS['stay_dates'])
                    cleanliness_elem = container.query_selector(AIRBNB_SELECTORS['cleanliness_rating'])
                    general_elem = container.query_selector(AIRBNB_SELECTORS['general_rating'])
                    text_elem = container.query_selector(AIRBNB_SELECTORS['review_text'])

                    if not all([guest_name_elem, dates_elem, general_elem]):
                        continue

                    guest_name = guest_name_elem.inner_text().strip()
                    dates_text = dates_elem.inner_text().strip()
                    review_text = text_elem.inner_text().strip() if text_elem else ""

                    # Parsear fechas
                    check_in_date, check_out_date = self._parse_stay_dates(dates_text)
                    if not check_in_date:
                        continue

                    # Usar fecha de check-out como fecha de reseña (aproximación)
                    review_date = check_out_date or check_in_date

                    # Extraer ratings
                    general_rating = self._extract_rating(general_elem)
                    cleanliness_rating = self._extract_rating(cleanliness_elem) if cleanliness_elem else "N/A"

                    # Crear ID único para evitar duplicados
                    review_id = f"{guest_name}_{review_date.strftime('%Y%m%d')}_{self.floor}"

                    if review_id in self.scraped_reviews:
                        self._log_step(f"Reseña duplicada omitida: {guest_name} - {review_date}")
                        continue

                    # Crear objeto Review
                    review = Review(
                        review_date=review_date,
                        check_in_date=check_in_date,
                        platform="Airbnb",
                        rating=general_rating,
                        guest_name=guest_name,
                        floor=self.floor,
                        complaints_summary="",  # Por implementar
                        suggestions="",  # Por implementar
                        action_plan="",  # Por implementar
                        full_comment=review_text,
                        added_date=date.today()
                    )

                    # Agregar campo adicional para rating de limpieza
                    review.cleanliness_rating = cleanliness_rating

                    self.add_review(review)
                    self.scraped_reviews.add(review_id)
                    reviews_count += 1

                    self._log_step(f"Reseña añadida: {guest_name} - {review_date} - {general_rating}")

                except Exception as e:
                    self._log_step(f"Error procesando reseña: {e}", "warning")
                    continue

        except Exception as e:
            self._log_step(f"Error en scrape_reviews_page: {e}", "error")

        return reviews_count

    def _go_to_next_page(self, page: Page) -> bool:
        """Intenta ir a la siguiente página de resultados"""
        try:
            next_button = page.query_selector(AIRBNB_SELECTORS['next_page_button'])
            if next_button and not next_button.get_attribute('disabled'):
                next_button.click()
                page.wait_for_timeout(3000)  # Esperar carga
                return True
        except Exception as e:
            self._log_step(f"Error yendo a página siguiente: {e}", "warning")
        return False

    def scrape(self) -> List[Review]:
        self._log_step(f"Iniciando scraping completo para: {self.url}")

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
                page = context.new_page()

                # Navegar a URL con filtros
                target_url = self._build_url_with_date_range(self.start_date, self.end_date)
                self._log_step(f"Navegando a: {target_url}")
                page.goto(target_url, wait_until="networkidle")
                page.wait_for_timeout(5000)

                # Scrapear todas las páginas
                total_reviews = 0
                page_number = 1

                while True:
                    self._log_step(f"Scrapeando página {page_number}")
                    reviews_count = self._scrape_reviews_page(page)
                    total_reviews += reviews_count
                    self._log_step(f"Página {page_number}: {reviews_count} reseñas")

                    # Intentar ir a siguiente página
                    if not self._go_to_next_page(page):
                        break

                    page_number += 1

                self._log_step(f"Scraping completado. Total: {total_reviews} reseñas")
                browser.close()
                return self.reviews

            except Exception as e:
                self._log_step(f"Error crítico: {e}", "error")
                try:
                    browser.close()
                except:
                    pass
                raise
