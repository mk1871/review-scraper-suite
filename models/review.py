# models/review.py

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Review:
    # 1. Campos obligatorios (sin default)
    review_date: date
    check_in_date: date
    platform: str
    rating: str
    guest_name: str
    floor: str
    full_comment: str

    # 2. Campos opcionales (con default)
    complaints_summary: Optional[str] = None
    suggestions: Optional[str] = None
    action_plan: Optional[str] = None
    added_date: Optional[date] = None

    def __post_init__(self):
        if not isinstance(self.review_date, date):
            raise TypeError("review_date debe ser un objeto date")
        if not isinstance(self.check_in_date, date):
            raise TypeError("check_in_date debe ser un objeto date")

    def to_dict(self):
        return {
            "Fecha Reseña": self.review_date.strftime("%Y-%m-%d"),
            "Fecha Ingreso": self.check_in_date.strftime("%Y-%m-%d"),
            "Plataforma": self.platform,
            "Valoración": self.rating,
            "Nombre Huésped": self.guest_name,
            "Piso": self.floor,
            "Resumen Quejas": self.complaints_summary or "",
            "Sugerencias": self.suggestions or "",
            "Plan Acción": self.action_plan or "",
            "Comentario Completo": self.full_comment,
            "Fecha Añadida": self.added_date.strftime("%Y-%m-%d") if self.added_date else ""
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            review_date=date.fromisoformat(data["Fecha Reseña"]),
            check_in_date=date.fromisoformat(data["Fecha Ingreso"]),
            platform=data["Plataforma"],
            rating=data["Valoración"],
            guest_name=data["Nombre Huésped"],
            floor=data["Piso"],
            full_comment=data["Comentario Completo"],
            complaints_summary=data.get("Resumen Quejas", ""),
            suggestions=data.get("Sugerencias", ""),
            action_plan=data.get("Plan Acción", ""),
            added_date=date.fromisoformat(data["Fecha Añadida"]) if data["Fecha Añadida"] else None
        )