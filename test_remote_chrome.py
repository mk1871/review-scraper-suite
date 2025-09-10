# test_remote_chrome.py

from scrapers.airbnb_scraper import AirbnbScraper

# Usa una URL real de tus pisos
URL_AIRBNB = "https://www.airbnb.es/performance/quality/overall/listing/45969317"  # Cambia por tu URL

if __name__ == "__main__":
    scraper = AirbnbScraper("A1", URL_AIRBNB)
    print("🚀 Iniciando scraper de Airbnb...")
    reviews = scraper.scrape()

    print(f"\n📊 Se obtuvieron {len(reviews)} reseñas:")
    for r in reviews:
        print(f"  - {r.guest_name} ({r.rating}): {r.review_date}")