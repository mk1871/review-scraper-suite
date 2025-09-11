# utils/logging_setup.py
# -*- coding: utf-8 -*-
import os
import re
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Loggers ruidosos que queremos silenciar en consola
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

# =========================
# FORMATOS DE LOG
# =========================
# (ANTES) Formato VERBOSO en consola, con fecha | nivel | logger | mensaje
# _CONSOLE_FMT_VERBOSE = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# (AHORA) Consola ultra-limpia: solo el mensaje
_CONSOLE_FMT_MINIMAL = "%(message)s"

# Archivo con contexto completo
_FILE_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# Regex para filtrar líneas HTTP muy verbosas (GET/PUT/POST a sheets/oauth)
_HTTP_NOISE_RE = re.compile(
    r'\b(POST|GET|PUT|PATCH|DELETE)\s+/v4/(?:spreadsheets|.*)|oauth2\.googleapis\.com|sheets\.googleapis\.com',
    re.IGNORECASE
)


class ConsoleFilter(logging.Filter):
    """
    Filtra del handler de consola:
      - Cualquier DEBUG (también controlado por nivel).
      - Mensajes de loggers ruidosos.
      - Mensajes HTTP tipo 'GET /v4/spreadsheets...' y 'POST /token ...'.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.INFO:
            return False
        if any(record.name.startswith(lbl) for lbl in _NOISY_LOGGERS):
            return False
        msg = record.getMessage()
        if _HTTP_NOISE_RE.search(msg):
            return False
        return True


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
        max_bytes: int = 2_000_000,
        backup_count: int = 5,
):
    """
    Configura logging con dos handlers:
      - Consola: INFO+ limpio con filtro (solo el mensaje).
      - Archivo rotativo: DEBUG (detallado) en logs/scraper.log.

    Env vars:
      APP_CONSOLE_LEVEL (default INFO)
      APP_FILE_LEVEL    (default DEBUG)
      HTTP_LOG_LEVEL    (default WARNING)
      LOG_FILE_PATH     (default logs/scraper.log)
    """
    console_level = (console_level or os.getenv("APP_CONSOLE_LEVEL", "INFO")).upper()
    file_level = (file_level or os.getenv("APP_FILE_LEVEL", "DEBUG")).upper()
    http_level = (http_level or os.getenv("HTTP_LOG_LEVEL", "WARNING")).upper()
    log_file = (log_file or os.getenv("LOG_FILE_PATH", "logs/scraper.log"))

    root = logging.getLogger()

    # Evita duplicados si se reconfigura
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(logging.DEBUG)  # los handlers filtran

    # -----------------------
    # Consola (limpia)
    # -----------------------
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, console_level, logging.INFO))

    # (ANTES) Formato VERBOSO en consola (comentado a petición):
    # ch.setFormatter(logging.Formatter(_CONSOLE_FMT_VERBOSE, datefmt=_DATE_FMT))

    # (AHORA) Solo el mensaje:
    ch.setFormatter(logging.Formatter(_CONSOLE_FMT_MINIMAL, datefmt=_DATE_FMT))

    ch.addFilter(ConsoleFilter())
    root.addHandler(ch)

    # -----------------------
    # Archivo rotativo (DEBUG)
    # -----------------------
    log_path = Path(log_file)
    _ensure_log_dir(log_path)
    fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    fh.setLevel(getattr(logging, file_level, logging.DEBUG))
    fh.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # Sube nivel de librerías ruidosas (el filtro consola ya las corta)
    for name in _NOISY_LOGGERS:
        noisy = logging.getLogger(name)
        noisy.setLevel(getattr(logging, http_level, logging.WARNING))
        noisy.propagate = True

    # Mensaje de arranque (aparece como solo mensaje en consola, completo en archivo)
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configurado → console=%s, file=%s, http=%s, file_path=%s",
        console_level, file_level, http_level, log_file
    )
