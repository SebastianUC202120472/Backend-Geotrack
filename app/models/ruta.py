from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False) # Ej: "Ruta San Miguel - Tarde"
    estado = Column(String(50), default="CREADA") # CREADA, EN_PROGRESO, FINALIZADA
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Asignaciones (Para simplicidad, lo enlazamos por ID o nombre de momento)
    vehiculo_placa = Column(String(20), nullable=True)
    conductor_id = Column(Integer, nullable=True)

    # Relación con el detalle
    detalles = relationship("RutaDetalle", back_populates="ruta", cascade="all, delete")

class RutaDetalle(Base):
    __tablename__ = "ruta_detalles"

    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(Integer, ForeignKey("rutas.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    
    # ¡ESTE ES EL CAMPO MÁS IMPORTANTE PARA EL VRP!
    secuencia = Column(Integer, nullable=False) 
    
    estado_entrega = Column(String(50), default="PENDIENTE") # PENDIENTE, ENTREGADO, FALLIDO

    # Relaciones
    ruta = relationship("Ruta", back_populates="detalles")
    # Nota: Aquí asumo que en tu pedido.py no pusiste 'relationship', 
    # por ahora está bien mantenerlo simple.