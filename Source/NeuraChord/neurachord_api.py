# neurachord_api.py (VERSIÓN FUNCIONAL)
import traceback
import os
from music21 import stream, note, chord, instrument, tempo, midi

# Definimos una ruta de exportación fija para el plugin
RUTA_BASE_PLUGIN = os.path.dirname(os.path.abspath(__file__))
CARPETA_MIDI_EXPORTADO_PLUGIN = os.path.join(RUTA_BASE_PLUGIN, "MIDI_EXPORTADO_PLUGIN")

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

def get_available_genres():
    """
    Devuelve una lista con los nombres de todos los géneros entrenados
    que se encuentran en los archivos de estilo.
    """
    try:
        # INFO_GENERO se importa desde generador_acordes y ya contiene todo
        from generador_acordes import INFO_GENERO
        if not INFO_GENERO:
            return []
        
        # Filtramos para quedarnos solo con las claves que son diccionarios de géneros
        genres = [
            genre for genre in INFO_GENERO.keys()
            if isinstance(INFO_GENERO[genre], dict) and "patrones_ritmicos" in INFO_GENERO[genre]
        ]
        return sorted(genres)
    except Exception as e:
        print(f"!!! Python API Error al obtener géneros: {e}")
        return []

def _exportar_a_midi(stream_obj, nombre_archivo_base):
    """Función auxiliar para guardar un stream de music21 como archivo MIDI."""
    try:
        os.makedirs(CARPETA_MIDI_EXPORTADO_PLUGIN, exist_ok=True)
        
        # Creamos un nombre de archivo único para no sobrescribir
        i = 1
        nombre_final = f"{nombre_archivo_base}.mid"
        ruta_completa = os.path.join(CARPETA_MIDI_EXPORTADO_PLUGIN, nombre_final)
        while os.path.exists(ruta_completa):
            nombre_final = f"{nombre_archivo_base}_{i}.mid"
            ruta_completa = os.path.join(CARPETA_MIDI_EXPORTADO_PLUGIN, nombre_final)
            i += 1
            
        mf = midi.translate.streamToMidiFile(stream_obj)
        mf.open(ruta_completa, "wb")
        mf.write()
        mf.close()
        print(f">>> Python API: Archivo exportado con éxito a {ruta_completa}")
        return {"ruta": ruta_completa, "error": ""}
    except Exception as e:
        error_msg = f"Error al exportar MIDI: {e}\n{traceback.format_exc()}"
        print(f"!!! Python API Error: {error_msg}")
        return {"error": error_msg}


def exportar_acordes_midi(acordes, ritmo, bpm):
    s = stream.Stream()
    s.insert(0, tempo.MetronomeMark(number=bpm))
    s.append(instrument.Piano()) # Instrumento por defecto para acordes
    
    offset_actual = 0.0
    for i, ac_data in enumerate(acordes):
        duracion = float(ritmo[i])
        if isinstance(ac_data, list):
            acorde_obj = chord.Chord(ac_data, quarterLength=duracion)
            s.insert(offset_actual, acorde_obj)
        # Ignoramos los silencios ("0") en la exportación
        offset_actual += duracion
        
    return _exportar_a_midi(s, "acordes_exportados")


def exportar_melodia_midi(melodia, bpm):
    s = stream.Stream()
    s.insert(0, tempo.MetronomeMark(number=bpm))
    s.append(instrument.Violin()) # Instrumento por defecto para melodía
    
    offset_actual = 0.0
    for nota_data in melodia:
        nombre_nota = nota_data[0]
        duracion = float(nota_data[1])
        
        if nombre_nota == "0":
            elemento = note.Rest(quarterLength=duracion)
        else:
            elemento = note.Note(nombre_nota, quarterLength=duracion)
        
        s.insert(offset_actual, elemento)
        offset_actual += duracion

    return _exportar_a_midi(s, "melodia_exportada")