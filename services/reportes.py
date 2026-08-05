from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
import csv
from openpyxl import Workbook
from fpdf import FPDF

router = APIRouter()

@router.get("/{modulo}/{formato}")
async def descargar_reporte(
        modulo: str,
        formato: str,
        inicio: str = Query(None),
        fin: str = Query(None)
):
    # --- LÓGICA PARA CSV ---
    if formato == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Modulo", "Fecha Inicio", "Fecha Fin", "Estado"])
        writer.writerow([modulo, inicio, fin, "Generado correctamente"])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=reporte_{modulo}.csv"}
        )

    # --- LÓGICA PARA EXCEL ---
    elif formato == "excel":
        output = io.BytesIO() # Usamos BytesIO porque Excel es un archivo binario
        wb = Workbook()
        ws = wb.active
        ws.title = f"Reporte {modulo.capitalize()}"

        # Agregamos encabezados y datos (luego aquí meterás los datos de tu BD)
        ws.append(["Modulo", "Fecha Inicio", "Fecha Fin", "Estado"])
        ws.append([modulo, inicio, fin, "Generado correctamente"])

        wb.save(output)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=reporte_{modulo}.xlsx"}
        )

    # --- LÓGICA PARA PDF ---
    elif formato == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Agregamos texto al PDF
        pdf.cell(200, 10, txt=f"S.A.R.A - Reporte de {modulo.capitalize()}", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Periodo: {inicio} al {fin}", ln=True, align='C')
        pdf.cell(200, 10, txt="Estado: Generado correctamente", ln=True, align='C')

        # Guardamos el PDF en memoria (FPDF lo saca como string, lo pasamos a bytes)
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        output = io.BytesIO(pdf_bytes)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=reporte_{modulo}.pdf"}
        )

    else:
        raise HTTPException(status_code=400, detail="Formato no soportado")