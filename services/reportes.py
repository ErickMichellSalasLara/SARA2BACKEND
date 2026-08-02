# Estadísticas
from fastapi import APIRouter
from schemas.dto import MetricasDashboard

# Creamos un "Router" para agrupar todas las rutas relacionadas al dashboard
router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard Administrativo"]
)

@router.get("/metricas", response_model=MetricasDashboard)
def obtener_metricas_mock():
    # Retornamos los datos falsos simulando una base de datos real
    return {
        "usuarios_dentro": 128,
        "accesos_hoy": 387,
        "cubiculos_ocupados": 8,
        "cubiculos_totales": 12,
        "prestamos_activos": 43,
        "prestamos_vencidos": 5,
        "ocupacion_porcentaje": 67,
        "afluencia_grafica": [10, 30, 80, 120, 95, 150, 110]
    }