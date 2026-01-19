# MGFisioBook - Sistema de Gestión de Citas para Fisioterapia

API REST construida con FastAPI para la gestión de citas, pacientes, terapeutas y facturas en un centro de fisioterapia.

## 🚀 Características

- ✅ Gestión de pacientes, terapeutas y tratamientos
- ✅ Sistema de reservas de citas con validación de conflictos
- ✅ Control de disponibilidad de terapeutas
- ✅ Generación automática de facturas
- ✅ Notificaciones push mediante Firebase
- ✅ Autenticación con Supabase
- ✅ Control de acceso basado en roles (Admin, Terapeuta, Paciente)
- ✅ API documentada con OpenAPI/Swagger

## 📋 Requisitos

- Python 3.12+
- PostgreSQL (producción) o SQLite (desarrollo/tests)
- Docker & Docker Compose (opcional)

## 🛠️ Instalación

### Opción 1: Docker (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd MGFisioBook

# Crear archivo .env con las variables de entorno necesarias
cp .env.example .env

# Construir y ejecutar
docker compose up --build -d
```

La API estará disponible en `http://localhost:8000`

### Opción 2: Instalación Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

## 🧪 Tests

### Configuración

Los tests requieren dependencias adicionales:

```bash
# En tu entorno virtual
pip install -r requirements.txt
```

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=app --cov-report=html

# Tests específicos
pytest tests/test_appointments_comprehensive.py -v
```

### Estructura de Tests

- `test_appointments_comprehensive.py` - Tests completos de citas
- `test_invoices_comprehensive.py` - Tests de facturas
- `test_patient_*.py` - Tests de pacientes
- `test_availability_service.py` - Tests de disponibilidad
- Más detalles en [tests/README.md](tests/README.md)

## 📚 Documentación de la API

Una vez iniciada la aplicación, visita:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🏗️ Estructura del Proyecto

```
MGFisioBook/
├── app/
│   ├── core/           # Configuración, seguridad, database
│   ├── models/         # Modelos SQLAlchemy
│   ├── routers/        # Endpoints de la API
│   ├── schemas/        # Schemas Pydantic
│   ├── services/       # Lógica de negocio
│   └── templates/      # Templates de emails
├── migrations/         # Migraciones de Alembic
├── tests/             # Tests automatizados
├── .github/           # CI/CD workflows
└── docker-compose.yml
```

## 🔐 Variables de Entorno

Crear un archivo `.env` con:

```env
# Supabase
SUPABASE_URL=tu_url_de_supabase
SUPABASE_PUBLISHABLE_KEY=tu_key_publica
SUPABASE_SECRET_KEY=tu_secret_key

# Base de datos
DATABASE_URL=postgresql+asyncpg://usuario:password@localhost/mgfisiobook

# JWT
JWT_SECRET_KEY=tu_secret_key_muy_seguro
JWT_ALGORITHM=HS256

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password

# Firebase (para notificaciones push)
FIREBASE_CREDENTIALS=path/to/firebase-service-account.json
```

## 🔄 CI/CD

El proyecto incluye GitHub Actions para:

- ✅ Ejecución automática de tests
- ✅ Análisis de código (black, isort, flake8)
- ✅ Build de imagen Docker

Ver detalles en [.github/workflows/README.md](.github/workflows/README.md)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

### Estándares de Código

```bash
# Formatear código
black app/ tests/
isort app/ tests/

# Verificar lint
flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
```

## 📝 Licencia

[Especificar licencia]

## 👥 Autores

[Tus datos]

## 📧 Contacto

[Tu contacto]
