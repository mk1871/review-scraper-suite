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
}

# BOOKING_SELECTORS = {} # Comentado por ahora
