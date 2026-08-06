# Revisión y corrección de S.A.R.A.

Se revisaron los archivos entregados del frontend `SARA2` y del backend `SARA2BACKEND` y se prepararon dos versiones corregidas listas para sustituir el contenido de las ramas correspondientes.

## Hallazgos principales

### Frontend

- Credenciales temporales y tokens falsos dentro de React.
- Rutas protegidas que confiaban en el rol guardado en el navegador.
- Registro con una variable `email` no definida.
- URLs de Railway repetidas en distintos componentes.
- Datos mock activados como comportamiento predeterminado.
- Módulos administrativos que solo modificaban `useState` y perdían datos al recargar.
- Inconsistencias entre cuatro cubículos y referencias anteriores a África/12 cubículos.
- Horarios distintos al institucional de 07:30 a 16:00.
- Enlaces de términos y privacidad sin páginas de destino.
- `.env` no estaba excluido explícitamente de Git.

### Backend

- Una credencial real de MySQL/Railway estaba escrita en el código fuente.
- Login administrativo fijo, contraseña fija y token simulado.
- Falta de autorización real por rol en los endpoints.
- DTO inválido y contratos diferentes a los que esperaba React.
- Dependencia obligatoria de credenciales de Google Calendar para iniciar módulos.
- Ausencia de endpoints completos para la mayoría de módulos del frontend.
- Script SQL con datos de materiales incompatibles con el trigger de préstamos.

## Correcciones realizadas

- Comunicación centralizada `React → FastAPI → MySQL`.
- Autenticación PBKDF2-SHA256 y JWT HMAC-SHA256.
- Verificación de sesión en `/api/auth/me`.
- Autorización administrativa en FastAPI.
- APIs reales para dashboard, cubículos, reservas, usuarios, préstamos, accesos, auditoría, configuración, calendario y reportes.
- Cuatro cubículos oficiales: América, Oceanía, Europa y Asia.
- Reglas de reservas de 07:30 a 16:00, máximo configurable, días hábiles, capacidad, mantenimiento, cierres y traslapes.
- Datos reales como modo predeterminado; mocks únicamente por variable de entorno.
- Proxy de Vite y cliente de API configurable.
- Fechas locales corregidas en formularios y reportes.
- Script MySQL completo con vistas, triggers y datos iniciales coherentes.
- Documentación y archivos `.env.example` actualizados.

## Verificaciones realizadas

- Compilación sintáctica de todos los archivos Python.
- Importación de la aplicación FastAPI y prueba básica de `/`, `/mensaje` y `/api/health`.
- Pruebas de creación/validación de JWT.
- Pruebas de hash y verificación de contraseñas PBKDF2-SHA256.
- ESLint del frontend sin advertencias.
- Análisis sintáctico de todos los archivos JS/JSX.
- Resolución de todas las importaciones relativas del frontend.
- Revisión de rutas API del frontend frente a los endpoints del backend.
- Búsqueda de secretos, URLs productivas codificadas, marcadores de conflicto y datos incongruentes.

## Límites de la verificación

- No había un servidor MySQL disponible en el entorno de revisión, por lo que el script no se ejecutó contra MySQL real.
- La compilación de producción de Vite no pudo completarse en este contenedor porque los `node_modules` entregados fueron instalados en Windows y no incluían el binario nativo de Rolldown para Linux. El ZIP corregido no incluye `node_modules`; debes ejecutar `npm install` en tu equipo.
- El envío de correos y el restablecimiento final de contraseña todavía requieren SMTP y una pantalla de nueva contraseña.
- La integración física con lectores RFID/ESP32 requiere los dispositivos y sus credenciales.

## Acción urgente

La contraseña de la base que apareció en el backend original debe considerarse comprometida. Rótala en Railway/MySQL y elimina el secreto del historial del repositorio antes de volver a desplegar.
