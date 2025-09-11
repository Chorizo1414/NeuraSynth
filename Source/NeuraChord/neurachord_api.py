# neurachord_api.py (VERSIÓN DE PRUEBA)
import traceback

def generar_progresion(prompt: str, num_acordes: int = -1):
    """
    Función de prueba que no depende de otros archivos.
    """
    try:
        # Este print aparecerá en la consola de sistema, no en la de Visual Studio
        print(">>> Python: generar_progresion FUE LLAMADA con el prompt:", prompt)

        # Devolvemos datos falsos para confirmar que la comunicación funciona
        return {
            "acordes": ["C", "G", "Am", "F"],
            "ritmo": [1.0, 1.0, 1.0, 1.0],
            "raiz": "C",
            "modo": "major",
            "estilo": "pop de prueba",
            "error": ""
        }
    except Exception as e:
        error_message = f"Error en generar_progresion (prueba): {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": error_message}

def generar_melodia(acordes, ritmo, raiz, modo, bpm):
    """
    Función de prueba.
    """
    return {
        "melodia": [],
        "error": ""
    }