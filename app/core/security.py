from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt

# Usamos argon2, es el estándar más robusto y sin errores de compilación
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

SECRET_KEY = "tu_clave_super_secreta_aqui_para_el_mvp"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decodifica y valida un token JWT. Lanza JWTError si es inválido o expiró."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])