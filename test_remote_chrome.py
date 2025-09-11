from scrapers.airbnb_scraper import AirbnbScraper
from datetime import date
import logging
from utils.gsheet_utils import setup_gspread, append_review_to_sheet, update_existing_review

# Configurar logging para ver más detalles
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Usa una URL real de tus pisos
URL_AIRBNB = "https://www.airbnb.es/performance/quality/overall/listing/48263202"

if __name__ == "__main__":
    # MODIFICAR: Pasar fechas específicas
    scraper = AirbnbScraper(
        floor="GB28",
        url=URL_AIRBNB,
        start_date="2025-07-01",  # Fecha inicio
        end_date=date.today().strftime("%Y-%m-%d")  # Fecha fin (hoy)
    )

    print("🚀 Iniciando scraper de Airbnb con URL directa a reviews...")
    print("📊 Cargando hashes existentes de Google Sheets...")

    # FORZAR la carga de hashes existentes
    scraper._load_existing_hashes()

    print(f"📋 {len(scraper.existing_hashes)} hashes existentes cargados")

    # Ejecutar scraping (ahora devuelve dos valores)
    reviews, reviews_to_update = scraper.scrape()

    print(f"\n📊 Proceso completado.")
    print(f"   ✅ {len(reviews)} reseñas NUEVAS")
    print(f"   🔄 {len(reviews_to_update)} reseñas para ACTUALIZAR")

    # Mostrar nuevas reseñas
    if reviews:
        print("\n📍 RESEÑAS NUEVAS:")
        for r in reviews:
            print(f"   - {r.guest_name} ({r.rating}): {r.review_date} - Limpieza: {r.cleanliness_rating}")

    # Mostrar reseñas para actualizar
    if reviews_to_update:
        print("\n📍 RESEÑAS PARA ACTUALIZAR:")
        for r in reviews_to_update:
            print(f"   - {r.guest_name} ({r.rating}): {r.review_date} - Limpieza: {r.cleanliness_rating}")

    # Opcional: Exportar a Google Sheets
    export = input("\n¿Exportar a Google Sheets? (s/n): ")
    if export.lower() == 's':
        try:
            sheet = setup_gspread()
            print("✅ Conectado a Google Sheets")

            # Agregar nuevas reseñas
            new_count = 0
            for review in reviews:
                if append_review_to_sheet(sheet, review):
                    new_count += 1

            # Actualizar reseñas existentes
            update_count = 0
            for review in reviews_to_update:
                if update_existing_review(sheet, review):
                    update_count += 1

            print(f"✅ Exportadas {new_count} nuevas y actualizadas {update_count} reseñas")

        except Exception as e:
            print(f"❌ Error exportando: {e}")

    print("\n🔍 Hashes existentes cargados:", len(scraper.existing_hashes))
    if scraper.existing_hashes:
        print("   Ejemplos:", list(scraper.existing_hashes)[:3])
