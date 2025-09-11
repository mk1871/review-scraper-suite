# scrapers/airbnb_scraper.py (VERSIÓN OPTIMIZADA)

import hashlib
import logging
import re
from datetime import datetime, date
from typing import List, Optional, Tuple, Set

from playwright.sync_api import sync_playwright, Page

from config.selectors import AIRBNB_SELECTORS
from models.review import Review
from utils.gsheet_utils import get_existing_reviews_hashes  # Nueva función
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str, start_date: str = None, end_date: str = None):
        super().__init__(floor)
        self.url = url
        self.start_date = datetime.strptime(start_date or "2025-07-01", "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date or date.today().strftime("%Y-%m-%d"), "%Y-%m-%d").date()
        self.existing_hashes: Set[str] = set()
        self.min_review_date = None  # Para parada temprana

    def _log_step(self, message: str, level: str = "info"):
        log_method = getattr(logger, level)
        log_method(f"[{self.floor}] {message}")

    def _load_existing_hashes(self):
        """Cargar hashes de reseñas existentes para evitar duplicados"""
        try:
            self.existing_hashes = get_existing_reviews_hashes(self.floor)
            self._log_step(f"Loaded {len(self.existing_hashes)} existing review hashes")
        except Exception as e:
            self._log_step(f"Error loading existing hashes: {e}", "warning")

    def _generate_review_hash(self, guest_name: str, review_date: date, review_text: str) -> str:
        """Generar hash único para la reseña"""
        text_snippet = review_text[:100]  # Primeros 100 caracteres para hash
        unique_string = f"{guest_name}_{review_date.strftime('%Y%m%d')}_{self.floor}_{text_snippet}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _is_duplicate_review(self, guest_name: str, review_date: date, review_text: str) -> bool:
        """Verificar si la reseña ya existe"""
        review_hash = self._generate_review_hash(guest_name, review_date, review_text)
        return review_hash in self.existing_hashes

    def _parse_stay_dates(self, date_text: str) -> Tuple[Optional[date], Optional[date]]:
        """Convierte texto de fechas a objetos date"""
        try:
            # Patrones para diferentes formatos de fecha
            patterns = [
                r'(\d{1,2})[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',  # 15–16 ago 2025
                r'(\d{1,2})\s+(\w+)[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',  # 29 may–1 jun 2025
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # 15 ago 2025 (estadía de un día)
            ]

            months_es = {
                'ene': 1, 'enero': 1, 'feb': 2, 'febrero': 2, 'mar': 3, 'marzo': 3,
                'abr': 4, 'abril': 4, 'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6,
                'jul': 7, 'julio': 7, 'ago': 8, 'agosto': 8, 'sep': 9, 'septiembre': 9,
                'oct': 10, 'octubre': 10, 'nov': 11, 'noviembre': 11, 'dic': 12, 'diciembre': 12
            }

            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()

                    if len(groups) == 4:
                        # Formato: 15–16 ago 2025
                        start_day, end_day, month_str, year = groups
                        start_month = end_month = month_str
                    elif len(groups) == 5:
                        # Formato: 29 may–1 jun 2025
                        start_day, start_month, end_day, end_month, year = groups
                    elif len(groups) == 3:
                        # Formato: 15 ago 2025 (un día)
                        start_day, month_str, year = groups
                        end_day = start_day
                        start_month = end_month = month_str
                    else:
                        continue

                    start_month_num = months_es.get(start_month.lower().strip(), 1)
                    end_month_num = months_es.get(
                        end_month.lower().strip() if 'end_month' in locals() else start_month.lower().strip(), 1)

                    check_in = date(int(year), start_month_num, int(start_day))
                    check_out = date(int(year), end_month_num, int(end_day))

                    return check_in, check_out

        except Exception as e:
            self._log_step(f"Error parseando fechas '{date_text}': {e}", "warning")

        return None, None

    def _should_stop_scraping(self, review_date: date) -> bool:
        """Determinar si debemos dejar de scrapear por fecha"""
        if review_date < self.start_date:
            self._log_step(f"⏹️ Parando scraping: fecha {review_date} anterior al rango {self.start_date}")
            return True
        return False

    def _scrape_reviews_page(self, page: Page) -> Tuple[int, bool]:
        """Extrae reseñas de la página actual. Retorna (count, should_stop)"""
        reviews_count = 0
        should_stop = False

        try:
            review_containers = page.query_selector_all(AIRBNB_SELECTORS['review_container'])
            self._log_step(f"Encontrados {len(review_containers)} reseñas en página")

            for container in review_containers:
                try:
                    # Extraer datos básicos
                    guest_name_elem = container.query_selector(AIRBNB_SELECTORS['guest_name'])
                    dates_elem = container.query_selector(AIRBNB_SELECTORS['stay_dates'])
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

                    # Usar fecha de check-out como fecha de reseña
                    review_date = check_out_date or check_in_date

                    # VERIFICAR PARADA TEMPRANA
                    if self._should_stop_scraping(review_date):
                        should_stop = True
                        break

                    # VERIFICAR DUPLICADO
                    if self._is_duplicate_review(guest_name, review_date, review_text):
                        self._log_step(f"⏭️ Duplicado omitido: {guest_name} - {review_date}")
                        continue

                    # Extraer rating general
                    general_rating = self._extract_rating(general_elem)

                    # Crear objeto Review
                    review = Review(
                        review_date=review_date,
                        check_in_date=check_in_date,
                        platform="Airbnb",
                        rating=general_rating,
                        guest_name=guest_name,
                        floor=self.floor,
                        full_comment=review_text,
                        added_date=date.today()
                    )

                    # Extraer rating de limpieza si existe
                    cleanliness_elem = container.query_selector(AIRBNB_SELECTORS['cleanliness_rating'])
                    if cleanliness_elem:
                        review.cleanliness_rating = self._extract_rating(cleanliness_elem)

                    self.add_review(review)
                    reviews_count += 1

                    self._log_step(f"✅ Reseña nueva: {guest_name} - {review_date} - {general_rating}")

                    # Actualizar fecha mínima encontrada
                    if self.min_review_date is None or review_date < self.min_review_date:
                        self.min_review_date = review_date

                except Exception as e:
                    self._log_step(f"⚠️ Error procesando reseña: {e}", "warning")
                    continue

        except Exception as e:
            self._log_step(f"❌ Error en scrape_reviews_page: {e}", "error")

        return reviews_count, should_stop

    def scrape(self) -> List[Review]:
        """Scraping con parada inteligente por fecha"""
        self._log_step(f"🚀 Iniciando scraping inteligente para piso {self.floor}")
        self._log_step(f"Rango objetivo: {self.start_date} a {self.end_date}")

        # Cargar hashes existentes ANTES de empezar
        self._load_existing_hashes()

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
                page = context.new_page()

                # Navegar a URL con filtros
                target_url = self._build_url_with_date_range(
                    self.start_date.strftime("%Y-%m-%d"),
                    self.end_date.strftime("%Y-%m-%d")
                )
                page.goto(target_url, wait_until="networkidle")
                page.wait_for_timeout(5000)

                # Scraping con parada inteligente
                total_reviews = 0
                page_number = 1
                should_stop = False

                while not should_stop:
                    self._log_step(f"📄 Procesando página {page_number}")

                    reviews_count, should_stop = self._scrape_reviews_page(page)
                    total_reviews += reviews_count

                    self._log_step(f"Página {page_number}: {reviews_count} nuevas reseñas")

                    # Ir a siguiente página si no debemos parar
                    if not should_stop and not self._go_to_next_page(page):
                        break

                    page_number += 1

                self._log_step(f"🏁 Scraping completado. Total: {total_reviews} nuevas reseñas")
                browser.close()
                return self.reviews

            except Exception as e:
                self._log_step(f"❌ Error crítico: {e}", "error")
                try:
                    browser.close()
                except:
                    pass
                raise
