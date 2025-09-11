# config/settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de Google Sheets
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1vYfIeIkR3NYw5DwJ8dnoTfKvEI8_sXt0Uk9eF4BvzyY")
SHEET_NAME = os.getenv("SHEET_NAME", "Todas")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", BASE_DIR / "config" / "credentials.json")

# Configuración de Chrome
CHROME_DEBUG_PORT = int(os.getenv("CHROME_DEBUG_PORT", "9222"))
CHROME_USER_DATA_DIR = os.getenv("CHROME_USER_DATA_DIR", str(Path.home() / ".config" / "google-chrome"))
CHROME_PROFILE = os.getenv("CHROME_PROFILE", "Default")

# URLs
AIRBNB_BASE_URL = "https://www.airbnb.es"
