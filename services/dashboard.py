from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

# NOTA: Quitamos el prefix aquí porque main.py ya le pone "/api/dashboard"
router = APIRouter(tags=["Dashboard"])

@router.get("/")
def vista_dashboard(db: Session = Depends(get_db)):
    # TARJETAS DE RESUMEN (MÉTRICAS) ---
    # Total de usuarios registrados[cite: 1]
    q_users = text("SELECT COUNT(*) FROM users")
    total_usuarios = db.execute(q_users).scalar() or 0

    # Préstamos activos o vencidos[cite: 1]
    q_loans = text("SELECT COUNT(*) FROM loans WHERE status IN ('active', 'overdue')")
    prestamos_activos = db.execute(q_loans).scalar() or 0

    # Reservas para el día de hoy[cite: 1]
    q_res = text("SELECT COUNT(*) FROM reservations WHERE reservation_date = CURDATE() AND status IN ('pending', 'confirmed', 'active')")
    reservas_hoy = db.execute(q_res).scalar() or 0

    metrics = [
        {"id": "users", "title": "Usuarios Registrados", "value": total_usuarios, "trend": "Base de datos actual"},
        {"id": "loans", "title": "Préstamos Activos", "value": prestamos_activos, "trend": "Requieren atención"},
        {"id": "rooms", "title": "Reservas de Hoy", "value": reservas_hoy, "trend": "Agendadas en sistema"}
    ]

    # GRÁFICA DE AFLUENCIA
    # Accesos concedidos hoy agrupados por hora[cite: 1]
    q_affluence = text("""
                       SELECT DATE_FORMAT(occurred_at, '%H:00') AS time, COUNT(*) AS visitors
                       FROM access_records
                       WHERE DATE(occurred_at) = CURDATE() AND movement = 'entry' AND result = 'granted'
                       GROUP BY HOUR(occurred_at)
                       """)
    affluence_rows = db.execute(q_affluence).fetchall()
    affluence = [{"time": row[0], "visitors": row[1]} for row in affluence_rows]

    # GRÁFICA DE OCUPACIÓN
    # Usamos tu vista de SQL para los cubículos[cite: 1]
    q_occ = text("SELECT name AS room, status FROM vw_cubicle_status")
    occ_rows = db.execute(q_occ).fetchall()
    occupancy = [{"room": row[0], "status": row[1]} for row in occ_rows]

    # ACTIVIDAD RECIENTE
    # Sacamos los últimos 5 registros de tu tabla de auditoría[cite: 1]
    q_act = text("SELECT id, record_label AS description, occurred_at AS time FROM vw_audit_records ORDER BY occurred_at DESC LIMIT 5")
    act_rows = db.execute(q_act).fetchall()
    activities = [{"id": row[0], "description": row[1], "time": str(row[2])} for row in act_rows]

    #ALERTAS
    # Alertas del sistema no resueltas[cite: 1]
    q_alerts = text("SELECT id, level AS type, description AS message FROM system_alerts WHERE is_resolved = FALSE ORDER BY created_at DESC")
    alert_rows = db.execute(q_alerts).fetchall()
    alerts = [{"id": row[0], "type": row[1], "message": row[2]} for row in alert_rows]

    # Construimos el JSON final para React
    return {
        "metrics": metrics,
        "affluence": affluence,
        "occupancy": occupancy,
        "activities": activities,
        "alerts": alerts
    }