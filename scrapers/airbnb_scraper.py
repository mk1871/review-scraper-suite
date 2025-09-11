# scrapers/airbnb_scraper.py

import logging
from typing import List

from playwright.sync_api import sync_playwright, TimeoutError

from config.selectors import AIRBNB_SELECTORS
from models.review import Review
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class AirbnbScraper(BaseScraper):
    def __init__(self, floor: str, url: str):
        super().__init__(floor)
        self.url = url

    def _log_step(self, message: str):
        """Imprime un mensaje de paso para mejor seguimiento en terminal."""
        print(f"  → {message}")

    def _open_date_filter(self, page):
        """Abre el panel de filtro de fechas."""
        self._log_step("Buscando selector de fechas...")
        try:
            # Espera a que el contenedor del selector esté disponible
            date_selector_container = page.wait_for_selector(
                AIRBNB_SELECTORS['date_filter_container'],
                timeout=15000  # Aumento ligero del timeout
            )
            self._log_step("Selector de fechas encontrado.")

            # Busca el botón dentro del contenedor usando el selector más específico
            filter_button = date_selector_container.query_selector(
                'button'  # El botón es un hijo directo del contenedor
            )
            if filter_button:
                self._log_step("Haciendo clic en el botón del selector de fechas...")
                filter_button.click()
                self._log_step("Clic realizado. Panel de fechas debería estar abierto.")
                # Pequeña pausa para que el panel se abra completamente
                page.wait_for_timeout(2000)
            else:
                self._log_step("❌ No se encontró el botón dentro del selector de fechas.")
                raise Exception("Botón del filtro de fechas no encontrado")

        except TimeoutError:
            self._log_step("❌ Timeout: No se encontró el selector de fechas.")
            raise
        except Exception as e:
            self._log_step(f"❌ Error al intentar abrir el filtro de fechas: {e}")
            raise

    def _navigate_to_month(self, page, target_month_year: str):
        """
        Navega por el calendario hasta encontrar el mes objetivo.
        target_month_year: Texto como "julio de 2025" que aparece en el título del mes.
        """
        self._log_step(f"Navegando al mes: {target_month_year}")
        max_attempts = 24  # Evitar bucle infinito
        attempts = 0

        while attempts < max_attempts:
            try:
                # Esperar a que los meses visibles se carguen
                page.wait_for_selector(AIRBNB_SELECTORS['calendar_visible_month'], timeout=5000)

                # Buscar si el mes objetivo está visible
                visible_months = page.query_selector_all(AIRBNB_SELECTORS['calendar_visible_month'])
                found = False
                for month_div in visible_months:
                    title_element = month_div.query_selector(AIRBNB_SELECTORS['calendar_month_title'])
                    if title_element and target_month_year.lower() in title_element.inner_text().lower():
                        self._log_step(f"Mes objetivo '{target_month_year}' encontrado.")
                        return True  # Mes encontrado

                # Si no se encontró, hacer clic en "Siguiente"
                # (Asumimos que normalmente queremos fechas futuras, si no, se puede ajustar)
                next_button = page.wait_for_selector(AIRBNB_SELECTORS['calendar_next_button'], timeout=2000)
                if next_button:
                    self._log_step("Haciendo clic en flecha 'Siguiente'...")
                    next_button.click()
                    page.wait_for_timeout(1000)  # Pausa para que cargue el nuevo mes
                else:
                    self._log_step("❌ Botón 'Siguiente' no encontrado.")
                    return False

            except Exception as e:
                self._log_step(f"⚠️ Error al navegar a {target_month_year}: {e}")
                # Intentar continuar
                pass

            attempts += 1

        self._log_step(f"❌ No se pudo encontrar el mes '{target_month_year}' después de {max_attempts} intentos.")
        return False

    def _select_date_from_calendar(self, page, date_str: str):
        """
        Selecciona una fecha específica del calendario.
        date_str: Fecha en formato YYYY-MM-DD (ej: "2025-07-01").
        """
        self._log_step(f"Seleccionando fecha del calendario: {date_str}")
        try:
            # Formato del selector para el día específico
            day_selector = AIRBNB_SELECTORS['calendar_day_button'].format(date=date_str)

            # Esperar a que el día esté disponible y hacer clic
            day_button = page.wait_for_selector(day_selector, timeout=10000)
            if day_button:
                # Verificar si está deshabilitado (aunque wait_for_selector debería esperar uno habilitado)
                # aria-disabled="true" o similar podría estar presente
                is_disabled = day_button.get_attribute("aria-disabled") == "true"
                if is_disabled:
                    self._log_step(f"❌ La fecha {date_str} está deshabilitada.")
                    return False

                day_button.click()
                self._log_step(f"✅ Fecha {date_str} seleccionada.")
                return True
            else:
                self._log_step(f"❌ No se encontró el botón para la fecha {date_str}.")
                return False
        except TimeoutError:
            self._log_step(f"❌ Timeout al esperar la fecha {date_str} en el calendario.")
            return False
        except Exception as e:
            self._log_step(f"❌ Error al seleccionar la fecha {date_str}: {e}")
            return False

    def _set_date_range(self, page, start_date_iso: str, end_date_iso: str):
        """
        Establece el rango de fechas seleccionando en el calendario.
        start_date_iso: Fecha de inicio en formato YYYY-MM-DD (ej: "2025-07-01").
        end_date_iso: Fecha de fin en formato YYYY-MM-DD (ej: "2025-09-10").
        """
        # Convertir fechas ISO a nombres de meses en español para Airbnb
        # Esta es una forma básica, se podría mejorar usando `locale` o un diccionario
        meses_es = {
            "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
            "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
            "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
        }

        try:
            start_year, start_month, start_day = start_date_iso.split("-")
            end_year, end_month, end_day = end_date_iso.split("-")

            start_month_name = meses_es.get(start_month, "julio")  # Por defecto julio si falla
            end_month_name = meses_es.get(end_month, "septiembre")  # Por defecto septiembre

            start_month_year_text = f"{start_month_name} de {start_year}"
            end_month_year_text = f"{end_month_name} de {end_year}"

            self._log_step(
                f"Estableciendo rango de fechas mediante calendario: {start_date_iso} ({start_month_year_text}) → {end_date_iso} ({end_month_year_text})")

            # 1. Navegar al mes de inicio
            if not self._navigate_to_month(page, start_month_year_text):
                raise Exception(f"No se pudo navegar al mes de inicio: {start_month_year_text}")

            # 2. Seleccionar la fecha de inicio
            if not self._select_date_from_calendar(page, start_date_iso):
                raise Exception(f"No se pudo seleccionar la fecha de inicio: {start_date_iso}")

            # 3. Seleccionar la fecha de fin (se asume que el mes está visible o se puede navegar)
            # El calendario podría haberse movido, pero normalmente muestra varios meses.
            # Si el mes de fin no está visible, necesitamos navegar.
            # Para simplificar, asumiremos que está visible o haremos una navegación adicional.

            # Verificar si el mes de fin está visible
            visible_months_after_start = page.query_selector_all(AIRBNB_SELECTORS['calendar_visible_month'])
            end_month_found = False
            for month_div in visible_months_after_start:
                title_element = month_div.query_selector(AIRBNB_SELECTORS['calendar_month_title'])
                if title_element and end_month_year_text.lower() in title_element.inner_text().lower():
                    end_month_found = True
                    break

            # Si no está visible, navegar hasta él
            if not end_month_found:
                if not self._navigate_to_month(page, end_month_year_text):
                    # Si falla la navegación directa, intentar navegar paso a paso
                    # (Este es un enfoque básico, podría mejorarse)
                    self._log_step(f"Intentando navegación paso a paso para llegar a {end_month_year_text}...")
                    # Esto es complejo sin saber cuántos meses hay entre inicio y fin.
                    # Por ahora, lanzamos un error si no se encuentra después de navegar.
                    raise Exception(f"No se pudo navegar al mes de fin: {end_month_year_text}")

            # 4. Seleccionar la fecha de fin
            if not self._select_date_from_calendar(page, end_date_iso):
                raise Exception(f"No se pudo seleccionar la fecha de fin: {end_date_iso}")

            self._log_step("✅ Rango de fechas establecido correctamente mediante calendario.")

            # --- Pausa breve antes de aplicar ---
            self._log_step("⏳ Pausando 2 segundos antes de aplicar el filtro...")
            page.wait_for_timeout(2000)  # 2 segundos
            # --- FIN NUEVO ---

        except Exception as e:
            self._log_step(f"❌ Error al establecer el rango de fechas mediante calendario: {e}")
            raise  # Re-lanzar para que el error se maneje en scrape

    def _apply_filter(self, page):
        """
        Haz clic en el botón "Aplicar".
        Basado en el HTML: button[data-testid="dsDropdownApply"]
        """
        self._log_step("Buscando botón 'Aplicar'...")
        try:
            apply_button = page.wait_for_selector(AIRBNB_SELECTORS['apply_button'], timeout=10000)
            self._log_step("Botón 'Aplicar' encontrado.")
            self._log_step("Haciendo clic en 'Aplicar'...")
            apply_button.click()
            self._log_step("✅ Filtro aplicado. Esperando a que cargue el contenido...")
            # Esperar a que algo indique que el contenido se ha actualizado
            # Esto puede ser específico a la página, por ahora una pausa genérica
            page.wait_for_timeout(5000)  # Ajustar según la velocidad de carga
        except TimeoutError:
            self._log_step("❌ Timeout: No se encontró el botón 'Aplicar'.")
            raise
        except Exception as e:
            self._log_step(f"❌ Error al aplicar el filtro: {e}")
            raise

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

                # --- Proceso de filtro de fechas ---
                print("\n--- Iniciando proceso de filtro de fechas ---")
                self._open_date_filter(page)

                # Establecer rango de fechas específico
                self._set_date_range(page, "2025-07-01", "2025-09-10")

                # Aplicar filtro
                self._apply_filter(page)
                print("--- Finalizado proceso de filtro de fechas ---\n")

                # --- Aquí iría el scraping de las reseñas ---
                # ... (código para extraer reseñas) ...

                browser.close()
                print("✅ Proceso de scraping (filtro de fechas) completado.")
                return self.reviews  # Devuelve lista vacía por ahora

            except Exception as e:
                logger.error(f"❌ Error crítico en el proceso de scraping: {e}")
                # Intentar cerrar el navegador si está abierto
                try:
                    browser.close()
                except:
                    pass  # Ignorar errores al cerrar
                raise  # Re-lanzar la excepción para que se maneje arriba
