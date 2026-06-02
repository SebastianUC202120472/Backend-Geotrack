from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    numero_tracking = Column(String(50), unique=True, index=True, nullable=False)
    cliente_origen = Column(String(100), nullable=False)
    direccion_destino = Column(String(255), nullable=False)
    distrito = Column(String(100), nullable=True) # Lo llenaremos después con CUS-16
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    peso_kg = Column(Float, nullable=True)
    volumen_m3 = Column(Float, nullable=True)
    estado = Column(String(50), default="PENDIENTE") # PENDIENTE, EN_RUTA, ENTREGADO, FALLIDO
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)