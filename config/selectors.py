# config/selectors.py

AIRBNB_SELECTORS = {
    # Selectores principales para los campos de texto (BASADOS EN TU HTML)
    'start_date_input': 'input#startDate',
    'end_date_input': 'input#endDate',

    # Selectores alternativos (por data-testid)
    'start_date_input_alt': 'input[data-testid="input"][id="startDate"]',
    'end_date_input_alt': 'input[data-testid="input"][id="endDate"]',

    # Botón aplicar - selector principal y alternativos
    'apply_button': 'button[data-testid="dsDropdownApply"]',
    'apply_button_alt': 'button:has-text("Aplicar"), button:has-text("Apply")',

    # Contenedor del filtro de fechas (para abrirlo)
    'date_filter_container': 'div[data-testid="dsSelector"]',
    'date_filter_button': 'div[data-testid="dsSelector"] button',

    # Selectores del calendario (como respaldo)
    'calendar_container': 'div[data-testid="dsDropdown"]',
    'calendar_day_button': 'div[data-testid="datepicker-day-{date}"]',
    'calendar_next_button': 'button[aria-label="Siguiente"]',
    'calendar_prev_button': 'button[aria-label="Anterior"]',

    # NUEVOS SELECTORES PARA REVIEWS
    'review_container': 'div._i3snph',  # Contenedor de cada reseña
    'guest_name': 'div._gt7myn',  # Nombre del huésped
    'stay_dates': 'div._1w3y9kg',  # Fechas de estadía
    'cleanliness_rating': 'div._1m338bm6 + span[aria-label*="Valoración"]',  # Rating limpieza
    'general_rating': 'div._8vya27 + span[aria-label*="Valoración"]',  # Rating general
    'review_text': 'div._1umquac',  # Texto de la reseña
    'pagination_container': 'div.p1j2gy66',  # Contenedor de paginación
    'next_page_button': 'button[aria-label="Página siguiente"]',  # Botón siguiente
    'current_page_info': 'div._1j4qd3l',  # "Mostrando X de Y"
}

# BOOKING_SELECTORS = {} # Comentado por ahora
