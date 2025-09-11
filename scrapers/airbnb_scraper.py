# scrapers/airbnb_scraper.py
import logging
import re
import hashlib
from typing import List, Optional, Tuple, Set
from datetime import datetime, date
from playwright.sync_api import sync_playwright, Page

from config.selectors import AIRBNB_SELECTORS
from models.review import Review
from .base_scraper import BaseScraper
from utils.gsheet_utils import get_existing_reviews_hashes

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str, start_date: str = None, end_date: str = None):
        super().__init__(floor)
        self.url = url
        self.start_date = datetime.strptime(start_date or "2025-07-01", "%Y-%m-%d").date()
        self.end_date = datetime.strptime(end_date or date.today().strftime("%Y-%m-%d"), "%Y-%m-%d").date()
        self.existing_hashes: Set[str] = set()
        self.min_review_date = None
        self.max_review_date = None
        self.reviews_to_update = []

    def _log_step(self, message: str, level: str = "info"):
        log_method = getattr(logger, level)
        log_method(f"[{self.floor}] {message}")

    def _calculate_days_from_today(self, target_date: str) -> int:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        today = date.today()
        delta = (target - today).days
        self._log_step(f"Cálculo días: {target_date} -> {delta} días desde hoy")
        return delta

    def _build_url_with_date_range(self, start_date: str, end_date: str) -> str:
        ds_start = self._calculate_days_from_today(start_date)
        ds_end = self._calculate_days_from_today(end_date)

        self._log_step(f"Días relativos: start={ds_start}, end={ds_end}")

        base_url = self.url.replace('/overall/', '/cleanliness/')
        if '/reviews?' not in base_url:
            base_url = base_url + '/reviews?'
        else:
            base_url = base_url.split('?')[0] + '?'

        new_url = f"{base_url}ds-start={ds_start}&ds-end={ds_end}"
        self._log_step(f"URL construida: {new_url}")
        return new_url

    def _load_existing_hashes(self):
        try:
            self.existing_hashes = get_existing_reviews_hashes(self.floor)
            self._log_step(f"Cargados {len(self.existing_hashes)} hashes existentes")
        except Exception as e:
            self._log_step(f"Error cargando hashes existentes: {e}", "warning")

    def _generate_review_hash(self, guest_name: str, review_date: date, review_text: str) -> str:
        unique_string = f"{guest_name}_{review_date.strftime('%Y%m%d')}_{self.floor}"
        self._log_step(f"🔐 Hash basado en: '{guest_name}', '{review_date}', piso")
        review_hash = hashlib.md5(unique_string.encode()).hexdigest()
        self._log_step(f"🔐 Hash generado: {review_hash}")
        return review_hash

    def _is_duplicate_review(self, guest_name: str, review_date: date, review_text: str) -> bool:
        review_hash = self._generate_review_hash(guest_name, review_date, review_text)
        is_duplicate = review_hash in self.existing_hashes
        if is_duplicate:
            self._log_step(f"⏭️ Reseña duplicada detectada: {guest_name} - {review_date}")
            self._log_step(f"⏭️ Hash: {review_hash}")
        else:
            self._log_step(f"✅ Reseña nueva: {review_hash}")
        return is_duplicate

    def _parse_stay_dates(self, date_text: str) -> Tuple[Optional[date], Optional[date]]:
        self._log_step(f"Parseando fechas: '{date_text}'")
        try:
            patterns = [
                r'(\d{1,2})[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',
                r'(\d{1,2})\s+(\w+)[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',
            ]

            # Soporta abreviaturas exactas de Airbnb
            months_es = {
                'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4,
                'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
                'sep': 9, 'sept': 9, 'oct': 10,
                'nov': 11, 'dic': 12
            }

            for pattern in patterns:
                match = re.search(pattern, date_text, re.IGNORECASE)
                if match:
                    groups = match.groups()

                    if len(groups) == 4:
                        start_day, end_day, month_str, year = groups
                        start_month = end_month = month_str
                    elif len(groups) == 5:
                        start_day, start_month, end_day, end_month, year = groups
                    elif len(groups) == 3:
                        start_day, month_str, year = groups
                        end_day = start_day
                        start_month = end_month = month_str
                    else:
                        continue

                    start_month_num = months_es.get(start_month.lower().strip(), 1)
                    end_month_num = months_es.get(end_month.lower().strip(), 1)

                    check_in = date(int(year), start_month_num, int(start_day))
                    check_out = date(int(year), end_month_num, int(end_day))

                    self._log_step(f"✅ Fechas parseadas: check_in={check_in}, check_out={check_out}")
                    return check_in, check_out

        except Exception as e:
            self._log_step(f"❌ Error parseando fechas '{date_text}': {e}", "warning")

        self._log_step(f"❌ No se pudieron parsear las fechas: '{date_text}'")
        return None, None

    def _extract_rating(self, container) -> str:
        """Extrae la valoración numérica de un contenedor de rating"""
        try:
            # Buscar el elemento que contiene el valor del rating
            rating_element = container.query_selector(AIRBNB_SELECTORS['rating_value'])
            if rating_element:
                # Extraer del aria-label
                aria_label = rating_element.get_attribute('aria-label') or ''
                match = re.search(r'(\d+)', aria_label)
                if match:
                    rating = f"{match.group(1)}*"
                    self._log_step(f"⭐ Rating extraído de aria-label: {rating}")
                    return rating

            # Alternativa: buscar el número en elementos internos
            rating_span = container.query_selector(AIRBNB_SELECTORS['rating_stars'])
            if rating_span:
                rating_text = rating_span.inner_text().strip()
                if rating_text.isdigit():
                    rating = f"{rating_text}*"
                    self._log_step(f"⭐ Rating extraído de span: {rating}")
                    return rating

            # Último recurso: buscar cualquier número en el contenedor
            container_text = container.inner_text()
            match = re.search(r'(\d+)', container_text)
            if match:
                rating = f"{match.group(1)}*"
                self._log_step(f"⭐ Rating extraído de texto: {rating}")
                return rating

        except Exception as e:
            self._log_step(f"❌ Error extrayendo rating: {e}", "warning")

        self._log_step("❌ No se pudo extraer el rating")
        return "N/A"

    def _should_stop_scraping(self, review_date: date) -> bool:
        self._log_step(f"🔍 Verificando si parar: {review_date} < {self.start_date} = {review_date < self.start_date}")
        if review_date < self.start_date:
            self._log_step(f"⏹️ ¡PARANDO SCRAPING! Fecha {review_date} es anterior al rango {self.start_date}")
            return True
        return False

    def _scrape_reviews_page(self, page: Page) -> Tuple[int, bool]:
        reviews_count = 0
        should_stop = False

        try:
            review_containers = page.query_selector_all(AIRBNB_SELECTORS['review_container'])
            self._log_step(f"📄 Encontrados {len(review_containers)} contenedores de reseña")

            for i, container in enumerate(review_containers):
                try:
                    self._log_step(f"🔍 Procesando reseña {i + 1}/{len(review_containers)}")

                    # Extraer elementos
                    guest_name_elem = container.query_selector(AIRBNB_SELECTORS['guest_name'])
                    dates_elem = container.query_selector(AIRBNB_SELECTORS['stay_dates'])
                    text_elem = container.query_selector(AIRBNB_SELECTORS['review_text'])

                    # Extraer ratings
                    cleanliness_container = container.query_selector(AIRBNB_SELECTORS['cleanliness_rating_container'])
                    general_container = container.query_selector(AIRBNB_SELECTORS['general_rating_container'])

                    # Verificar elementos esenciales
                    if not all([guest_name_elem, dates_elem, general_container]):
                        self._log_step("⚠️ Faltan elementos esenciales, saltando reseña", "warning")
                        continue

                    guest_name = guest_name_elem.inner_text().strip()
                    dates_text = dates_elem.inner_text().strip()
                    review_text = text_elem.inner_text().strip() if text_elem else ""

                    self._log_step(f"📅 Texto de fechas: '{dates_text}'")
                    check_in_date, check_out_date = self._parse_stay_dates(dates_text)

                    if not check_in_date:
                        self._log_step("❌ No se pudieron parsear las fechas, saltando reseña", "warning")
                        continue

                    review_date = check_out_date or check_in_date
                    self._log_step(f"📅 Fecha de reseña: {review_date}")

                    # VERIFICAR SI DEBEMOS PARAR
                    if self._should_stop_scraping(review_date):
                        should_stop = True
                        break

                    # Extraer ratings
                    general_rating = self._extract_rating(general_container)
                    cleanliness_rating = self._extract_rating(cleanliness_container) if cleanliness_container else "N/A"

                    # VERIFICAR SI ES DUPLICADO
                    is_duplicate = self._is_duplicate_review(guest_name, review_date, review_text)

                    if is_duplicate:
                        self._log_step(
                            f"🔄 Reseña duplicada encontrada, preparando para actualizar: {guest_name} - {review_date}")

                        # Crear objeto Review con todos los datos (para actualización)
                        review = Review(
                            review_date=review_date,
                            check_in_date=check_in_date,
                            platform="Airbnb",
                            rating=general_rating,
                            guest_name=guest_name,
                            floor=self.floor,
                            full_comment=review_text,
                            added_date=date.today(),
                            cleanliness_rating=cleanliness_rating
                        )

                        # Agregar a la lista de actualizaciones
                        self.reviews_to_update.append(review)
                        self._log_step(
                            f"📝 Reseña marcada para actualización: {guest_name} - Limpieza: {cleanliness_rating}")

                    else:
                        # RESEÑA NUEVA
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

                        # Agregar rating de limpieza
                        review.cleanliness_rating = cleanliness_rating

                        self.add_review(review)
                        reviews_count += 1

                        self._log_step(
                            f"✅ Reseña nueva añadida: {guest_name} - {review_date} - General: {general_rating} - Limpieza: {cleanliness_rating}")

                    # Actualizar fechas mínima y máxima
                    if self.min_review_date is None or review_date < self.min_review_date:
                        self.min_review_date = review_date
                    if self.max_review_date is None or review_date > self.max_review_date:
                        self.max_review_date = review_date

                except Exception as e:
                    self._log_step(f"⚠️ Error procesando reseña: {e}", "warning")
                    continue

        except Exception as e:
            self._log_step(f"❌ Error en scrape_reviews_page: {e}", "error")

        self._log_step(
            f"📊 Resumen página: {reviews_count} nuevas, {len(self.reviews_to_update)} para actualizar, debería parar: {should_stop}")
        return reviews_count, should_stop

    def _go_to_next_page(self, page: Page) -> bool:
        try:
            next_button = page.query_selector(AIRBNB_SELECTORS['next_page_button'])
            if next_button:
                is_disabled = next_button.get_attribute('disabled')
                if is_disabled:
                    self._log_step("⏹️ Botón 'Siguiente' está deshabilitado")
                    return False
                else:
                    self._log_step("➡️ Haciendo clic en botón 'Siguiente'")
                    next_button.click()
                    page.wait_for_timeout(3000)

                    # Verificar que la página realmente cambió
                    current_url = page.url
                    self._log_step(f"🔗 Nueva URL: {current_url}")

                    return True
            else:
                self._log_step("❌ No se encontró botón 'Siguiente'")
                return False
        except Exception as e:
            self._log_step(f"❌ Error yendo a página siguiente: {e}", "warning")
            return False

    def scrape(self) -> List[Review]:
        """Scraping con parada inteligente por fecha y detección de duplicados"""
        self._log_step(f"🚀 Iniciando scraping inteligente para piso {self.floor}")
        self._log_step(f"🎯 Rango objetivo: {self.start_date} a {self.end_date}")

        # Inicializar lista de actualizaciones
        self.reviews_to_update = []

        self._load_existing_hashes()

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
                page = context.new_page()

                # Construir URL con filtros
                target_url = self._build_url_with_date_range(
                    self.start_date.strftime("%Y-%m-%d"),
                    self.end_date.strftime("%Y-%m-%d")
                )
                self._log_step(f"🌐 Navegando a: {target_url}")
                page.goto(target_url, wait_until="networkidle")
                page.wait_for_timeout(5000)

                # Scraping con parada inteligente
                total_reviews = 0
                page_number = 1
                should_stop = False

                while not should_stop:
                    self._log_step(f"📖 Procesando página {page_number}")

                    reviews_count, should_stop = self._scrape_reviews_page(page)
                    total_reviews += reviews_count

                    self._log_step(
                        f"📊 Página {page_number}: {reviews_count} nuevas reseñas, {len(self.reviews_to_update)} para actualizar")

                    if should_stop:
                        self._log_step("⏹️ Deteniendo scraping por fecha fuera de rango")
                        break

                    if not self._go_to_next_page(page):
                        self._log_step("⏹️ No hay más páginas")
                        break

                    page_number += 1
                    if page_number > 50:  # Límite de seguridad
                        self._log_step("⚠️ Límite de páginas alcanzado (50)")
                        break

                self._log_step(
                    f"🏁 Scraping completado. Total: {total_reviews} nuevas reseñas, {len(self.reviews_to_update)} para actualizar")

                if self.min_review_date:
                    self._log_step(f"📅 Fecha más antigua encontrada: {self.min_review_date}")
                if self.max_review_date:
                    self._log_step(f"📅 Fecha más reciente encontrada: {self.max_review_date}")

                browser.close()

                # Devolver ambas listas: nuevas reseñas y reseñas para actualizar
                return self.reviews, self.reviews_to_update

            except Exception as e:
                self._log_step(f"❌ Error crítico: {e}", "error")
                try:
                    browser.close()
                except:
                    pass
                raise
