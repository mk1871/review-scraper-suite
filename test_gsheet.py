# test_gsheet.py

from models.review import Review
from utils.gsheet_utils import setup_gspread, append_review_to_sheet
from datetime import date


def test_write_to_gsheet():
    print("📂 Conectando a Google Sheets...")
    try:
        sheet = setup_gspread(sheet_name="Todas")
        print("✅ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return

    # Crear una reseña de prueba
    review = Review(
        review_date=date(2025, 4, 5),
        check_in_date=date(2025, 4, 1),
        platform="Airbnb",
        rating="5*",
        guest_name="Juan Pérez",
        floor="A1",
        complaints_summary="Un poco ruidoso por la noche",
        suggestions="Mejorar insonorización",
        action_plan="",  # Se llena manualmente
        full_comment="Excelente lugar, muy limpio y cómodo. El entorno es precioso. Solo un poco de ruido por la noche.",
        added_date=date.today()
    )

    print("📝 Escribiendo reseña de prueba...")
    success = append_review_to_sheet(sheet, review)

    if success:
        print("✅ Reseña escrita correctamente en Google Sheets")
    else:
        print("❌ Error al escribir la reseña")


if __name__ == "__main__":
    test_write_to_gsheet()