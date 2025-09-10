# test_chrome_profile.py
import os
from playwright.sync_api import sync_playwright


def get_chrome_user_data_dir():
    """Devuelve la ruta del perfil de Chrome según el sistema operativo"""
    if os.name == 'nt':  # Windows
        return os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data')
    elif 'darwin' in os.sys.platform:  # macOS
        return os.path.expanduser('~/Library/Application Support/Google/Chrome')
    else:  # Linux
        return os.path.expanduser('~/.config/google-chrome')


def test_chrome_profile():
    user_data_dir = get_chrome_user_data_dir()
    profile_dir = "Default"  # o "Profile 1", etc.

    print(f"Usando perfil: {user_data_dir}/{profile_dir}")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            args=[f"--profile-directory={profile_dir}"]
        )
        page = browser.new_page()

        print("Abriendo Airbnb...")
        page.goto("https://www.airbnb.com/rooms/XXXXXXXXX/reviews")  # Usa una URL real tuya

        print("Verifica manualmente si estás logueado y si se cargan las reseñas.")
        print("Cierra el navegador cuando termines de verificar.")

        # Espera indefinidamente hasta que cierres el navegador
        page.wait_for_timeout(60000)  # 60 segundos, ajusta si necesitas más
        browser.close()


if __name__ == "__main__":
    test_chrome_profile()