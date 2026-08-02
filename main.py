from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 1. Inicializar la aplicación
app = FastAPI(title="S.A.R.A. Backend")

# 2. Configurar CORS para permitir que React (Frontend) se comunique
# Ajusta el puerto 3000 si tu React corre en otro distinto
origenes_permitidos = [
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Permite todos los headers
)

# --- MODELOS DE DATOS (PYDANTIC) ---
# Esto define la estructura exacta que esperamos recibir de Reactl. PYDANTIC valida los json recibidos
class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

# --- ENDPOINTS ---
@app.get("/")
def ruta_principal():
    return {"mensaje": "¡Bienvenido a la API de S.A.R.A!"}

# Nuevo endpoint de Login
@app.post("/api/auth/login")
def login(request: LoginRequest):
    # SIMULACIÓN DE BASE DE DATOS:
    # Por ahora hardcodeamos un usuario administrador válido para probar
    if request.email == "admin@utr.edu.mx" and request.password == "admin12345":
        # Respuesta exitosa que espera tu React
        return {
            "token": "token_simulado_12345_sara",
            "user": {
                "name": "Administrador Principal",
                "role": "admin"
            }
        }

    # Si las credenciales no coinciden, lanzamos un error 401 (No autorizado)
    # Tu bloque catch en React capturará el "detail"
    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")

# --- CALENDARIO Y RESERVAS ---

@app.get("/api/calendario/dias-festivos")
async def obtener_dias_festivos(anio: int = 2026):
    """
    Consume la API pública y gratuita de Nager.Date.
    Devuelve los días festivos oficiales de México (MX) para el año solicitado.
    """
    url_api_externa = f"https://date.nager.at/api/v3/PublicHolidays/{anio}/MX"

    # Hacemos la petición asíncrona a la API externa
    async with httpx.AsyncClient() as client:
        respuesta = await client.get(url_api_externa)

        # Si la API externa responde bien, pasamos los datos a tu React
        if respuesta.status_code == 200:
            datos = respuesta.json()
            # Filtramos solo lo que nos importa (fecha y nombre del festivo)
            festivos_limpios = [{"fecha": dia["date"], "motivo": dia["localName"]} for dia in datos]
            return {"festivos": festivos_limpios}

        # Si la API externa falla, lanzamos un error controlado
        raise HTTPException(
            status_code=respuesta.status_code,
            detail="Error al conectar con el servidor de calendarios externos."
        )

    # --- GOOGLE CALENDAR API ---
# Definimos qué permisos queremos (en este caso, control total del calendario)
SCOPES = ['https://www.googleapis.com/auth/calendar']
# El ID del calendario que copiaste en el Paso 1
CALENDAR_ID = 'c_0897fb421b1c7095121077b97e2bba9b8aa9c5d1b4775f68493ffa5d2bfea268@group.calendar.google.com'

@app.get("/api/calendario/eventos")
def obtener_reservas():
    try:
        # 1. Cargamos las credenciales de tu archivo ignorado por Git
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)

        # 2. Construimos el servicio de conexión a la API v3 de Google
        servicio = build('calendar', 'v3', credentials=creds)

        # 3. Pedimos los próximos 10 eventos de tu calendario
        eventos_resultado = servicio.events().list(
            calendarId=CALENDAR_ID,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        eventos = eventos_resultado.get('items', [])

        return {"mensaje": "Conexión exitosa", "eventos": eventos}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando con Google Calendar: {str(e)}")