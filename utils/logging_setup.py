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

# Formatos
_CONSOLE_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_FILE_FMT = "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

# Regex para filtrar líneas HTTP muy verbosas (GET/PUT/POST a sheets.googleapis.com, oauth2, etc.)
_HTTP_NOISE_RE = re.compile(
    r'\b(POST|GET|PUT|PATCH|DELETE)\s+/v4/(?:spreadsheets|.*)|oauth2\.googleapis\.com|sheets\.googleapis\.com',
    re.IGNORECASE
)


class ConsoleFilter(logging.Filter):
    """
    Filtra del handler de consola:
      - Cualquier DEBUG (se controla también por nivel, pero por si otro handler cambia).
      - Mensajes de loggers ruidosos.
      - Mensajes HTTP tipo 'GET /v4/spreadsheets...' y 'POST /token ...'.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Bloquear DEBUG en consola
        if record.levelno < logging.INFO:
            return False

        # Bloquear loggers ruidosos
        if any(record.name.startswith(lbl) for lbl in _NOISY_LOGGERS):
            return False

        # Bloquear mensajes HTTP/Sheets/OAuth en consola
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
        max_bytes: int = 2_000_000,  # ~2MB
        backup_count: int = 5,
):
    """
    Configura logging con dos handlers:
      - Consola: INFO+ limpio (con filtro).
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

    # Quitar cualquier handler previo que otro módulo haya registrado (evita “doble log”)
    for h in list(root.handlers):
        root.removeHandler(h)

    # Root al máximo; los handlers filtran
    root.setLevel(logging.DEBUG)

    # --- Consola (INFO+) con filtro de ruido ---
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, console_level, logging.INFO))
    ch.setFormatter(logging.Formatter(_CONSOLE_FMT, datefmt=_DATE_FMT))
    ch.addFilter(ConsoleFilter())
    root.addHandler(ch)

    # --- Archivo rotativo (DEBUG completo) ---
    log_path = Path(log_file)
    _ensure_log_dir(log_path)
    fh = RotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    fh.setLevel(getattr(logging, file_level, logging.DEBUG))
    fh.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    root.addHandler(fh)

    # Subir nivel de loggers ruidosos para todos los handlers
    for name in _NOISY_LOGGERS:
        noisy = logging.getLogger(name)
        noisy.setLevel(getattr(logging, http_level, logging.WARNING))
        noisy.propagate = True  # siguen yendo al archivo si son WARNING+, pero el filtro consola los corta

    # Mensaje de arranque (aparece en consola y archivo)
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configurado → console=%s, file=%s, http=%s, file_path=%s",
        console_level, file_level, http_level, log_file
    )
