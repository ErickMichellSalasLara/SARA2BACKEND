# S.A.R.A. Backend

API FastAPI para la plataforma S.A.R.A., conectada a MySQL 8.0.

## Correcciones principales

- Eliminadas las credenciales de MySQL escritas directamente en el código.
- Inicio de sesión real contra `users`, con contraseñas PBKDF2-SHA256.
- Tokens JWT firmados, con expiración y validación de usuario activo.
- Permisos administrativos verificados en el servidor, no en `localStorage`.
- Endpoints para autenticación, dashboard, cubículos, reservas, usuarios, préstamos, accesos, auditoría, configuración, calendario y reportes.
- Reservas restringidas a América, Oceanía, Europa y Asia.
- Horario obligatorio de 07:30 a 16:00, sin traslapes y con validación de capacidad, mantenimiento, días hábiles y cierres institucionales.
- Calendario respaldado por MySQL; Google Calendar ya no es obligatorio para iniciar la API.
- Reportes CSV, Excel y PDF generados desde datos reales.
- Script SQL corregido para que los datos iniciales respeten los triggers de préstamos.

## 1. Crear la base de datos

Ejecuta `database/sara_database.sql` en MySQL 8.0.

El script crea los cuatro cubículos oficiales:

- América
- Oceanía
- Europa
- Asia

> **Advertencia:** el script comienza con `DROP DATABASE IF EXISTS sara_db`. Úsalo para una instalación limpia de desarrollo; no lo ejecutes sobre una base de producción con información que necesites conservar.

Para una base vacía ya creada por Railway u otro proveedor, usa `database/sara_schema_current_database.sql`, que instala las tablas en la base seleccionada sin eliminarla.

## 2. Variables de entorno

Copia `.env.example` como `.env` y completa los valores:

```env
ENVIRONMENT=development
DATABASE_URL=mysql+pymysql://root:TU_CONTRASENA@127.0.0.1:3306/sara_db
DATABASE_TIMEZONE=-06:00
JWT_SECRET=una-clave-muy-larga-y-aleatoria
ACCESS_TOKEN_MINUTES=120
ALLOWED_EMAIL_DOMAIN=@utr.edu.mx
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

También se acepta `MYSQL_URL` cuando el proveedor la entrega con ese nombre. En producción usa `ENVIRONMENT=production`; la aplicación rechazará la clave JWT predeterminada.

No subas `.env` al repositorio.

## 3. Ejecutar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Estado de la API: `http://127.0.0.1:8000/api/health`
- Prueba de MySQL: `http://127.0.0.1:8000/api/health/database`

## Endpoints principales

```text
POST  /api/auth/login
POST  /api/auth/register
GET   /api/auth/me
POST  /api/auth/forgot-password

GET   /api/cubicles/status
GET   /api/dashboard/summary
GET   /api/reservations
POST  /api/reservations
PATCH /api/reservations/{id}/cancel

GET   /api/accesos/historial
GET   /api/prestamos/historial
GET   /api/prestamos/catalogos
POST  /api/prestamos/registrar
PUT   /api/prestamos/devolver/{id}
PUT   /api/prestamos/renovar/{id}

GET   /api/usuarios
POST  /api/usuarios
PATCH /api/usuarios/{id}/status
GET   /api/auditoria/historial
GET   /api/configuracion
PUT   /api/configuracion
GET   /api/reportes/{tipo}/{formato}
```

## Cuentas de demostración

Se crean al ejecutar el script SQL:

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@utr.edu.mx` | `Admin123` |
| Estudiante | `alumno@utr.edu.mx` | `Alumno123` |

Cambia o elimina estas cuentas antes de publicar un entorno real.

## Recuperación de contraseña

`POST /api/auth/forgot-password` crea un token temporal cifrado en la base y no revela si el correo existe. Aún falta integrar un proveedor SMTP y una pantalla para consumir el token y establecer una contraseña nueva.

## Seguridad crítica

La versión original contenía una URL de MySQL con credenciales en `database.py`. Aunque se haya eliminado del código corregido, debes:

1. Rotar inmediatamente la contraseña de MySQL/Railway.
2. Actualizar `DATABASE_URL` o `MYSQL_URL` con la nueva credencial.
3. Eliminar el secreto del historial de Git, no solo del último commit.
4. Revisar los registros del proveedor por accesos no reconocidos.
