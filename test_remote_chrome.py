# test_remote_chrome.py
# -*- coding: utf-8 -*-
import logging
from datetime import date

from utils.logging_setup import configure_logging
from scrapers.airbnb_scraper import AirbnbScraper


def main():
    # Consola limpia, DEBUG al archivo, HTTP ruidoso en WARNING
    configure_logging(
        console_level="INFO",
        file_level="DEBUG",
        http_level="WARNING",
        log_file="logs/scraper.log",
    )
    logger = logging.getLogger(__name__)

    logger.info("🚀 Iniciando scraper de Airbnb con URL directa a reviews...")

    # Ejemplo: ajuste rápido para probar un piso concreto
    piso = "GF2"  # <-- cambia según tu CSV o test
    url = "https://www.airbnb.es/performance/quality/overall/listing/970291990719745713"  # <-- URL reviews/overall

    scraper = AirbnbScraper(
        floor=piso,
        url=url,
        start_date="2025-07-01",
        end_date=date.today().strftime("%Y-%m-%d"),
    )

    new_reviews, to_update = scraper.scrape()

    logger.info("\n📊 Proceso completado.\n   ✅ %d reseñas NUEVAS\n   🔄 %d reseñas para ACTUALIZAR",
                len(new_reviews), len(to_update))

    if to_update:
        logger.info("\n📍 RESEÑAS PARA ACTUALIZAR:")
        for r in to_update:
            logger.info("   - %s (%s): %s - Limpieza: %s",
                        r.guest_name, r.rating, r.review_date, r.cleanliness_rating)


if __name__ == "__main__":
    raise SystemExit(main())
