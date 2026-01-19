# GitHub Actions CI/CD

Este directorio contiene los workflows de CI/CD del proyecto MGFisioBook.

## Workflows

### `ci.yml` - Pipeline Principal

Este workflow se ejecuta en:

- Push a las ramas `main` y `develop`
- Pull requests hacia `main` y `develop`

#### Jobs

**1. test** - Ejecución de Tests

- ✅ Configura Python 3.12
- ✅ Instala dependencias desde `requirements.txt`
- ✅ Ejecuta pytest con cobertura de código
- ✅ Sube reportes de cobertura a Codecov (opcional)

Variables de entorno configuradas:

```
SUPABASE_URL=https://example.supabase.co
SUPABASE_PUBLISHABLE_KEY=test_pubkey
SUPABASE_SECRET_KEY=test_secret
SMTP_USER=test@example.com
SMTP_PASSWORD=test_password
JWT_SECRET_KEY=test_jwt_secret_key_for_ci
DATABASE_URL=sqlite+aiosqlite:///./test_ci.db
```

**2. lint** - Análisis de Código

- ✅ Verifica formato con `black`
- ✅ Verifica orden de imports con `isort`
- ✅ Análisis estático con `flake8`

Configuración de linting:

- Max line length: 88 (estándar black)
- Ignora: E203, W503 (compatibilidad con black)

**3. docker** - Build de Imagen Docker

- ⚠️ Solo se ejecuta en push a `main`
- ⚠️ Requiere que los jobs test y lint pasen
- ✅ Construye la imagen Docker
- ✅ Verifica la imagen ejecutando `python --version`

## Configuración Local

Para replicar los checks de CI localmente:

### Tests

```bash
pytest tests/ -v --cov=app --cov-report=term
```

### Linting

```bash
# Formatear código
black app/ tests/

# Ordenar imports
isort app/ tests/

# Lint
flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503
```

### Docker

```bash
docker build -t mgfisiobook-api:latest .
docker run --rm mgfisiobook-api:latest python --version
```

## Badges (Opcional)

Puedes agregar estos badges al README.md principal:

```markdown
![CI/CD](https://github.com/USERNAME/MGFisioBook/workflows/CI/CD%20Pipeline/badge.svg)
![Tests](https://github.com/USERNAME/MGFisioBook/workflows/CI/CD%20Pipeline/badge.svg?event=push)
[![codecov](https://codecov.io/gh/USERNAME/MGFisioBook/branch/main/graph/badge.svg)](https://codecov.io/gh/USERNAME/MGFisioBook)
```

## Mejoras Futuras

- [ ] Deploy automático a staging/producción
- [ ] Tests de integración con base de datos real
- [ ] Análisis de seguridad con Snyk o similar
- [ ] Notificaciones en Slack/Discord
- [ ] Cache de dependencias para builds más rápidos
- [ ] Matrix testing con múltiples versiones de Python
