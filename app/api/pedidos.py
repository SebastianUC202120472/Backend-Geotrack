from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import io
from app.models.ruta import Ruta, RutaDetalle
from app.services.router import optimizar_secuencia_pedidos
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.pedido import Pedido
# AQUÍ ESTÁ LA LÍNEA QUE FALTABA PARA QUE FUNCIONE LA GEOCODIFICACIÓN
from app.services.geocoder import obtener_coordenadas 

router = APIRouter()

@router.post("/upload")
async def upload_pedidos(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        columnas_requeridas = ['numero_tracking', 'cliente_origen', 'direccion_destino']
        if not all(col in df.columns for col in columnas_requeridas):
             raise HTTPException(status_code=400, detail=f"El Excel debe contener las columnas: {columnas_requeridas}")

        pedidos_creados = 0
        for index, row in df.iterrows():
            existe = db.query(Pedido).filter(Pedido.numero_tracking == str(row['numero_tracking'])).first()
            if not existe:
                nuevo_pedido = Pedido(
                    numero_tracking=str(row['numero_tracking']),
                    cliente_origen=str(row['cliente_origen']),
                    direccion_destino=str(row['direccion_destino']),
                    peso_kg=float(row['peso_kg']) if 'peso_kg' in df.columns and pd.notna(row['peso_kg']) else 0.0,
                    volumen_m3=float(row['volumen_m3']) if 'volumen_m3' in df.columns and pd.notna(row['volumen_m3']) else 0.0
                )
                db.add(nuevo_pedido)
                pedidos_creados += 1
        
        db.commit()
        
        return {
            "mensaje": "Carga masiva exitosa", 
            "pedidos_nuevos": pedidos_creados,
            "total_filas_leidas": len(df)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")


@router.get("/")
def listar_pedidos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    pedidos = db.query(Pedido).offset(skip).limit(limit).all()
    return pedidos


@router.post("/geocodificar")
def procesar_geocodificacion(db: Session = Depends(get_db)):
    pedidos_pendientes = db.query(Pedido).filter(Pedido.latitud == None).all()
    
    if not pedidos_pendientes:
        return {"mensaje": "Todos los pedidos ya están geocodificados"}

    procesados = 0
    fallidos = 0

    for pedido in pedidos_pendientes:
        lat, lng = obtener_coordenadas(pedido.direccion_destino)
        
        if lat and lng:
            pedido.latitud = lat
            pedido.longitud = lng
            
            partes_direccion = pedido.direccion_destino.split(",")
            if len(partes_direccion) >= 2:
                pedido.distrito = partes_direccion[1].strip()
            else:
                pedido.distrito = "ZONA_DESCONOCIDA"
                
            procesados += 1
        else:
            pedido.estado = "GEOCODIFICACION_FALLIDA"
            fallidos += 1

    db.commit()
    
    return {
        "mensaje": "Proceso de geocodificación finalizado",
        "pedidos_exitosos": procesados,
        "pedidos_fallidos": fallidos
    }


@router.get("/zonas")
def agrupar_pedidos_por_zona(db: Session = Depends(get_db)):
    resultados = db.query(
        Pedido.distrito,
        func.count(Pedido.id).label('total_pedidos')
    ).filter(Pedido.latitud != None).group_by(Pedido.distrito).all()

    zonas = [{"distrito": r.distrito, "total_pedidos": r.total_pedidos} for r in resultados]
    
    return {"zonas_operativas": zonas}
