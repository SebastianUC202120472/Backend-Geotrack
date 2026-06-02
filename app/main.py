import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router  
from app.db.database import engine, Base, SessionLocal 
from app.models.usuario import Usuario 
from app.models.pedido import Pedido
from app.models.ruta import Ruta, RutaDetalle
from sqlalchemy import func
from app.services.geocoder import obtener_coordenadas  
from app.api.pedidos import router as pedidos_router
from app.api.rutas import router as rutas_router  # <-- AÑADE ESTO

async def tarea_limpieza_usuarios():
    while True:
        await asyncio.sleep(3600)
        db = SessionLocal()
        try:
            hace_6_horas = datetime.utcnow() - timedelta(hours=6)
            db.query(Usuario).filter(
                Usuario.correo.like("%@prueba.com%"),
                Usuario.fecha_creacion <= hace_6_horas
            ).delete(synchronize_session=False)
            db.commit()
            print("Limpieza de usuarios de prueba completada.")
        except Exception as e:
            db.rollback()
            print(f"Error en limpieza automática: {e}")
        finally:
            db.close()

# --- CICLO DE VIDA DE LA APLICACIÓN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # SOLUCIÓN A LA CARRERA DE DOCKER: Esperamos 5 segundos a que PostgreSQL despierte
    print("Esperando 5 segundos a que PostgreSQL esté 100% listo...")
    await asyncio.sleep(5)
    
    # Ahora sí, creamos las tablas de forma segura
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    
    # Arrancamos tu vigilante de limpieza
    print("Iniciando tarea de limpieza en segundo plano...")
    tarea_background = asyncio.create_task(tarea_limpieza_usuarios())
    yield
    tarea_background.cancel()

# --- CONFIGURACIÓN DE FASTAPI ---
app = FastAPI(
    title="SIOL-SAVA API",
    version="1.0.0",
    lifespan=lifespan 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(pedidos_router, prefix="/api/pedidos", tags=["Gestión de Pedidos"])
app.include_router(pedidos_router, prefix="/api/pedidos", tags=["Gestión de Pedidos"])
app.include_router(rutas_router, prefix="/api/rutas", tags=["Enrutamiento y Flota"]) 

@app.get("/")
def health_check():
    return {"status": "online", "message": "Backend SIOL-SAVA operativo"}