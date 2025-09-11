from datetime import date

from scrapers.airbnb_scraper import AirbnbScraper

# Usa una URL real de tus pisos
URL_AIRBNB = "https://www.airbnb.es/performance/quality/overall/listing/45969317"

if __name__ == "__main__":
    # Probar con fechas específicas (1 julio hasta hoy)
    scraper = AirbnbScraper("A1", URL_AIRBNB, "2025-07-01", date.today().strftime("%Y-%m-%d"))
    print("🚀 Iniciando scraper de Airbnb con URL directa a reviews...")
    reviews = scraper.scrape()

    print(f"\n📊 Proceso completado. Se obtuvieron {len(reviews)} reseñas:")
    for r in reviews:
        print(f"  - {r.guest_name} ({r.rating}): {r.review_date}")
