# utils/gsheet_utils.py

import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from models.review import Review

logger = logging.getLogger(__name__)


def setup_gspread(credentials_file: str = "config/credentials.json", sheet_name: str = "Todas") -> gspread.Worksheet:
    """
    Autentica y devuelve la hoja 'Todas' del documento de Google Sheets.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

    # Reemplaza con el ID real de tu documento
    SPREADSHEET_ID = "1vYfIeIkR3NYw5DwJ8dnoTfKvEI8_sXt0Uk9eF4BvzyY"
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    return sheet


def append_review_to_sheet(sheet: gspread.Worksheet, review: Review) -> bool:
    """
    Agrega una nueva reseña a la hoja.
    """
    try:
        row_data = review.to_dict()
        # Agregar campo de limpieza si existe
        if hasattr(review, 'cleanliness_rating'):
            row_data['V Limpieza'] = review.cleanliness_rating
        else:
            row_data['V Limpieza'] = ''

        sheet.append_row(list(row_data.values()))
        return True
    except Exception as e:
        logger.error(f"Error al agregar reseña: {e}")
        return False
