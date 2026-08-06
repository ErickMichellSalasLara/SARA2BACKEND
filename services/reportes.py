import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter()

# ---------------------------------------------------------
# 1. Exportar a CSV (Generado en Memoria RAM)
# ---------------------------------------------------------
@router.get("/accesses/csv")
async def exportar_csv(inicio: Optional[str] = None, fin: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        query = text("SELECT * FROM vw_audit_records ORDER BY occurred_at DESC")
        registros = db.execute(query).mappings().all()

        # Creamos un archivo "virtual" en la memoria RAM
        stream = io.StringIO()
        writer = csv.writer(stream)

        # Escribimos los encabezados y los datos
        writer.writerow(["ID", "Administrador", "Acción", "Módulo", "Registro", "Fecha"])
        for reg in registros:
            writer.writerow([
                reg["id"],
                reg["administrator"],
                reg["action"],
                reg["module"],
                reg["record_label"],
                str(reg["occurred_at"])
            ])

        # Preparamos la respuesta para que el navegador inicie la descarga
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=Reporte_SARA.csv"
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 2. Exportar a Excel (Esqueleto para evitar 404)
# ---------------------------------------------------------
@router.get("/accesses/excel")
async def exportar_excel(inicio: Optional[str] = None, fin: Optional[str] = None, db: Session = Depends(get_db)):
    # Por ahora lanzamos un error 501 (No implementado) en vez de un 404
    raise HTTPException(status_code=501, detail="La exportación a Excel aún está en construcción.")

# ---------------------------------------------------------
# 3. Exportar a PDF (Esqueleto para evitar 404)
# ---------------------------------------------------------
@router.get("/accesses/pdf")
async def exportar_pdf(inicio: Optional[str] = None, fin: Optional[str] = None, db: Session = Depends(get_db)):
    # Por ahora lanzamos un error 501 (No implementado) en vez de un 404
    raise HTTPException(status_code=501, detail="La exportación a PDF aún está en construcción.")