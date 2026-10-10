import json
import sys
from pathlib import Path
from typing import Dict, Any

# Resolución limpia de ruta ejecutables de PyInstaller vs. entorno Python
if getattr(sys, "frozen", False):
    CARPETA_BASE = Path(sys.executable).parent
else:
    CARPETA_BASE = Path(__file__).resolve().parent

RUTA_JSON = CARPETA_BASE / "cronograma.json"
RUTA_CONFIG = CARPETA_BASE / "config_sistema.json"

COLOR_VACIO = ("#2A2B3C", "#45475A")
COLOR_VARIOS = ("#B45309", "#F59E0B")

CATEGORIAS: Dict[str, Dict[str, Any]] = {
    "Estudio": {
        "palabras": ["estudiar", "repasar", "tarea", "examen", "clase", "leer", "estudio", "progam", "programar", "programa"],
        "colores": ("#1E3A5F", "#3B82F6"),
    },
    "Trabajo": {
        "palabras": ["reunión", "trabajo", "proyecto", "entrega", "reunion"],
        "colores": ("#AC1B33", "#D30C1C"),
    },
    "Personal": {
        "palabras": ["gym", "ejercicio", "descanso", "comer", "entrenar", "ejercitar", "entreno"],
        "colores": ("#2A693D", "#2D702B"),
    },
    "Recreación": {
        "palabras": ["jugar", "juego", "película", "pelicula", "serie", "ocio", "recreacion", "recreación"],
        "colores": ("#5E1E47", "#AD1457"),
    },
}

DIAS_ESPANOL = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

CONFIG_POR_DEFECTO: Dict[str, Any] = {
    "tema": "Dark",
    "formato_hora": "24h",
    "notificaciones_activas": True,
    "cronograma_activo": "Principal",
    "cronogramas_lista": ["Principal"],
    "pestanas_abiertas": ["Principal"],
    "colores_pestanas": {},
    "mostrar_indicador_vacio": True,
    "categorias": {},
}

SUGERENCIAS_NOTAS = {
    "tarea": "{hora}: Organizar mis apuntes\n{hora_mas_25}: Análisis de datos y marco metodológico...",
    "ejercicio": "{hora}: Estiramiento y acondicionamiento / descansar\n{hora_mas_30}: Inicio de rutina principal...",
    "recreación": "{hora}: Dedicar a algún hobby/distraerme...",
    "general": "{hora}: Detalle o instrucción de la casilla...",
}

def cargar_configuracion() -> dict:
    """Carga las preferencias del sistema desde disco, aplicando valores por defecto si faltan."""
    cfg = CONFIG_POR_DEFECTO.copy()
    if RUTA_CONFIG.exists():
        try:
            with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
                contenido = json.load(f)
                if isinstance(contenido, dict):
                    cfg.update(contenido)
        except Exception as e:
            print(f"[Config Error]: {e}")

    return cfg


def guardar_configuracion(config_data: dict) -> None:
    """Almacena el diccionario de configuración actual en disco de forma segura."""
    try:
        with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[Config Guardar Error]: {e}")