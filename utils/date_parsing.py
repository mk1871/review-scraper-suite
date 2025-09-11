# utils/date_parsing.py
# -*- coding: utf-8 -*-
"""
Parser robusto de fechas en español para las tarjetas de reseña de Airbnb.
Cubre casos como:
- "7–9 sept 2025 • ★LUJO★ ..."
- "7-9 sep 2025"
- "29 dic 2024 – 2 ene 2025"
- "1 jul 2025"
No depende del locale del sistema.

Uso típico:
    from utils.date_parsing import parse_spanish_date_range
    check_in, check_out = parse_spanish_date_range(raw_text)
    review_date = check_out
"""

from __future__ import annotations
import re
from datetime import date
from typing import Tuple

# Normalizamos tanto las abreviaturas que viste en Airbnb, como equivalentes comunes.
# En Airbnb: ene, feb, mar, abr, may, jun, jul, ago, sept, oct, nov, dic
_MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12,
    # nombres completos (por robustez)
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

_EN_DASH = "\u2013"  # “–”


def _norm(s: str) -> str:
    s = s.lower().strip()
    # Airbnb suele usar en-dash; lo normalizamos a "-".
    s = s.replace(_EN_DASH, "-")
    # Si hay bullet "•" (título del anuncio), nos quedamos con la parte de fechas previa.
    if "•" in s:
        s = s.split("•", 1)[0].strip()
    # Compacta espacios y guiones con espacios alrededor
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _to_month(token: str) -> int:
    t = token.lower().strip(".").strip()
    if t in _MONTHS_ES:
        return _MONTHS_ES[t]
    # fallback: primeras 3 letras
    t3 = t[:3]
    if t3 in _MONTHS_ES:
        return _MONTHS_ES[t3]
    raise ValueError(f"Mes no reconocido: {token!r}")


def parse_spanish_date_range(text: str) -> Tuple[date, date]:
    """
    Devuelve (check_in, check_out).
    - Si el texto contiene un rango dentro del mismo mes y año: "7-9 sept 2025"
    - Si el texto contiene un rango cruzando mes/año: "29 dic 2024 - 2 ene 2025"
    - Si el texto trae una sola fecha: "1 jul 2025" (in == out)
    Lanza ValueError si no puede parsear.
    """
    s = _norm(text)

    # 1) Rango mismo mes y año: "7-9 sept 2025"
    m = re.search(r"\b(\d{1,2})-(\d{1,2})\s+([a-záéíóú]+)\s+(\d{4})\b", s)
    if m:
        d1, d2, mon, y = int(m[1]), int(m[2]), _to_month(m[3]), int(m[4])
        return date(y, mon, d1), date(y, mon, d2)

    # 2) Rango cruzando mes/año: "29 dic 2024 - 2 ene 2025"
    m = re.search(
        r"\b(\d{1,2})\s+([a-záéíóú]+)\s+(\d{4})-(\d{1,2})\s+([a-záéíóú]+)\s+(\d{4})\b",
        s
    )
    if m:
        d1, mon1, y1 = int(m[1]), _to_month(m[2]), int(m[3])
        d2, mon2, y2 = int(m[4]), _to_month(m[5]), int(m[6])
        return date(y1, mon1, d1), date(y2, mon2, d2)

    # 3) Sola: "1 jul 2025"
    m = re.search(r"\b(\d{1,2})\s+([a-záéíóú]+)\s+(\d{4})\b", s)
    if m:
        d, mon, y = int(m[1]), _to_month(m[2]), int(m[3])
        the_date = date(y, mon, d)
        return the_date, the_date

    raise ValueError(f"No se pudo parsear rango/fecha desde: {text!r}")
