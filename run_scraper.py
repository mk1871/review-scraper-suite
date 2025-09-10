# run_scraper.py
"""
Script para ejecutar el scraper de Airbnb automáticamente.

Inicia Chrome en modo remoto con tu perfil y luego ejecuta el scraper.
"""

import subprocess
import time
import sys
import os
import signal
import atexit

# Configuración
CHROME_PATH = "google-chrome-stable"
USER_DATA_DIR = os.path.expanduser("~/.config/google-chrome")
PROFILE_NAME = "Default"
DEBUG_PORT = 9222
SCRAPER_SCRIPT = "test_remote_chrome.py"  # Cambiar por main.py cuando esté listo


def kill_chrome():
    """Cierra cualquier instancia de Chrome con el puerto de depuración."""
    print("🛑 Cerrando Chrome si está abierto...")
    try:
        subprocess.run(
            ["pkill", "-f", f"{CHROME_PATH}.*--remote-debugging-port={DEBUG_PORT}"],
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception as e:
        print(f"⚠️ Error al cerrar Chrome: {e}")


def start_chrome():
    """Inicia Chrome en modo remoto con el perfil especificado."""
    print("🚀 Iniciando Chrome en modo remoto...")
    chrome_cmd = [
        CHROME_PATH,
        f"--user-data-dir={USER_DATA_DIR}",
        f"--profile-directory={PROFILE_NAME}",
        f"--remote-debugging-port={DEBUG_PORT}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",  # Evita mensaje de "Chrome se cerró inesperadamente"
        "about:blank"
    ]

    try:
        process = subprocess.Popen(chrome_cmd)
        time.sleep(5)  # Esperar a que inicie

        # Registrar para cerrar Chrome al terminar el script
        atexit.register(lambda: os.kill(process.pid, signal.SIGTERM) if process.poll() is None else None)

        print("✅ Chrome iniciado")
        return process
    except Exception as e:
        print(f"❌ Error al iniciar Chrome: {e}")
        sys.exit(1)


def run_scraper():
    """Ejecuta el script del scraper."""
    print(f"🕷️ Ejecutando scraper: {SCRAPER_SCRIPT}")
    try:
        result = subprocess.run([sys.executable, SCRAPER_SCRIPT])
        return result.returncode
    except Exception as e:
        print(f"❌ Error al ejecutar el scraper: {e}")
        return 1


def main():
    """Función principal."""
    print("🔄 Iniciando proceso de scraping de Airbnb...")

    # 1. Cerrar Chrome si está abierto
    kill_chrome()

    # 2. Iniciar Chrome en modo remoto
    chrome_process = start_chrome()

    # 3. Ejecutar scraper
    exit_code = run_scraper()

    # 4. Cerrar Chrome al finalizar
    print("🔚 Cerrando Chrome...")
    if chrome_process and chrome_process.poll() is None:
        chrome_process.terminate()
        try:
            chrome_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome_process.kill()

    print("🏁 Proceso completado")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()