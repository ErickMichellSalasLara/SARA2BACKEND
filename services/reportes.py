# Estadísticas
#Librerias de panda
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io

router = APIRouter()

@router.get("/reservas/excel")
def descargar_reporte_excel():
    try:
        datos_reporte = [
            {"ID": 1, "Usuario": "Ana López", "Cubículo": "Cubículo 01", "Fecha": "2026-08-01", "Estado": "Ocupado"},
            {"ID": 2, "Usuario": "Carlos Ruiz", "Cubículo": "Cubículo 02", "Fecha": "2026-08-01", "Estado": "Reservado"},
            {"ID": 3, "Usuario": "Mantenimiento", "Cubículo": "Cubículo 04", "Fecha": "2026-08-01", "Estado": "Mantenimiento"},
            {"ID": 4, "Usuario": "Luis Pérez", "Cubículo": "Cubículo 03", "Fecha": "2026-08-02", "Estado": "Reservado"}
        ]

        df = pd.DataFrame(datos_reporte)
        stream = io.BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Reservas_SARA")

        stream.seek(0)
        headers = {'Content-Disposition': 'attachment; filename="Reporte_Reservas_SARA.xlsx"'}

        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el reporte: {str(e)}")