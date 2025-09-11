# utils/logging_setup.py
# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Loggers “ruidosos” que queremos subir a WARNING para que no inunden la consola
_NOISY_LOGGERS = [
    "urllib3",
    "google",
    "googleapiclient",
    "google.auth",
    "google.auth.transport.requests",
    "oauth2client",
    "gspread",
    "playwright._impl._transport",
]

# Formatos
_CONSOLE_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_FILE_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_dir(path: Path):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def configure_logging(
        console_level: Optional[str] = None,
        file_level: Optional[str] = None,
        http_level: Optional[str] = None,
        log_file: Optional[str] = None,
        max_bytes: int = 2_000_000,  # ~2MB por archivo
        backup_count: int = 5,
):
    """
    Configura logging con dos handlers:
      - Consola: nivel console_level (default INFO).
      - Archivo rotativo: nivel file_level (default DEBUG) a logs/scraper.log.
    Además eleva a WARNING loggers ruidosos (http_level por env).

    Permite override vía ENV:
      APP_CONSOLE_LEVEL, APP_FILE_LEVEL, HTTP_LOG_LEVEL, LOG_FILE_PATH
    """
    console_level = (console_level or os.getenv("APP_CONSOLE_LEVEL", "INFO")).upper()
    file_level = (file_level or os.getenv("APP_FILE_LEVEL", "DEBUG")).upper()
    http_level = (http_level or os.getenv("HTTP_LOG_LEVEL", "WARNING")).upper()
    log_file = (log_file or os.getenv("LOG_FILE_PATH", "logs/scraper.log"))

    root = logging.getLogger()
    # Limpia handlers previos si se vuelve a llamar
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(logging.DEBUG)  # root al máximo; los handlers filtran

    # --- Consola ---
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, console_level, logging.INFO))
    ch.setFormatter(logging.Formatter(_CONSOLE_FMT, datefmt=_DATE_FMT))
    root.addHandler(ch)

    # --- Archivo rotativo ---
    log_path = Path(log_file)
    _ensure_log_dir(log_path)
    fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    fh.setLevel(getattr(logging, file_level, logging.DEBUG))
    fh.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # --- Elevar nivel de librerías ruidosas ---
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(getattr(logging, http_level, logging.WARNING))

    # Opcional: si quieres que SOLO tu app salga a INFO aunque el root esté en DEBUG,
    # puedes subir el nivel de los “demas” al WARNING y dejar tu namespace a INFO.
    # logging.getLogger("").setLevel(logging.WARNING)
    # logging.getLogger("scrapers").setLevel(logging.INFO)

    # Mensaje de arranque para confirmar configuración
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configurado: console=%s, file=%s, http=%s, file_path=%s",
        console_level, file_level, http_level, log_file
    )
