# app/models/pedido.py
# ============================================================================
# CAPA: MODELO (tabla de base de datos) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define la tabla 'pedidos': cada paquete que entra al sistema.
#             Es el corazón del Inbound (Fase 2) y de la trazabilidad.
# ¿CON QUÉ SE CONECTA?
#   - Hereda de 'Base' (db/database.py).
#   - La consultan: repositories/pedido_repository.py y ruta_repository.py.
#   - Se vincula a una ruta a través de 'ruta_detalles' (ver models/ruta.py).
# ============================================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.database import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    numero_tracking = Column(String(50), unique=True, index=True, nullable=False)  # código único (se lee por QR)
    cliente_origen = Column(String(100), nullable=False)   # quién envía el paquete
    direccion_destino = Column(String(255), nullable=False)  # a dónde se entrega
    distrito = Column(String(100), nullable=True)   # se rellena al geocodificar (CUS-16)
    latitud = Column(Float, nullable=True)          # coordenada (CUS-15)
    longitud = Column(Float, nullable=True)         # coordenada (CUS-15)
    peso_kg = Column(Float, nullable=True)
    volumen_m3 = Column(Float, nullable=True)
    # Ciclo de vida del paquete:
    # PENDIENTE -> ASIGNADO -> EN_RUTA -> ENTREGADO / FALLIDO
    estado = Column(String(50), default="PENDIENTE")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)  # se sella al marcar ENTREGADO (CUS-26)
