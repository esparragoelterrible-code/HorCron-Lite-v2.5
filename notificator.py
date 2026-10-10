from datetime import datetime
from config import DIAS_ESPANOL, RUTA_JSON, RUTA_CONFIG
from persistence import cargar_json_completo

try:
    from plyer import notification
    PLYER_DISPONIBLE = True
except ImportError:
    PLYER_DISPONIBLE = False

ultima_notificacion = ""

def enviar_notificacion(titulo: str, mensaje: str) -> None:
    if not PLYER_DISPONIBLE:
        return
    try:
        notification.notify(
            title=titulo,
            message=mensaje,
            app_name="Cronograma",
            timeout=5
        )
    except Exception as e:
        print(f"[Notificación Error]: {e}")


def verificar_horario() -> None:
    global ultima_notificacion

    if not RUTA_CONFIG.exists() or not RUTA_JSON.exists():
        return

    try:
        # 1. Leer estado de configuración desde la caché
        cfg = cargar_json_completo(RUTA_CONFIG)
        if not cfg.get("notificaciones_activas", True):
            return

        cronograma_activo = cfg.get("cronograma_activo", "Principal")

        # 2. Evaluar tiempo actual
        ahora = datetime.now()
        dia_actual = DIAS_ESPANOL[ahora.weekday()]
        hora_actual = ahora.strftime("%H:00")
        minuto_actual = ahora.minute
        clave_actual = f"{dia_actual}_{hora_actual}"

        if minuto_actual <= 2 and clave_actual != ultima_notificacion:
            datos = cargar_json_completo(RUTA_JSON)

            tareas_activas = datos.get(cronograma_activo, {})
            actividad = tareas_activas.get(clave_actual, "").strip()

            if actividad:
                enviar_notificacion(
                    f"⏰ Hora de: {actividad}",
                    f"Tienes programado '{actividad}' para hoy {dia_actual} a las {hora_actual}."
                )

            # Se marca como evaluada para la hora en curso
            ultima_notificacion = clave_actual

    except Exception as e:
        print(f"[Rutina Notificación Error]: {e}")