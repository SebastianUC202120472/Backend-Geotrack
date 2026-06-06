# app/core/security.py
# ============================================================================
# CAPA: CORE / SEGURIDAD — utilidades transversales
# ----------------------------------------------------------------------------
# ¿QUÉ HACE?  Centraliza la criptografía del sistema:
#               - Encriptar y verificar contraseñas (con Argon2).
#               - Crear y decodificar tokens JWT (la "credencial" del usuario).
# ¿CÓMO?      'passlib' hace el hash de contraseñas; 'jose' firma/verifica el JWT.
# ¿CON QUÉ SE CONECTA?
#   - Lo USAN: services/usuario_service.py (hash + crear token) y
#              api/deps.py (decodificar token para identificar al usuario).
# ============================================================================
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

# Contexto de encriptación. Usamos Argon2: estándar moderno y robusto,
# sin problemas de compilación en Windows/Docker.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# --- Parámetros del token JWT ---
# IMPORTANTE: en producción SECRET_KEY debería leerse de una variable de
# entorno (.env), nunca quedar fija en el código. Para el MVP la dejamos aquí.
SECRET_KEY = "tu_clave_super_secreta_aqui_para_el_mvp"
ALGORITHM = "HS256"                 # algoritmo de firma del token
# Duración del token. 480 min = 8 horas: cómodo para pruebas/demo de la tesis.
# En PRODUCCIÓN debería ser corto (ej. 30-60 min) por seguridad.
ACCESS_TOKEN_EXPIRE_MINUTES = 480


def get_password_hash(password: str) -> str:
    """Convierte una contraseña en texto plano a un hash seguro para guardar."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña escrita con el hash guardado. True si coincide."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un token JWT firmado. 'data' lleva la info del usuario (sub=correo, rol).
    Le añade una fecha de expiración ('exp') y lo firma con SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT; devuelve su contenido (payload).
    Lanza JWTError si el token es inválido o ya expiró (lo captura deps.py).
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
