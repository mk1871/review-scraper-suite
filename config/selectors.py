AIRBNB_SELECTORS = {
    # Selectores principales para los campos de texto
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

    # SELECTORES CORREGIDOS PARA REVIEWS:
    'review_container': 'div._i3snph',  # ✅ Correcto
    'guest_name': 'div._gt7myn',  # ✅ Correcto
    'stay_dates': 'div._1w3y9kg',  # ✅ Correcto
    'review_text': 'div._1umquac',  # ✅ Correcto

    # SELECTORES NUEVOS PARA RATINGS (basados en tu HTML):
    'cleanliness_rating_container': 'div._5kaapu:has(div._1m338bm6)',  # Contenedor de rating limpieza
    'general_rating_container': 'div._1uuujzfx:has(div._8vya27)',  # Contenedor de rating general

    # Selectores para extraer el valor numérico del rating:
    'rating_value': 'span[aria-label*="Valoración"]',  # Elemento que contiene el rating
    'rating_stars': 'span[aria-hidden="true"]',  # Elemento con el número

    'pagination_container': 'div.p1j2gy66',
    'next_page_button': 'button[aria-label="Página siguiente"]',
    'current_page_info': 'div._1j4qd3l',
}
