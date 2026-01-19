# Tests - MGFisioBook

Este directorio contiene todos los tests automatizados del proyecto MGFisioBook.

## Estructura de Tests

### Tests de Integración (Routers)

- `test_appointments_comprehensive.py` - Tests completos del sistema de citas con control de acceso por roles
- `test_invoices_comprehensive.py` - Tests del sistema de facturas
- `test_patient_router.py` - Tests de endpoints de pacientes
- `test_routers_more_coverage.py` - Tests adicionales de cobertura de routers

### Tests de Servicio

- `test_patient_service.py` - Tests de lógica de negocio de pacientes
- `test_availability_service.py` - Tests de disponibilidad de terapeutas
- `test_push_notification_service.py` - Tests de notificaciones push

### Tests Funcionales

- `test_appointment_and_free_slots.py` - Tests de citas y slots libres
- `test_treatment_therapist_invoice_appointment.py` - Tests de flujo completo de tratamientos

### Tests de Configuración

- `conftest.py` - Fixtures y configuración compartida
- `test_smoke.py` - Tests básicos de smoke para verificar el arranque

## Tests Eliminados/Consolidados

Los siguientes archivos fueron eliminados por redundancia y sus tests fueron consolidados:

- `test_appointment_router_edges.py` → Consolidado en `test_appointments_comprehensive.py`
- `test_appointment_router_roles.py` → Consolidado en `test_appointments_comprehensive.py`
- `test_routers_appointments_and_device_token.py` → Funcionalidad en `test_appointments_comprehensive.py`
- `test_routers_appointments_and_invoices_extra.py` → Consolidado en `test_invoices_comprehensive.py`
- `test_invoice_router_more.py` → Consolidado en `test_invoices_comprehensive.py`

## Ejecutar Tests

### Todos los tests

```bash
pytest tests/ -v
```

### Con cobertura

```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Tests específicos

```bash
pytest tests/test_appointments_comprehensive.py -v
pytest tests/test_invoices_comprehensive.py -v
```

### Por marcadores

```bash
pytest tests/ -v -m asyncio
```

## Convenciones

1. **Nombres descriptivos**: Cada test debe tener un nombre que indique claramente qué está probando
2. **Docstrings**: Todos los tests tienen docstrings explicando su propósito
3. **Fixtures compartidas**: Se usan fixtures en `conftest.py` para evitar duplicación
4. **Helpers**: Funciones auxiliares para setup común están al inicio de cada archivo
5. **Assertions flexibles**: Los tests verifican múltiples status codes válidos para mayor robustez

## Cobertura

Los tests cubren:

- ✅ Control de acceso por roles (admin, therapist, patient)
- ✅ CRUD de todas las entidades
- ✅ Validación de conflictos de citas
- ✅ Sistema de notificaciones
- ✅ Generación de facturas
- ✅ Gestión de disponibilidad

## Base de Datos de Test

Los tests usan SQLite en memoria configurada en `conftest.py`:

- Base de datos limpia por sesión
- Fixtures async para operaciones de BD
- Rollback automático después de cada test
