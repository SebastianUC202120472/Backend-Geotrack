# app/repositories/ruta_repository.py
# Capa de acceso a datos para Rutas (Clean Architecture).
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.ruta import Ruta, RutaDetalle
from app.models.pedido import Pedido

# Una ruta se considera "activa" mientras no haya sido finalizada (CUS-28).
ESTADOS_RUTA_ACTIVA = ("CREADA", "EN_PROGRESO")


def obtener_ruta_activa_por_conductor(db: Session, conductor_id: int) -> Optional[Ruta]:
    """Devuelve la ruta activa más reciente asignada a un conductor."""
    return (
        db.query(Ruta)
        .filter(
            Ruta.conductor_id == conductor_id,
            Ruta.estado.in_(ESTADOS_RUTA_ACTIVA),
        )
        .order_by(Ruta.fecha_creacion.desc())
        .first()
    )


def obtener_detalles_con_pedido(
    db: Session, ruta_id: int
) -> List[Tuple[RutaDetalle, Pedido]]:
    """Devuelve los detalles de una ruta junto a su pedido, ordenados por secuencia."""
    return (
        db.query(RutaDetalle, Pedido)
        .join(Pedido, RutaDetalle.pedido_id == Pedido.id)
        .filter(RutaDetalle.ruta_id == ruta_id)
        .order_by(RutaDetalle.secuencia.asc())
        .all()
    )


def obtener_pedido_por_tracking(db: Session, numero_tracking: str) -> Optional[Pedido]:
    """Busca un pedido por su número de tracking (lectura QR)."""
    return (
        db.query(Pedido)
        .filter(Pedido.numero_tracking == numero_tracking)
        .first()
    )


def obtener_detalle_de_ruta(
    db: Session, ruta_id: int, pedido_id: int
) -> Optional[RutaDetalle]:
    """Devuelve el RutaDetalle que vincula un pedido con una ruta concreta."""
    return (
        db.query(RutaDetalle)
        .filter(
            RutaDetalle.ruta_id == ruta_id,
            RutaDetalle.pedido_id == pedido_id,
        )
        .first()
    )
