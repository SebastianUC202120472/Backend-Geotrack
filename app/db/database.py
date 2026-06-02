from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL de conexión exacta a tu contenedor Docker (tal como está en el docker-compose)
SQLALCHEMY_DATABASE_URL = "postgresql://sava_admin:sava_password123@db:5432/siol_sava_db"

# Motor de la base de datos
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Sesión para interactuar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredarán todos nuestros modelos (tablas)
Base = declarative_base()

# Dependencia para inyectar la sesión en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()