import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Optional, Set
from datetime import datetime
import logging
import hashlib

# Asegurar esta importación
from models.review import Review

logger = logging.getLogger(__name__)


def setup_gspread(credentials_file: str = "config/credentials.json", sheet_name: str = "Todas") -> gspread.Worksheet:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

    SPREADSHEET_ID = "1vYfIeIkR3NYw5DwJ8dnoTfKvEI8_sXt0Uk9eF4BvzyY"
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    return sheet


def get_existing_reviews_hashes(floor: str) -> Set[str]:
    try:
        sheet = setup_gspread()
        records = sheet.get_all_records()

        existing_hashes = set()
        for record in records:
            if record['Piso'] == floor:
                guest_name = record['Nombre Huésped']
                review_date_str = record['Fecha Reseña']
                review_text = record['Comentario Completo'][:100]

                try:
                    review_date = datetime.strptime(review_date_str, '%Y-%m-%d').date()
                    date_formatted = review_date.strftime('%Y%m%d')
                except:
                    date_formatted = review_date_str.replace('-', '')

                unique_string = f"{guest_name}_{date_formatted}_{floor}_{review_text}"
                review_hash = hashlib.md5(unique_string.encode()).hexdigest()
                existing_hashes.add(review_hash)

                # Log para debugging
                logger.debug(f"Hash existente: {review_hash} - {guest_name} - {review_date_str}")

        logger.info(f"Se cargaron {len(existing_hashes)} hashes existentes para el piso {floor}")
        return existing_hashes

    except Exception as e:
        logger.error(f"Error obteniendo hashes existentes: {e}")
        return set()


def append_review_to_sheet(sheet: gspread.Worksheet, review: Review) -> bool:
    try:
        row = review.to_dict()
        if hasattr(review, 'cleanliness_rating'):
            row['V Limpieza'] = review.cleanliness_rating
        else:
            row['V Limpieza'] = ''

        sheet.append_row(list(row.values()))
        logger.info(f"Se agregó nueva reseña: {review.guest_name} - {review.platform}")
        return True
    except Exception as e:
        logger.error(f"Error al agregar reseña: {e}")
        return False
