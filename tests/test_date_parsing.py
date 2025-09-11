# tests/test_date_parsing.py
# -*- coding: utf-8 -*-

from datetime import date
from utils.date_parsing import parse_spanish_date_range


def test_mismo_mes_y_anio():
    ci, co = parse_spanish_date_range("7–9 sept 2025 • ★LUJO★ Parking, Netflix")
    assert (ci, co) == (date(2025, 9, 7), date(2025, 9, 9))


def test_mismo_mes_y_anio_guion_simple():
    ci, co = parse_spanish_date_range("7-9 sep 2025")
    assert (ci, co) == (date(2025, 9, 7), date(2025, 9, 9))


def test_cruza_anio():
    ci, co = parse_spanish_date_range("29 dic 2024 – 2 ene 2025")
    assert (ci, co) == (date(2024, 12, 29), date(2025, 1, 2))


def test_sola():
    ci, co = parse_spanish_date_range("1 jul 2025")
    assert (ci, co) == (date(2025, 7, 1), date(2025, 7, 1))


def test_nombre_completo_mes():
    ci, co = parse_spanish_date_range("15 septiembre 2025")
    assert (ci, co) == (date(2025, 9, 15), date(2025, 9, 15))
