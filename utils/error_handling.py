# utils/error_handling.py
# -*- coding: utf-8 -*-
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def handle_scraper_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            logger.warning("⚠️ Interrumpido por el usuario (Ctrl+C)")
            raise
        except Exception as e:
            logger.exception("❌ Error en %s: %s", fn.__name__, e)
            raise

    return wrapper
