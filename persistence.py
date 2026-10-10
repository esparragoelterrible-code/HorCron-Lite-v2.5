import json
from pathlib import Path

_CACHE_JSON = None
_RUTA_CACHE = None

def cargar_json_completo(ruta_json, forzar_recarga=False) -> dict:
    global _CACHE_JSON, _RUTA_CACHE
    ruta = Path(ruta_json)
    
    if not forzar_recarga and _CACHE_JSON is not None and _RUTA_CACHE == str(ruta):
        return _CACHE_JSON

    if ruta.exists():
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                _CACHE_JSON = json.load(f)
                _RUTA_CACHE = str(ruta)
                return _CACHE_JSON
        except Exception as e:
            print(f"[Error Cargar JSON]: {e}")
            return {}
    return {}

def guardar_cronograma_y_notas(ruta_json, cronograma_actual: str, entradas: dict, gestor_notas) -> None:
    global _CACHE_JSON
    ruta = Path(ruta_json)
    datos = cargar_json_completo(ruta)

    grilla_datos = {}
    for (dia, hora), casilla in entradas.items():
        contenido = casilla.get().strip()
        if contenido:
            grilla_datos[f"{dia}_{hora}"] = contenido

    datos[cronograma_actual] = grilla_datos

    if "_notas" not in datos:
        datos["_notas"] = {}
    if cronograma_actual not in datos["_notas"]:
        datos["_notas"][cronograma_actual] = {}

    key_celda, nota_txt = gestor_notas.obtener_nota_actual()
    if key_celda:
        if nota_txt:
            datos["_notas"][cronograma_actual][key_celda] = nota_txt
        elif key_celda in datos["_notas"][cronograma_actual]:
            del datos["_notas"][cronograma_actual][key_celda]

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
        
    _CACHE_JSON = datos

def cargar_datos_cronograma(ruta_json, cronograma_actual: str, entradas: dict) -> None:
    datos = cargar_json_completo(ruta_json)
    cronograma_datos = datos.get(cronograma_actual, {})

    for (dia, hora), casilla in entradas.items():
        casilla.delete(0, "end")
        clave = f"{dia}_{hora}"
        if clave in cronograma_datos:
            casilla.insert(0, cronograma_datos[clave])