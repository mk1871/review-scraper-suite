# test_remote_chrome.py
from scrapers.airbnb_scraper import AirbnbScraper
from datetime import date
import logging

# Configurar logging para ver más detalles
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Usa una URL real de tus pisos
URL_AIRBNB = "https://www.airbnb.es/performance/quality/overall/listing/45969317"

if __name__ == "__main__":
    # MODIFICAR: Pasar fechas específicas
    scraper = AirbnbScraper(
        floor="FP",
        url=URL_AIRBNB,
        start_date="2025-07-01",  # Fecha inicio
        end_date=date.today().strftime("%Y-%m-%d")  # Fecha fin (hoy)
    )

    print("🚀 Iniciando scraper de Airbnb con URL directa a reviews...")
    print("📊 Cargando hashes existentes de Google Sheets...")

    # FORZAR la carga de hashes existentes
    scraper._load_existing_hashes()

    print(f"📋 {len(scraper.existing_hashes)} hashes existentes cargados")

    reviews = scraper.scrape()

    print(f"\n📊 Proceso completado. Se obtuvieron {len(reviews)} reseñas:")
    for r in reviews:
        print(f"  - {r.guest_name} ({r.rating}): {r.review_date}")

    # Mostrar información de duplicados
    if hasattr(scraper, 'existing_hashes'):
        print(f"\n🔍 Hashes existentes cargados: {len(scraper.existing_hashes)}")
        if scraper.existing_hashes:
            print("   Ejemplos:", list(scraper.existing_hashes)[:3])
