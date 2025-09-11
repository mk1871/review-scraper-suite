# utils/text_utils.py
# -*- coding: utf-8 -*-

# Limpieza de comillas “fantasma” y caracteres invisibles que a veces se cuelan
_INVISIBLES = [
    "\u200b",  # ZERO WIDTH SPACE
    "\u200e",  # LEFT-TO-RIGHT MARK
    "\u200f",  # RIGHT-TO-LEFT MARK
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # bidi controls
    "\xa0",  # NBSP
]


def clean_text(value: str) -> str:
    """Limpia comillas iniciales y caracteres invisibles comunes."""
    if value is None:
        return ""
    s = str(value)
    for ch in _INVISIBLES:
        s = s.replace(ch, "")
    s = s.strip()
    # Si viene con comilla inicial (típico truco en Sheets), eliminarla
    if s.startswith("'") and len(s) > 1:
        s = s[1:].lstrip()
    return s
