# Cubículos
from fastapi import APIRouter, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
import httpx
import os
import json

router = APIRouter()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'c_0897fb421b1c7095121077b97e2bba9b8aa9c5d1b4775f68493ffa5d2bfea268@group.calendar.google.com'

@router.get("/dias-festivos")
async def obtener_dias_festivos(anio: int = 2026):
    url_api_externa = f"https://date.nager.at/api/v3/PublicHolidays/{anio}/MX"
    async with httpx.AsyncClient() as client:
        respuesta = await client.get(url_api_externa)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            festivos_limpios = [{"fecha": dia["date"], "motivo": dia["localName"]} for dia in datos]
            return {"festivos": festivos_limpios}
        raise HTTPException(status_code=respuesta.status_code, detail="Error conectando externos.")

@router.get("/eventos")
def obtener_reservas():
    try:
        # LÓGICA DE CREDENCIALES (NUBE VS LOCAL)
        google_creds_env = os.getenv("GOOGLE_CREDENTIALS")

        if google_creds_env:
            # Si estamos en Railway, leemos la variable de entorno
            creds_dict = json.loads(google_creds_env)
            creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            # Si estamos en tu computadora local, leemos el archivo
            creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)

        servicio = build('calendar', 'v3', credentials=creds)
        eventos_resultado = servicio.events().list(
            calendarId=CALENDAR_ID, maxResults=10, singleEvents=True, orderBy='startTime'
        ).execute()

        eventos = eventos_resultado.get('items', [])
        return {"mensaje": "Conexión exitosa", "eventos": eventos}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando con Google Calendar: {str(e)}")