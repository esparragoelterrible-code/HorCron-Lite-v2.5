from typing import Tuple
from config import CATEGORIAS, COLOR_VACIO, COLOR_VARIOS

try:
    from thefuzz import fuzz
    FUZZ_DISPONIBLE = True
except ImportError:
    FUZZ_DISPONIBLE = False

def obtener_color_por_categoria(texto: str) -> Tuple[str, str]:
    """Determina la paleta de colores de una celda mediante búsqueda directa y Fuzzy Matching."""
    texto_limpio = texto.strip().lower()

    if not texto_limpio:
        return COLOR_VACIO

    # 1. Búsqueda directa por palabras clave exactas o contenidas
    for cat_info in CATEGORIAS.values():
        for palabra_clave in cat_info["palabras"]:
            if palabra_clave in texto_limpio:
                colores = cat_info["colores"]
                return colores if isinstance(colores, (list, tuple)) else (colores, colores)

    # 2. Coincidencia difusa (Fuzzy Matching) para tolerar pequeños typos)
    if FUZZ_DISPONIBLE:
        for cat_info in CATEGORIAS.values():
            for palabra_clave in cat_info["palabras"]:
                if fuzz.partial_ratio(palabra_clave, texto_limpio) >= 85:
                    colores = cat_info["colores"]
                    return colores if isinstance(colores, (list, tuple)) else (colores, colores)

    return COLOR_VARIOS