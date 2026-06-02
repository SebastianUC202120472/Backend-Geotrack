# app/api/rutas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.pedido import Pedido
from app.models.ruta import Ruta, RutaDetalle
from app.services.router import optimizar_secuencia_pedidos

router = APIRouter()

# --- ESQUEMAS ---
class AsignacionBloque(BaseModel):
    nombre_ruta: str
    distrito: str
    conductor_id: int

class SolicitudOptimizacion(BaseModel):
    ruta_id: int
    latitud_actual_conductor: float
    longitud_actual_conductor: float


# --- CUS-18: ADMINISTRADOR ASIGNA CARGA AL CONDUCTOR ---
@router.post("/asignar-bloque")
def administrador_asigna_bloque(asignacion: AsignacionBloque, db: Session = Depends(get_db)):
    # 1. Busca los pedidos PENDIENTES de ese distrito
    pedidos_zona = db.query(Pedido).filter(
        Pedido.distrito == asignacion.distrito, 
        Pedido.estado == "PENDIENTE"
    ).all()
    
    if not pedidos_zona:
        raise HTTPException(status_code=400, detail="No hay pedidos pendientes para esa zona")

    # 2. Crea la Ruta vacía
    nueva_ruta = Ruta(nombre=asignacion.nombre_ruta, conductor_id=asignacion.conductor_id)
    db.add(nueva_ruta)
    db.flush()
    
    # 3. Asigna los pedidos a la ruta (Sin secuencia matemática aún)
    for pedido in pedidos_zona:
        detalle = RutaDetalle(ruta_id=nueva_ruta.id, pedido_id=pedido.id, secuencia=0)
        pedido.estado = "ASIGNADO"
        db.add(detalle)
        
    db.commit()
    return {"mensaje": f"{len(pedidos_zona)} pedidos asignados a la ruta '{asignacion.nombre_ruta}'", "ruta_id": nueva_ruta.id}


# --- CUS-19: CONDUCTOR OPTIMIZA SU RUTA DESDE LA APP MÓVIL ---
@router.post("/conductor/optimizar")
def conductor_optimiza_ruta(solicitud: SolicitudOptimizacion, db: Session = Depends(get_db)):
    ruta = db.query(Ruta).filter(Ruta.id == solicitud.ruta_id).first()
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    
    # Obtenemos los pedidos usando los detalles
    pedidos_desordenados = []
    for detalle in ruta.detalles:
        pedido = db.query(Pedido).filter(Pedido.id == detalle.pedido_id).first()
        if pedido and pedido.latitud is not None:
            pedidos_desordenados.append(pedido)
            
    if not pedidos_desordenados:
         raise HTTPException(status_code=400, detail="La ruta no tiene pedidos válidos para optimizar")

    # AQUÍ ENTRA EL CEREBRO MATEMÁTICO (VRP)
    pedidos_ordenados = optimizar_secuencia_pedidos(
        pedidos_desordenados, 
        solicitud.latitud_actual_conductor, 
        solicitud.longitud_actual_conductor
    )
    
    # Actualizamos la base de datos con la secuencia final
    secuencia_actual = 1
    for pedido_optimizado in pedidos_ordenados:
        detalle = db.query(RutaDetalle).filter(
            RutaDetalle.ruta_id == ruta.id, 
            RutaDetalle.pedido_id == pedido_optimizado.id
        ).first()
        
        detalle.secuencia = secuencia_actual
        pedido_optimizado.estado = "EN_RUTA"
        secuencia_actual += 1
        
    db.commit()
    return {"mensaje": "Ruta optimizada matemáticamente", "total_paradas": len(pedidos_ordenados)}