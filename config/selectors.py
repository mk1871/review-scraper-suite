# config/selectors.py

AIRBNB_SELECTORS = {
    # ... (selectores existentes) ...

    # Selectores para el filtro de fechas
    'date_filter_container': 'div[data-testid="dsSelector"]',
    'date_filter_button': 'div[data-testid="dsSelector"] button',

    # Selectores del calendario (campos de texto - como respaldo o si se arregla)
    'start_date_input': 'input#startDate',
    'end_date_input': 'input#endDate',
    'apply_button': 'button[data-testid="dsDropdownApply"]',

    # Nuevos selectores para interacción con el calendario
    'calendar_container': 'div[data-testid="dsDropdown"]',  # El contenedor principal del calendario
    'calendar_month_container': 'div._1foj6yps',  # Contiene los meses visibles
    'calendar_visible_month': 'div._1svux14[data-visible="true"]',  # Un mes visible
    'calendar_month_title': 'div._18c3hp2',  # Título del mes (ej: "julio de 2025")
    'calendar_prev_button': 'button[aria-label="Anterior"]',  # Flecha mes anterior
    'calendar_next_button': 'button[aria-label="Siguiente"]',  # Flecha mes siguiente
    'calendar_day_button': 'div[data-testid="datepicker-day-{date}"]',
    # Selector base para un día específico, {date} será reemplazado por YYYY-MM-DD
}

# BOOKING_SELECTORS = {} # Comentado por ahora
