# 🚚 SIOL-SAVA Backend (MVP Logístico)

Backend del Sistema Integrado de Operaciones Logísticas (SIOL-SAVA), desarrollado para gestionar la distribución de última milla. Construido bajo una arquitectura limpia y containerizada.

## 🛠️ Stack Tecnológico
* **Framework:** FastAPI (Python 3.11)
* **Base de Datos:** PostgreSQL 15
* **ORM:** SQLAlchemy + Alembic
* **Infraestructura:** Docker & Docker Compose
* **Procesamiento de Datos:** Pandas, Geopy

## 📋 Requisitos Previos
Para levantar este proyecto en tu máquina local, **no necesitas instalar Python ni PostgreSQL**. Solo necesitas tener instalados:
1. [Git](https://git-scm.com/)
2. [Docker Desktop](https://www.docker.com/products/docker-desktop) (Asegúrate de que esté ejecutándose).

## 🚀 Guía de Despliegue Rápido

**1. Clonar el repositorio:**
```bash
git clone https://github.com/SebastianUC202120472/Backend-Geotrack
cd siol-sava-backend

cada vez para levantar el backend debes utilizar lo siguiente: 
docker compose down
docker compose up --build

Solo será necesario usar los endpoints que veras en el swagger para conectarlo al frontend según el caso aplique sea web o aplicación movil y si es necesario verlo directamente en el codigo, las base de datos son independientes, por ende, solo se despliega en base a la variables de la base de datos ya establecida.