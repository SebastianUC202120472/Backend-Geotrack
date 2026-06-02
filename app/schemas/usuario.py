from pydantic import BaseModel, EmailStr

# Molde de lo que el frontend debe enviarnos para CREAR un usuario
class UsuarioCreate(BaseModel):
    correo: EmailStr
    contrasena: str
    rol: str  # Debe ser 'admin' o 'conductor'

# Molde de lo que le DEVOLVEMOS al frontend (Ocultamos la contraseña)
class UsuarioResponse(BaseModel):
    id: int
    correo: EmailStr
    rol: str
    estado: bool

    class Config:
        from_attributes = True # Permite a Pydantic leer los modelos de SQLAlchemy

# Molde para responder con el Token cuando hacen Login
class Token(BaseModel):
    access_token: str
    token_type: str