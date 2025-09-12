# neurachord_api.py (VERSIÓN FUNCIONAL)
import traceback

# Importamos las funciones clave de tus otros módulos
from generos import detectar_estilo
from generador_acordes import (
    extraer_tonalidad,
    generar_progresion_acordes_smart,
    INFO_GENERO, # Necesario para la lógica de inferencia
    MAPEO_GENERO_BPM # Asumiendo que MAPEO_GENERO_BPM está en generador_acordes
)
from generador_melodia import generar_melodia_sobre_acordes
from procesador_sentimientos import detectar_sentimiento_en_prompt, inferir_parametros_desde_sentimiento

def generar_progresion(prompt: str, num_acordes: int = -1):
    """
    Función principal para generar acordes desde JUCE.
    Toma un prompt y devuelve un diccionario con la progresión y metadatos.
    """
    try:
        print(f">>> Python API: Recibido prompt: '{prompt}'")

        # 1. Detección inicial (similar a como lo hace main.py)
        estilo_explicito = detectar_estilo(prompt)
        raiz_explicita, modo_explicito = extraer_tonalidad(prompt, estilo_detectado_param=estilo_explicito)
        sentimiento_detectado = detectar_sentimiento_en_prompt(prompt)

        # 2. Inferencia de parámetros
        # Obtenemos los géneros entrenados para pasarlos a la función de inferencia
        generos_entrenados_reales = {
            g for g in INFO_GENERO.keys()
            if g != "patrones_ritmicos" and isinstance(INFO_GENERO.get(g), dict) and
            any(INFO_GENERO[g].get(k) for k in INFO_GENERO[g] if k != "patrones_ritmicos")
        }
        
        estilo_final, raiz_final, modo_final = inferir_parametros_desde_sentimiento(
            sentimiento_detectado,
            estilo_explicito,
            raiz_explicita,
            modo_explicito,
            generos_entrenados_reales
        )

        # 3. Verificación y Fallback
        if not estilo_final or estilo_final == "normal" or not INFO_GENERO.get(estilo_final):
             error_msg = f"Genero no encontrado o sin datos suficientes: '{estilo_explicito or prompt.split()[0]}'"
             print(f"!!! Python API Error: {error_msg}")
             return {"error": error_msg}

        if not raiz_final: raiz_final = "C"
        if not modo_final: modo_final = "major"

        print(f">>> Python API: Parámetros inferidos -> Estilo: {estilo_final}, Tonalidad: {raiz_final} {modo_final}")

        # Si el usuario no especificó un número de acordes, lo dejamos en None (sin límite)
        cantidad_acordes_seleccionada = num_acordes if num_acordes > 0 else None

        # 4. Generación de acordes
        acordes_generados, ritmo_obtenido = generar_progresion_acordes_smart(
            raiz_final,
            modo_final,
            estilo_final,
            cantidad_acordes_seleccionada
        )

        if not acordes_generados:
            return {"error": "No se pudieron generar acordes con los parámetros dados."}

        # 5. Devolver el resultado en el formato esperado por JUCE
        return {
            "acordes": acordes_generados,
            "ritmo": ritmo_obtenido,
            "raiz": raiz_final,
            "modo": modo_final,
            "estilo": estilo_final,
            "error": ""
        }

    except Exception as e:
        error_message = f"Error en generar_progresion: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": error_message}


def generar_melodia(acordes, ritmo, raiz, modo, bpm):
    """
    Función principal para generar melodías desde JUCE.
    """
    try:
        print(f">>> Python API: Generando melodía para {raiz} {modo} a {bpm} BPM.")
        
        # Llama a tu función real de generación de melodía
        melodia_generada = generar_melodia_sobre_acordes(
            acordes_progresion=acordes,
            ritmo_acordes=ritmo,
            raiz_tonalidad=raiz,
            modo_tonalidad=modo,
            bpm=bpm
        )

        if not melodia_generada:
            return {"error": "No se pudo generar la melodía."}
            
        return {
            "melodia": melodia_generada,
            "error": ""
        }
    except Exception as e:
        error_message = f"Error en generar_melodia: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": error_message}