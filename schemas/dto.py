from pydantic import BaseModel
from typing import List

# Definimos la estructura exacta que tu Dashboard de React necesita
class MetricasDashboard(BaseModel):
    usuarios_dentro: int
    accesos_hoy: int
    cubiculos_ocupados: int
    cubiculos_totales: int
    prestamos_activos: int
    prestamos_vencidos: int
    ocupacion_porcentaje: int
    afluencia_grafica: List[int] # Lista de números para dibujar los picos en tu gráfica