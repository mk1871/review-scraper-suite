# config/selectors.py

# Airbnb (por ahora solo este)
AIRBNB_SELECTORS = {

    # Selectores para fechas
    'date_filter_container': 'div[data-testid="dsSelector"]',
    'date_filter_button': 'div[data-testid="dsSelector"] button',

    'reviews_container': 'div[data-testid="reviews-container"]',
    'review_items': 'div[data-testid="review-card"]',
    'review_date': 'div[data-testid="review-date"]',
    'check_in_date': 'div[data-testid="check-in-date"]',
    'rating': 'div[data-testid="review-rating"] span',  # Ajustar según estructura real
    'guest_name': 'div[data-testid="reviewer-name"]',
    'full_comment': 'div[data-testid="review-text"]',
    'complaints': 'div[data-testid="review-pros-cons"] div:nth-child(2)',  # Ajustar si es necesario
    'suggestions': 'div[data-testid="review-pros-cons"] div:nth-child(1)'  # Ajustar si es necesario
}

# Deja BOOKING_SELECTORS comentado o vacío por ahora
# BOOKING_SELECTORS = {}
