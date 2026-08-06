# Base de datos S.A.R.A.

`database/sara_database.sql` crea el esquema de desarrollo para MySQL 8.0, los triggers, procedimientos, vistas y datos iniciales utilizados por FastAPI.

## Reglas incluidas

- Cubículos: América, Oceanía, Europa y Asia.
- Servicio de lunes a viernes, de 07:30 a 16:00.
- Duración máxima inicial de reserva: 90 minutos.
- Prevención de reservaciones traslapadas.
- Validación de usuarios activos, capacidad, mantenimiento y días festivos.
- Contraseñas almacenadas como PBKDF2-SHA256.
- Préstamos que actualizan automáticamente el estado de los materiales.
- Auditoría y alertas administrativas.

## Importación

Desde MySQL Workbench abre `sara_database.sql` y ejecútalo completo, o utiliza:

```powershell
mysql -u root -p < database/sara_database.sql
```

Después comprueba la conexión mediante:

```text
GET http://127.0.0.1:8000/api/health/database
```

> El script elimina y vuelve a crear `sara_db`. No lo uses como migración sobre una base con datos reales.

## Base administrada o Railway

Para instalar en una base vacía ya creada por el proveedor, utiliza:

```text
database/sara_schema_current_database.sql
```

Ese archivo no ejecuta `DROP DATABASE`, `CREATE DATABASE` ni `USE`; crea el esquema en la base seleccionada por la conexión. No lo ejecutes sobre tablas existentes sin una copia de seguridad.
