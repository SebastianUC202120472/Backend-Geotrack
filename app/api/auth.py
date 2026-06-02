from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse, Token
from app.core.security import get_password_hash, verify_password, create_access_token


router = APIRouter()

@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # 1. Verificar si el correo ya existe en la base de datos
    db_user = db.query(Usuario).filter(Usuario.correo == usuario.correo).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # 2. Crear el usuario encriptando su contraseña
    nuevo_usuario = Usuario(
        correo=usuario.correo,
        hash_contrasena=get_password_hash(usuario.contrasena),
        rol=usuario.rol
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Buscar al usuario por correo (username)
    usuario = db.query(Usuario).filter(Usuario.correo == form_data.username).first()
    
    # 2. Verificar que exista y que la contraseña sea correcta
    if not usuario or not verify_password(form_data.password, usuario.hash_contrasena):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generar el Token JWT que usará el Frontend y la App Móvil
    access_token = create_access_token(data={"sub": usuario.correo, "rol": usuario.rol})
    return {"access_token": access_token, "token_type": "bearer"}