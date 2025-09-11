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

                try:
                    review_date = datetime.strptime(review_date_str, '%Y-%m-%d').date()
                    date_formatted = review_date.strftime('%Y%m%d')
                except:
                    date_formatted = review_date_str.replace('-', '')

                # SOLO nombre, fecha y piso (sin texto por problemas de idioma)
                unique_string = f"{guest_name}_{date_formatted}_{floor}"
                review_hash = hashlib.md5(unique_string.encode()).hexdigest()
                existing_hashes.add(review_hash)

                if len(existing_hashes) < 5:  # Mostrar primeros 5 para debug
                    print(f"   📝 {guest_name} - {review_date_str} -> {review_hash}")

        print(f"✅ {len(existing_hashes)} hashes generados para piso {floor}")
        return existing_hashes

    except Exception as e:
        print(f"❌ Error conectando a Google Sheets: {e}")
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


def update_existing_review(sheet: gspread.Worksheet, review: Review) -> bool:
    """Actualiza una reseña existente con el rating de limpieza"""
    try:
        # Buscar la reseña por nombre, fecha y piso
        records = sheet.get_all_records()

        for i, record in enumerate(records, start=2):  # start=2 porque la fila 1 son headers
            if (record['Nombre Huésped'] == review.guest_name and
                    record['Fecha Reseña'] == review.review_date.strftime('%Y-%m-%d') and
                    record['Piso'] == review.floor):
                # Actualizar solo el rating de limpieza (columna L = 12)
                sheet.update_cell(i, 12, review.cleanliness_rating or "")
                logger.info(
                    f"✅ Actualizada reseña: {review.guest_name} - {review.review_date} - Limpieza: {review.cleanliness_rating}")
                return True

        logger.warning(f"⚠️ No se encontró reseña para actualizar: {review.guest_name} - {review.review_date}")
        return False

    except Exception as e:
        logger.error(f"❌ Error actualizando reseña: {e}")
        return False
