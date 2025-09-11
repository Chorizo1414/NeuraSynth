# neurachord_api.py

# Importa las funciones necesarias de tus otros archivos
from generador_acordes import generar_progresion_acordes_smart, extraer_tonalidad
from generador_melodia import generar_melodia_sobre_acordes
from generos import detectar_estilo
import traceback

def generar_progresion(prompt: str, num_acordes: int = -1):
    """Genera una progresión de acordes a partir de un ``prompt``.

    Parameters
    ----------
    prompt: str
        Texto descriptivo que guía la generación.
    num_acordes: int, optional
        Número deseado de acordes; si se omite o es ``-1``, se genera una
        cantidad por defecto.

    Returns
    -------
    dict
        Diccionario con la progresión generada y metadatos.
    """
    try:
        if num_acordes == -1:
            num_acordes = None # generador_acordes usa None para "sin límite"

        estilo = detectar_estilo(prompt)
        raiz, modo = extraer_tonalidad(prompt)

        if not raiz: raiz = "C"
        if not modo: modo = "major"

        acordes, ritmo = generar_progresion_acordes_smart(raiz, modo, estilo, num_acordes)

        return {
            "acordes": acordes if acordes else [],
            "ritmo": ritmo if ritmo else [],
            "raiz": raiz,
            "modo": modo,
            "estilo": estilo,
            "error": ""
        }
    except Exception as e:
        # Devolver un mensaje de error claro a C++ si algo falla
        error_message = f"Error en generar_progresion: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": error_message}


def generar_melodia(acordes, ritmo, raiz, modo, bpm):
    """
    Función que C++ llamará para obtener la melodía.
    """
    try:
        melodia = generar_melodia_sobre_acordes(acordes, ritmo, raiz, modo, bpm=bpm)
        return {
            "melodia": melodia if melodia else [],
            "error": ""
        }
    except Exception as e:
        error_message = f"Error en generar_melodia: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": error_message}