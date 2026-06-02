from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    correo = Column(String(100), unique=True, index=True, nullable=False)
    hash_contrasena = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False) 
    estado = Column(Boolean, default=True)  
    fecha_creacion = Column(DateTime, default=datetime.utcnow)