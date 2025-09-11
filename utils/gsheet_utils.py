# utils/gsheet_utils.py
# -*- coding: utf-8 -*-
import logging
import hashlib
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from models.review import Review
from utils.text_utils import clean_text

logger = logging.getLogger(__name__)


def setup_gspread(credentials_file: str = "config/credentials.json", sheet_name: str = "Todas") -> gspread.Worksheet:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)

    SPREADSHEET_ID = "1vYfIeIkR3NYw5DwJ8dnoTfKvEI8_sXt0Uk9eF4BvzyY"
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    return sheet


def get_existing_reviews_hashes(floor: str):
    """Hash estable por (Nombre, Fecha Reseña, Piso)."""
    try:
        sheet = setup_gspread()
        records = sheet.get_all_records()
        existing_hashes = set()

        for record in records:
            if record.get('Piso') == floor:
                guest_name = clean_text(record.get('Nombre Huésped', ''))
                review_date_str = clean_text(record.get('Fecha Reseña', ''))

                # Normaliza la fecha a yyyymmdd cuando sea posible
                try:
                    review_date = datetime.strptime(review_date_str, '%Y-%m-%d').date()
                    date_formatted = review_date.strftime('%Y%m%d')
                except Exception:
                    date_formatted = review_date_str.replace('-', '')

                unique_string = f"{guest_name}_{date_formatted}_{floor}"
                review_hash = hashlib.md5(unique_string.encode()).hexdigest()
                existing_hashes.add(review_hash)

                if len(existing_hashes) < 5:
                    print(f"   📝 {guest_name} - {review_date_str} -> {review_hash}")

        print(f"✅ {len(existing_hashes)} hashes generados para piso {floor}")
        return existing_hashes

    except Exception as e:
        print(f"❌ Error conectando a Google Sheets: {e}")
        return set()


# Orden exacto de columnas en la hoja "Todas".
_HEADERS = [
    "Fecha Reseña",
    "Fecha Ingreso",
    "Plataforma",
    "Valoración",
    "Nombre Huésped",
    "Piso",
    "Resumen Quejas",
    "Sugerencias",
    "Plan Acción",
    "Comentario Completo",
    "Fecha Añadida",
    "V Limpieza",
]


def _row_from_review(review: Review):
    """Construye una fila con strings limpios (valoraciones siempre como TEXTO)."""
    d = review.to_dict()

    # Limpieza general de strings (evita comillas invisibles o iniciales)
    for k in list(d.keys()):
        if isinstance(d[k], str):
            d[k] = clean_text(d[k])

    # Asegurar que las valoraciones queden como TEXTO
    # - d["Valoración"] ya viene con "5*", "4*", etc.
    # - d["V Limpieza"] puede venir vacío o "5*", "4*", etc.
    d["Valoración"] = clean_text(d.get("Valoración", ""))
    d["V Limpieza"] = clean_text(d.get("V Limpieza", ""))

    # Ensamblar en el orden exacto de la hoja
    return [d.get(h, "") for h in _HEADERS]


def append_review_to_sheet(sheet: gspread.Worksheet, review: Review) -> bool:
    """
    Inserta una NUEVA reseña.
    Usamos USER_ENTERED para que las fechas se escriban bien; las valoraciones contienen un asterisco,
    por lo que Google Sheets las mantiene como TEXTO (no las convierte a número).
    """
    try:
        values = [_row_from_review(review)]
        sheet.append_rows(values, value_input_option="USER_ENTERED")
        logger.info(f"Se agregó nueva reseña: {review.guest_name} - {review.platform}")
        return True
    except Exception as e:
        logger.error(f"Error al agregar reseña: {e}")
        return False


def update_existing_review(sheet: gspread.Worksheet, review: Review) -> bool:
    """
    Actualiza SOLO 'V Limpieza' de una reseña existente (misma persona, misma fecha, mismo piso).
    Escribe como TEXTO (ej.: '5*'). No convierte a número.
    """
    try:
        records = sheet.get_all_records()

        target_date = review.review_date.strftime('%Y-%m-%d')
        target_name = clean_text(review.guest_name)
        target_floor = review.floor

        target_value = clean_text(getattr(review, "cleanliness_rating", ""))  # ej.: "5*"

        for i, record in enumerate(records, start=2):  # fila 1 = headers
            name_ok = clean_text(record.get('Nombre Huésped', '')) == target_name
            date_ok = clean_text(record.get('Fecha Reseña', '')) == target_date
            floor_ok = record.get('Piso') == target_floor

            if name_ok and date_ok and floor_ok:
                # Columna L (12) = "V Limpieza"
                rng = f"L{i}:L{i}"
                sheet.update(rng, [[target_value]], value_input_option="USER_ENTERED")
                logger.info(f"✅ Actualizada reseña: {target_name} - {target_date} - Limpieza: {target_value}")
                return True

        logger.warning(f"⚠️ No se encontró reseña para actualizar: {target_name} - {target_date}")
        return False

    except Exception as e:
        logger.error(f"❌ Error actualizando reseña: {e}")
        return False
