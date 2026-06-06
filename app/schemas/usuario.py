# app/schemas/usuario.py
# ============================================================================
# CAPA: SCHEMA (validación de datos con Pydantic) — Clean Architecture
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Define los "moldes" de los datos que ENTRAN y SALEN por la API.
#             Pydantic valida automáticamente tipos y formatos (ej. el correo).
# ¿POR QUÉ separado del modelo?  El modelo es la tabla (BD); el schema es el
#             contrato con el cliente. Así nunca exponemos campos sensibles
#             (como el hash de la contraseña).
# ¿CON QUÉ SE CONECTA?
#   - Lo USAN: api/auth.py y services/usuario_service.py.
# ============================================================================
from pydantic import BaseModel, EmailStr


class UsuarioCreate(BaseModel):
    """Molde de ENTRADA: lo que el cliente envía para crear un usuario."""
    correo: EmailStr   # EmailStr valida que tenga formato de correo válido
    contrasena: str
    rol: str           # debe ser 'admin' o 'conductor'


class UsuarioResponse(BaseModel):
    """Molde de SALIDA: lo que devolvemos al cliente (SIN la contraseña)."""
    id: int
    correo: EmailStr
    rol: str
    estado: bool

    class Config:
        from_attributes = True  # permite construir el schema desde un objeto SQLAlchemy


class Token(BaseModel):
    """Molde de SALIDA del login: el token JWT y su tipo."""
    access_token: str
    token_type: str
