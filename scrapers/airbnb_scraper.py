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
        # SOLO usar nombre, fecha y piso para el hash (el texto varía por idioma)
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
            # DEBUG: Mostrar hashes existentes similares
            similar_hashes = [h for h in self.existing_hashes if h.startswith(review_hash[:5])]
            if similar_hashes:
                self._log_step(f"⏭️ Hashes existentes similares: {similar_hashes}")
        else:
            self._log_step(f"✅ Reseña nueva: {review_hash}")
            # DEBUG: Mostrar por qué no se considera duplicado
            self._log_step(f"✅ Hash no encontrado en {len(self.existing_hashes)} hashes existentes")

        return is_duplicate

    def _parse_stay_dates(self, date_text: str) -> Tuple[Optional[date], Optional[date]]:
        self._log_step(f"Parseando fechas: '{date_text}'")
        try:
            patterns = [
                r'(\d{1,2})[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',
                r'(\d{1,2})\s+(\w+)[–\-](\d{1,2})\s+(\w+)\s+(\d{4})',
                r'(\d{1,2})\s+(\w+)\s+(\d{4})',
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
                    end_month_num = months_es.get(
                        end_month.lower().strip() if 'end_month' in locals() else start_month.lower().strip(), 1)

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
            # DEPURACIÓN: Verificar si los selectores existen en la página
            self._log_step("🔍 Verificando selectores en la página...")

            # Verificar cada selector individualmente
            for selector_name, selector in AIRBNB_SELECTORS.items():
                elements = page.query_selector_all(selector)
                self._log_step(f"Selector '{selector_name}': {len(elements)} elementos encontrados")
                if len(elements) > 0 and len(elements) < 5:  # Mostrar primeros elementos para debug
                    for i, element in enumerate(elements[:3]):
                        try:
                            text = element.inner_text().strip()[:100] + "..." if len(
                                element.inner_text().strip()) > 100 else element.inner_text().strip()
                            self._log_step(f"  Elemento {i}: '{text}'")
                        except:
                            self._log_step(f"  Elemento {i}: [no se pudo obtener texto]")

            review_containers = page.query_selector_all(AIRBNB_SELECTORS['review_container'])
            self._log_step(f"📄 Encontrados {len(review_containers)} contenedores de reseña")

            for i, container in enumerate(review_containers):
                try:
                    self._log_step(f"🔍 Procesando reseña {i + 1}/{len(review_containers)}")

                    # DEPURACIÓN: Verificar qué elementos tiene cada contenedor
                    guest_name_elem = container.query_selector(AIRBNB_SELECTORS['guest_name'])
                    dates_elem = container.query_selector(AIRBNB_SELECTORS['stay_dates'])
                    text_elem = container.query_selector(AIRBNB_SELECTORS['review_text'])

                    # EXTRAER RATINGS CORRECTAMENTE
                    cleanliness_container = container.query_selector(AIRBNB_SELECTORS['cleanliness_rating_container'])
                    general_container = container.query_selector(AIRBNB_SELECTORS['general_rating_container'])

                    # DEPURACIÓN: Mostrar qué elementos se encontraron
                    elements_found = []
                    if guest_name_elem:
                        elements_found.append(f"guest_name: '{guest_name_elem.inner_text().strip()[:50]}...'")
                    else:
                        elements_found.append("guest_name: NO")

                    if dates_elem:
                        elements_found.append(f"dates: '{dates_elem.inner_text().strip()[:50]}...'")
                    else:
                        elements_found.append("dates: NO")

                    if general_container:
                        elements_found.append(f"general_rating: encontrado")
                    else:
                        elements_found.append("general_rating: NO")

                    if cleanliness_container:
                        elements_found.append(f"cleanliness_rating: encontrado")
                    else:
                        elements_found.append("cleanliness_rating: NO")

                    if text_elem:
                        elements_found.append(f"text: '{text_elem.inner_text().strip()[:50]}...'")
                    else:
                        elements_found.append("text: NO")

                    self._log_step(f"📋 Elementos encontrados: {', '.join(elements_found)}")

                    if not all([guest_name_elem, dates_elem, general_container]):
                        self._log_step("⚠️ Faltan elementos esenciales, saltando reseña", "warning")

                        # DEPURACIÓN EXTRA: Ver la estructura HTML del contenedor
                        try:
                            container_html = container.inner_html()[:200] + "..." if len(
                                container.inner_html()) > 200 else container.inner_html()
                            self._log_step(f"🔍 HTML del contenedor: {container_html}")
                        except:
                            self._log_step("❌ No se pudo obtener HTML del contenedor")

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

                    # VERIFICAR DUPLICADOS
                    if self._is_duplicate_review(guest_name, review_date, review_text):
                        continue

                    # EXTRAER RATINGS
                    general_rating = self._extract_rating(general_container)
                    cleanliness_rating = self._extract_rating(cleanliness_container) if cleanliness_container else "N/A"

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

                    # Agregar rating de limpieza como atributo adicional
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

        self._log_step(f"📊 Resumen página: {reviews_count} nuevas, debería parar: {should_stop}")
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
        self._log_step(f"🚀 Iniciando scraping inteligente para piso {self.floor}")
        self._log_step(f"🎯 Rango objetivo: {self.start_date} a {self.end_date}")

        self._load_existing_hashes()
        self._log_step(f"📊 {len(self.existing_hashes)} hashes existentes cargados")

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                context = browser.contexts[0]
                page = context.new_page()

                target_url = self._build_url_with_date_range(
                    self.start_date.strftime("%Y-%m-%d"),
                    self.end_date.strftime("%Y-%m-%d")
                )
                self._log_step(f"🌐 Navegando a: {target_url}")
                page.goto(target_url, wait_until="networkidle")
                page.wait_for_timeout(5000)

                total_reviews = 0
                page_number = 1
                should_stop = False

                while not should_stop:
                    self._log_step(f"📖 Procesando página {page_number}")

                    reviews_count, should_stop = self._scrape_reviews_page(page)
                    total_reviews += reviews_count

                    self._log_step(f"📊 Página {page_number}: {reviews_count} nuevas reseñas")

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

                self._log_step(f"🏁 Scraping completado. Total: {total_reviews} nuevas reseñas")
                if self.min_review_date:
                    self._log_step(f"📅 Fecha más antigua encontrada: {self.min_review_date}")
                if self.max_review_date:
                    self._log_step(f"📅 Fecha más reciente encontrada: {self.max_review_date}")

                browser.close()
                return self.reviews

            except Exception as e:
                self._log_step(f"❌ Error crítico: {e}", "error")
                try:
                    browser.close()
                except:
                    pass
                raise
