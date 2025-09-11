# utils/error_handling.py
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def handle_scraper_errors(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            # Puedes agregar lógica específica aquí, como notificaciones
            raise

    return wrapper
