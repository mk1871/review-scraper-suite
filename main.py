# main.py (nuevo archivo principal)
import logging
from typing import List

import pandas as pd

from config.settings import BASE_DIR
from models.review import Review
from scrapers.airbnb_scraper import AirbnbScraper
from utils.error_handling import handle_scraper_errors
from utils.gsheet_utils import setup_gspread, append_review_to_sheet

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@handle_scraper_errors
def load_pisos_from_csv() -> pd.DataFrame:
    """Carga la lista de pisos desde el archivo CSV"""
    csv_path = BASE_DIR / "pisos.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Archivo {csv_path} no encontrado")

    df = pd.read_csv(csv_path)
    logger.info(f"Cargados {len(df)} pisos desde CSV")
    return df


@handle_scraper_errors
def scrape_airbnb_reviews() -> List[Review]:
    """Ejecuta el scraping para todos los pisos de Airbnb"""
    all_reviews = []

    try:
        df = load_pisos_from_csv()

        for _, row in df.iterrows():
            piso = row['piso']
            url = row['url']

            logger.info(f"Scrapeando piso: {piso}")

            scraper = AirbnbScraper(piso, url)
            reviews = scraper.scrape()
            all_reviews.extend(reviews)

            logger.info(f"Obtenidas {len(reviews)} reseñas para {piso}")

    except Exception as e:
        logger.error(f"Error durante el scraping: {e}")
        raise

    return all_reviews


@handle_scraper_errors
def export_to_google_sheets(reviews: List[Review]):
    """Exporta las reseñas a Google Sheets"""
    if not reviews:
        logger.warning("No hay reseñas para exportar")
        return

    try:
        sheet = setup_gspread()
        logger.info("✅ Conectado a Google Sheets")

        success_count = 0
        for review in reviews:
            if append_review_to_sheet(sheet, review):
                success_count += 1

        logger.info(f"✅ Exportadas {success_count}/{len(reviews)} reseñas a Google Sheets")

    except Exception as e:
        logger.error(f"❌ Error exportando a Google Sheets: {e}")
        raise


def main():
    """Función principal"""
    logger.info("🚀 Iniciando proceso de scraping")

    try:
        # 1. Scrapear reseñas
        reviews = scrape_airbnb_reviews()

        # 2. Exportar a Google Sheets
        if reviews:
            export_to_google_sheets(reviews)
        else:
            logger.info("No se encontraron reseñas nuevas")

        logger.info("🏁 Proceso completado exitosamente")

    except Exception as e:
        logger.error(f"❌ Error fatal en el proceso: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
