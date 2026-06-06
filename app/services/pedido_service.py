# app/services/pedido_service.py
# ============================================================================
# CAPA: SERVICIO (lógica de negocio) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  La inteligencia del módulo Inbound:
#               - CUS-13: leer el Excel y crear los pedidos (evitando duplicados).
#               - CUS-15: geocodificar (dirección -> latitud/longitud).
#               - CUS-16: agrupar pedidos por distrito.
# ¿CÓMO?      Usa pandas para el Excel y el repositorio para tocar la BD.
# ¿CON QUÉ SE CONECTA?
#   - repositories/pedido_repository.py -> lectura/escritura de pedidos.
#   - services/geocoder.py              -> convierte direcciones en coordenadas.
#   - Lo USA: api/pedidos.py.
# ============================================================================
import io
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.pedido import Pedido
from app.repositories import pedido_repository
from app.services.geocoder import obtener_coordenadas

# Columnas mínimas que debe traer el Excel para poder procesarlo.
COLUMNAS_REQUERIDAS = ["numero_tracking", "cliente_origen", "direccion_destino"]


def cargar_pedidos_excel(db: Session, contenido: bytes, nombre_archivo: str) -> dict:
    """
    CUS-13: recibe el contenido de un Excel y crea los pedidos nuevos.
    Pasos: validar extensión -> leer con pandas -> validar columnas ->
           saltar los tracking ya existentes -> guardar en bloque.
    """
    # 1) Validación de formato (antes del try, para que devuelva un 400 limpio).
    if not nombre_archivo.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    # 2) Leer el Excel a un DataFrame de pandas.
    try:
        df = pd.read_excel(io.BytesIO(contenido))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el archivo: {e}")

    # 3) Verificar que estén las columnas obligatorias.
    if not all(col in df.columns for col in COLUMNAS_REQUERIDAS):
        raise HTTPException(
            status_code=400,
            detail=f"El Excel debe contener las columnas: {COLUMNAS_REQUERIDAS}",
        )

    # 4) Construir la lista de pedidos nuevos, ignorando los tracking repetidos.
    nuevos: list[Pedido] = []
    for _, fila in df.iterrows():
        tracking = str(fila["numero_tracking"])
        if pedido_repository.obtener_por_tracking(db, tracking):
            continue  # ya existe -> no lo duplicamos

        nuevos.append(
            Pedido(
                numero_tracking=tracking,
                cliente_origen=str(fila["cliente_origen"]),
                direccion_destino=str(fila["direccion_destino"]),
                # peso/volumen son opcionales: si no vienen, ponemos 0.0
                peso_kg=float(fila["peso_kg"]) if "peso_kg" in df.columns and pd.notna(fila["peso_kg"]) else 0.0,
                volumen_m3=float(fila["volumen_m3"]) if "volumen_m3" in df.columns and pd.notna(fila["volumen_m3"]) else 0.0,
            )
        )

    # 5) Guardar todos de una sola vez.
    if nuevos:
        pedido_repository.crear_pedidos(db, nuevos)

    return {
        "mensaje": "Carga masiva exitosa",
        "pedidos_nuevos": len(nuevos),
        "total_filas_leidas": len(df),
    }


def procesar_geocodificacion(db: Session) -> dict:
    """
    CUS-15: para cada pedido sin coordenadas, obtiene su latitud/longitud y
    deduce el distrito a partir de la dirección. Marca como fallido si no se logra.
    """
    pendientes = pedido_repository.obtener_sin_coordenadas(db)
    if not pendientes:
        return {"mensaje": "Todos los pedidos ya están geocodificados"}

    exitosos = 0
    fallidos = 0

    for pedido in pendientes:
        lat, lng = obtener_coordenadas(pedido.direccion_destino)

        if lat and lng:
            pedido.latitud = lat
            pedido.longitud = lng

            # Heurística simple: el distrito suele ser la 2ª parte de la dirección
            # ("Av. X, San Miguel, Lima" -> "San Miguel").
            partes = pedido.direccion_destino.split(",")
            pedido.distrito = partes[1].strip() if len(partes) >= 2 else "ZONA_DESCONOCIDA"
            exitosos += 1
        else:
            pedido.estado = "GEOCODIFICACION_FALLIDA"
            fallidos += 1

    pedido_repository.guardar_cambios(db)  # confirma todos los cambios juntos

    return {
        "mensaje": "Proceso de geocodificación finalizado",
        "pedidos_exitosos": exitosos,
        "pedidos_fallidos": fallidos,
    }


def listar_pedidos(db: Session, skip: int, limit: int):
    """Devuelve los pedidos paginados (panel web del admin)."""
    return pedido_repository.listar(db, skip=skip, limit=limit)


def agrupar_por_zona(db: Session) -> dict:
    """CUS-16: arma la lista de zonas operativas con su conteo de pedidos."""
    resultados = pedido_repository.agrupar_por_zona(db)
    zonas = [{"distrito": r.distrito, "total_pedidos": r.total_pedidos} for r in resultados]
    return {"zonas_operativas": zonas}
