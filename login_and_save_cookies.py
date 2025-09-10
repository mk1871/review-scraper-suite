# login_and_save_cookies.py
import os
import json
from playwright.sync_api import sync_playwright


def get_chrome_user_data_dir():
    if os.name == 'nt':
        return os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data')
    elif 'darwin' in os.sys.platform:
        return os.path.expanduser('~/Library/Application Support/Google/Chrome')
    else:
        return os.path.expanduser('~/.config/google-chrome')


def login_and_save_cookies():
    user_data_dir = get_chrome_user_data_dir()
    profile_dir = "Default"

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            args=[f"--profile-directory={profile_dir}"]
        )
        page = browser.new_page()

        print(".chrome/Abriendo Airbnb para hacer login...")
        page.goto("https://www.airbnb.com/login")

        print("Inicia sesión manualmente en Airbnb.")
        print("Una vez logueado, visita una página de reseñas para confirmar acceso.")
        print("Cuando estés listo, presiona ENTER aquí.")
        input("Presiona ENTER cuando hayas iniciado sesión...")

        # Guardar cookies
        cookies = browser.cookies()
        with open("airbnb_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print("✅ Cookies guardadas en 'airbnb_cookies.json'")
        browser.close()


if __name__ == "__main__":
    login_and_save_cookies()