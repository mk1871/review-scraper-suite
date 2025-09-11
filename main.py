# main.py
import logging
from typing import List, Tuple
from datetime import date
import pandas as pd

from config.settings import BASE_DIR
from models.review import Review
from scrapers.airbnb_scraper import AirbnbScraper
from utils.error_handling import handle_scraper_errors
from utils.gsheet_utils import setup_gspread, append_review_to_sheet, update_existing_review
from utils.logging_setup import configure_logging  # ← NUEVO

# Configura: consola=INFO (hitos), archivo=DEBUG (detalles), HTTP ruidoso=WARNING
configure_logging(
    console_level="INFO",
    file_level="DEBUG",
    http_level="WARNING",
    log_file="logs/scraper.log",
)
logger = logging.getLogger(__name__)


@handle_scraper_errors
def load_pisos_from_csv() -> pd.DataFrame:
    csv_path = BASE_DIR / "pisos.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Archivo {csv_path} no encontrado")
    df = pd.read_csv(csv_path)
    logger.info(f"Cargados {len(df)} pisos desde CSV")
    return df


@handle_scraper_errors
def scrape_airbnb_reviews() -> Tuple[List[Review], List[Review]]:
    """Scrapea TODOS los pisos Airbnb y acumula (nuevas, para_actualizar)."""
    all_new: List[Review] = []
    all_updates: List[Review] = []

    df = load_pisos_from_csv()
    for _, row in df.iterrows():
        piso = row['piso']
        url = row['url']
        logger.info(f"Scrapeando piso: {piso}")

        scraper = AirbnbScraper(
            floor=piso,
            url=url,
            start_date="2025-07-01",
            end_date=date.today().strftime("%Y-%m-%d")
        )
        new_reviews, to_update = scraper.scrape()
        all_new.extend(new_reviews)
        all_updates.extend(to_update)

        logger.info(f"{piso}: nuevas={len(new_reviews)}, actualizar={len(to_update)}")

    return all_new, all_updates


@handle_scraper_errors
def export_to_google_sheets(reviews: List[Review], reviews_to_update: List[Review]):
    sheet = setup_gspread()
    logger.info("✅ Conectado a Google Sheets")

    new_ok = 0
    upd_ok = 0

    for r in reviews:
        if append_review_to_sheet(sheet, r):
            new_ok += 1

    for r in reviews_to_update:
        if update_existing_review(sheet, r):
            upd_ok += 1

    logger.info(f"✅ Exportadas {new_ok} nuevas y actualizadas {upd_ok} reseñas")


def main():
    logger.info("🚀 Iniciando proceso de scraping")
    try:
        new_reviews, updates = scrape_airbnb_reviews()
        if new_reviews or updates:
            export_to_google_sheets(new_reviews, updates)
        else:
            logger.info("No se encontraron reseñas nuevas ni por actualizar")
        logger.info("🏁 Proceso completado exitosamente")
        return 0
    except Exception as e:
        logger.error(f"❌ Error fatal en el proceso: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
