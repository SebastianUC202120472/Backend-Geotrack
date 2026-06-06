# app/services/dashboard_service.py
# ============================================================================
# CAPA: SERVICIO (lógica de negocio) — Trazabilidad (Fase 4)
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  La inteligencia del panel de monitoreo del admin:
#               - CUS-33: estado de la flota (avance de cada ruta) y KPIs globales.
#               - CUS-35: arma la línea de tiempo (historial) de un paquete.
# ¿CÓMO?      Lee datos con los repositorios y los resume en porcentajes y eventos.
# ¿CON QUÉ SE CONECTA?
#   - repositories/ruta_repository.py    -> rutas y sus detalles.
#   - repositories/pedido_repository.py  -> conteos de pedidos y búsqueda por tracking.
#   - repositories/usuario_repository.py -> correo del conductor de cada ruta.
#   - schemas/dashboard.py               -> moldes de respuesta.
#   - Lo USA: api/dashboard.py.
# ============================================================================
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import ruta_repository, pedido_repository, usuario_repository
from app.schemas.dashboard import (
    RutaFlota,
    FlotaResponse,
    ResumenResponse,
    EventoHistorial,
    HistorialPedidoResponse,
)

ESTADOS_RUTA_ACTIVA = ("CREADA", "EN_PROGRESO")


def _contar_estados(detalles) -> tuple[int, int, int]:
    """Cuenta (entregadas, fallidas, pendientes) a partir de los detalles de una ruta."""
    entregadas = sum(1 for d, _ in detalles if d.estado_entrega == "ENTREGADO")
    fallidas = sum(1 for d, _ in detalles if d.estado_entrega == "FALLIDO")
    pendientes = sum(1 for d, _ in detalles if d.estado_entrega == "PENDIENTE")
    return entregadas, fallidas, pendientes


# ============ CUS-33: Seguimiento de la flota ============
def obtener_flota(db: Session) -> FlotaResponse:
    """Resume el avance de TODAS las rutas para el tablero de la flota."""
    rutas = ruta_repository.listar_rutas(db)

    # Caché de correos de conductores para no repetir consultas (evita N+1).
    cache_conductores: dict[int, str] = {}

    items: list[RutaFlota] = []
    for ruta in rutas:
        detalles = ruta_repository.obtener_detalles_con_pedido(db, ruta.id)
        total = len(detalles)
        entregadas, fallidas, pendientes = _contar_estados(detalles)

        # % de avance = (gestionadas / total) * 100, redondeado a 1 decimal.
        gestionadas = entregadas + fallidas
        avance = round((gestionadas / total) * 100, 1) if total else 0.0

        # Correo del conductor (si la ruta tiene uno asignado).
        correo = None
        if ruta.conductor_id:
            if ruta.conductor_id not in cache_conductores:
                u = usuario_repository.obtener_por_id(db, ruta.conductor_id)
                cache_conductores[ruta.conductor_id] = u.correo if u else None
            correo = cache_conductores[ruta.conductor_id]

        items.append(
            RutaFlota(
                ruta_id=ruta.id,
                nombre=ruta.nombre,
                estado=ruta.estado,
                conductor_id=ruta.conductor_id,
                conductor_correo=correo,
                vehiculo_placa=ruta.vehiculo_placa,
                total_paradas=total,
                entregadas=entregadas,
                fallidas=fallidas,
                pendientes=pendientes,
                avance_porcentaje=avance,
                fecha_creacion=ruta.fecha_creacion,
                fecha_fin=ruta.fecha_fin,
            )
        )

    return FlotaResponse(total_rutas=len(items), rutas=items)


def obtener_resumen(db: Session) -> ResumenResponse:
    """KPIs globales: pedidos por estado y conteo de rutas (CUS-33)."""
    por_estado = {estado: total for estado, total in pedido_repository.contar_por_estado(db)}
    total_pedidos = pedido_repository.contar_total(db)

    rutas = ruta_repository.listar_rutas(db)
    activas = sum(1 for r in rutas if r.estado in ESTADOS_RUTA_ACTIVA)
    finalizadas = sum(1 for r in rutas if r.estado == "FINALIZADA")

    return ResumenResponse(
        total_pedidos=total_pedidos,
        pedidos_por_estado=por_estado,
        total_rutas=len(rutas),
        rutas_activas=activas,
        rutas_finalizadas=finalizadas,
    )


# ============ CUS-35: Historial / línea de tiempo de un paquete ============
def obtener_historial(db: Session, numero_tracking: str) -> HistorialPedidoResponse:
    """
    Reconstruye la línea de tiempo de un paquete con los datos disponibles
    (creación, asignación a ruta, optimización y entrega/fallo).
    NOTA: se reconstruye desde el estado actual; un registro de eventos
    dedicado sería una mejora futura.
    """
    pedido = pedido_repository.obtener_por_tracking(db, numero_tracking)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un pedido con tracking '{numero_tracking}'",
        )

    eventos: list[EventoHistorial] = []

    # 1) Siempre: el pedido fue registrado.
    eventos.append(EventoHistorial(
        evento="REGISTRADO",
        descripcion="El pedido ingresó al sistema (carga de Excel).",
        fecha=pedido.fecha_creacion,
    ))

    # 2) Geocodificación (si ya tiene coordenadas).
    if pedido.latitud is not None and pedido.longitud is not None:
        eventos.append(EventoHistorial(
            evento="GEOCODIFICADO",
            descripcion=f"Ubicado en el distrito '{pedido.distrito}'.",
            fecha=None,  # no guardamos la hora exacta de geocodificación
        ))

    # 3) Si está en una ruta, añadimos asignación / en ruta / cierre.
    ruta_nombre = None
    secuencia = None
    url_evidencia = None
    motivo_fallo = None

    par = ruta_repository.obtener_detalle_y_ruta_por_pedido(db, pedido.id)
    if par:
        detalle, ruta = par
        ruta_nombre = ruta.nombre
        secuencia = detalle.secuencia
        url_evidencia = detalle.url_evidencia
        motivo_fallo = detalle.motivo_fallo

        eventos.append(EventoHistorial(
            evento="ASIGNADO",
            descripcion=f"Asignado a la ruta '{ruta.nombre}'.",
            fecha=ruta.fecha_creacion,
        ))

        if detalle.secuencia and detalle.secuencia > 0:
            eventos.append(EventoHistorial(
                evento="EN_RUTA",
                descripcion=f"Programado como parada N° {detalle.secuencia} de la ruta.",
                fecha=None,
            ))

        # Entrega o fallo (evento final, si ya se gestionó).
        if detalle.estado_entrega == "ENTREGADO":
            eventos.append(EventoHistorial(
                evento="ENTREGADO",
                descripcion="Paquete entregado al cliente. Evidencia (POD) registrada."
                            if detalle.url_evidencia else "Paquete entregado al cliente.",
                fecha=detalle.fecha_gestion,
            ))
        elif detalle.estado_entrega == "FALLIDO":
            eventos.append(EventoHistorial(
                evento="FALLIDO",
                descripcion=f"Entrega fallida. Motivo: {detalle.motivo_fallo or 'no especificado'}.",
                fecha=detalle.fecha_gestion,
            ))

    return HistorialPedidoResponse(
        numero_tracking=pedido.numero_tracking,
        cliente_origen=pedido.cliente_origen,
        direccion_destino=pedido.direccion_destino,
        distrito=pedido.distrito,
        estado_actual=pedido.estado,
        ruta_asignada=ruta_nombre,
        secuencia=secuencia,
        url_evidencia=url_evidencia,
        motivo_fallo=motivo_fallo,
        eventos=eventos,
    )
