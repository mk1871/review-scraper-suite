# scrapers/airbnb_scraper.py (SOLUCIÓN DEFINITIVA)

import logging
from datetime import datetime, date
from typing import List

from playwright.sync_api import sync_playwright

from models.review import Review
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str, start_date: str = None, end_date: str = None):
        super().__init__(floor)
        self.url = url
        self.start_date = start_date or "2025-07-01"  # 1 de julio por defecto
        self.end_date = end_date or date.today().strftime("%Y-%m-%d")  # Hoy por defecto

    def _log_step(self, message: str, level: str = "info"):
        """Log un paso del proceso"""
        log_method = getattr(logger, level)
        log_method(f"[{self.floor}] {message}")

    def _calculate_days_from_today(self, target_date: str) -> int:
        """
        Calcula días desde hoy con ajuste de offset de Airbnb (+1 día)
        """
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
        today = date.today()

        # AJUSTE: Airbnb tiene offset de +1 día, restamos 1 para compensar
        delta = (target - today).days - 1  # ← ESTA ES LA LÍNEA CLAVE

        self._log_step(f"Hoy: {today}, Target: {target}, Delta ajustado: {delta}")
        return delta

    # Versión alternativa para mantener el formato exacto:
    def _build_url_with_date_range(self, start_date: str, end_date: str) -> str:
        """
        Construye URL directa a reviews MANTENIENDO formato exacto
        """
        ds_start = self._calculate_days_from_today(start_date)
        ds_end = self._calculate_days_from_today(end_date)

        # URL base manteniendo la estructura completa
        base_url = self.url
        if '/reviews?' not in base_url:
            # Agregar /reviews? si no está presente
            base_url = base_url + '/reviews?'
        else:
            base_url = base_url.split('?')[0] + '?'

        # Agregar parámetros
        new_url = f"{base_url}ds-start={ds_start}&ds-end={ds_end}"

        self._log_step(f"URL final: {new_url}")
        return new_url

    def _extract_visible_dates(self, page):
        """
        Extrae las fechas REALES que muestra Airbnb después de aplicar filtro
        Esto asegura que usamos las fechas correctas (timezone España)
        """
        try:
            # Buscar elementos que muestren el rango de fechas aplicado
            date_elements = page.query_selector_all('[data-testid*="date"]')
            date_texts = []

            for element in date_elements:
                text = element.inner_text().strip()
                if text and any(char.isdigit() for char in text):
                    date_texts.append(text)

            self._log_step(f"Fechas visibles en página: {date_texts}")
            return date_texts

        except Exception as e:
            self._log_step(f"⚠️ Error extrayendo fechas visibles: {e}", "warning")
            return []

    def scrape(self) -> List[Review]:
        """Método principal de scraping"""
        self._log_step(f"Iniciando scraping para: {self.url}")

        with sync_playwright() as p:
            try:
                # INTENTAR CONEXIÓN CON 127.0.0.1 (IPv4)
                debug_url = "http://127.0.0.1:9222"
                self._log_step(f"Conectando a: {debug_url}")

                browser = p.chromium.connect_over_cdp(debug_url)
                context = browser.contexts[0]
                page = context.new_page()

                # ... resto del código igual ...

                # 1. URL DIRECTA A REVIEWS
                target_url = self._build_url_with_date_range(self.start_date, self.end_date)
                self._log_step(f"URL: {target_url}")

                # 2. NAVEGAR
                page.goto(target_url, wait_until="networkidle")
                page.wait_for_timeout(5000)

                # 3. VERIFICAR FECHAS REALES QUE MUESTRA AIRBNB
                visible_dates = self._extract_visible_dates(page)
                self._log_step(f"Fechas mostradas por Airbnb: {visible_dates}")

                # 4. TOMAR SCREENSHOT PARA VERIFICACIÓN VISUAL
                page.screenshot(path=f"verify_{self.floor}.png", full_page=True)
                self._log_step("📸 Screenshot de verificación tomado")

                # 5. EXTRAER REVIEWS (PRÓXIMO PASO)
                # Aquí extraeremos las fechas REALES que muestra cada reseña

                browser.close()
                self._log_step("✅ Proceso completado - Listo para extraer reseñas")
                return self.reviews

            except Exception as e:
                self._log_step(f"❌ Error: {e}", "error")
                try:
                    browser.close()
                except:
                    pass
                raise
