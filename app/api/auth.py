# app/api/auth.py
# ============================================================================
# CAPA: API / ROUTER (puerta de entrada HTTP) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Expone las URLs de autenticación que consumen la Web y la App:
#               POST /api/auth/registro -> crear cuenta (CUS-01)
#               POST /api/auth/login    -> iniciar sesión y recibir el JWT (CUS-02)
# ¿CÓMO?      Son funciones "delgadas": reciben la petición, llaman al SERVICIO
#             y devuelven la respuesta. NO contienen lógica de negocio.
# ¿CON QUÉ SE CONECTA?
#   - services/usuario_service.py -> donde está la lógica real.
#   - schemas/usuario.py          -> moldes de entrada/salida (validación).
#   - db/database.py (get_db)     -> inyecta la sesión de base de datos.
#   - Lo registra: main.py con el prefijo /api/auth.
# ============================================================================
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, Token
from app.services import usuario_service

router = APIRouter()


@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registra un usuario nuevo (CUS-01).
    NOTA DE SEGURIDAD: hoy está abierto para facilitar el MVP. En producción
    debería exigir rol 'admin' (añadiendo Depends(get_current_admin)).
    """
    return usuario_service.registrar_usuario(db, usuario)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Inicia sesión (CUS-02) y devuelve el token JWT.
    Usa OAuth2PasswordRequestForm: el cliente envía 'username' (=correo) y
    'password'. Es lo que rellena el botón "Authorize" de Swagger.
    """
    access_token = usuario_service.autenticar_y_generar_token(
        db, correo=form_data.username, contrasena=form_data.password
    )
    return {"access_token": access_token, "token_type": "bearer"}
