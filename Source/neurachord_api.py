# neurachord_api.py (VERSIÓN FUNCIONAL)
import traceback
import os
from music21 import stream, note, chord, instrument, tempo, midi
from generador_acordes import transponer_progresion

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
    Ahora también devuelve el BPM sugerido para el género.
    """
    try:
        print(f">>> Python API: Recibido prompt: '{prompt}'")

        # ... (Toda la lógica de detección y de inferencia de parámetros se queda igual) ...
        estilo_explicito = detectar_estilo(prompt)
        raiz_explicita, modo_explicito = extraer_tonalidad(prompt, estilo_detectado_param=estilo_explicito)
        sentimiento_detectado = detectar_sentimiento_en_prompt(prompt)
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

        if not estilo_final or estilo_final == "normal" or not INFO_GENERO.get(estilo_final):
             error_msg = f"Genero no encontrado o sin datos suficientes: '{estilo_explicito or prompt.split()[0]}'"
             print(f"!!! Python API Error: {error_msg}")
             return {"error": error_msg}

        if not raiz_final: raiz_final = "C"
        if not modo_final: modo_final = "major"

        print(f">>> Python API: Parámetros inferidos -> Estilo: {estilo_final}, Tonalidad: {raiz_final} {modo_final}")

        cantidad_acordes_seleccionada = num_acordes if num_acordes > 0 else None

        acordes_generados, ritmo_obtenido = generar_progresion_acordes_smart(
            raiz_final,
            modo_final,
            estilo_final,
            cantidad_acordes_seleccionada
        )

        if not acordes_generados:
            return {"error": "No se pudieron generar acordes con los parámetros dados."}

        # --- NUEVA LÓGICA DE BPM ---
        # Buscamos el BPM sugerido del diccionario MAPEO_GENERO_BPM
        # El [2] corresponde al valor "default_bpm_sugerido" en la tupla
        bpm_sugerido = MAPEO_GENERO_BPM.get(estilo_final, MAPEO_GENERO_BPM["normal"])[2]
        
        # Devolvemos el resultado incluyendo el BPM
        return {
            "acordes": acordes_generados,
            "ritmo": ritmo_obtenido,
            "raiz": raiz_final,
            "modo": modo_final,
            "estilo": estilo_final,
            "bpm": bpm_sugerido,  # <--- BPM AÑADIDO
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
    """Función auxiliar que ahora SOBREESCRIBE el archivo MIDI."""
    try:
        os.makedirs(CARPETA_MIDI_EXPORTADO_PLUGIN, exist_ok=True)
        
        # Ya no creamos nombres únicos. Siempre usamos el mismo.
        nombre_final = f"{nombre_archivo_base}.mid"
        ruta_completa = os.path.join(CARPETA_MIDI_EXPORTADO_PLUGIN, nombre_final)
            
        mf = midi.translate.streamToMidiFile(stream_obj)
        # El modo "wb" (write binary) automáticamente sobrescribe el archivo si ya existe.
        mf.open(ruta_completa, "wb")
        mf.write()
        mf.close()
        print(f">>> Python API: Archivo MIDI sobreescrito en {ruta_completa}")
        return {"ruta": ruta_completa, "error": ""}
    except Exception as e:
        error_msg = f"Error al exportar MIDI: {e}\n{traceback.format_exc()}"
        print(f"!!! Python API Error: {error_msg}")
        return {"error": error_msg}


def exportar_acordes_midi(acordes, ritmo, bpm):
    s = stream.Stream()
    s.insert(0, tempo.MetronomeMark(number=bpm))
    s.append(instrument.Piano())
    
    offset_actual = 0.0
    for i, ac_data in enumerate(acordes):
        duracion = float(ritmo[i])
        if isinstance(ac_data, list):
            acorde_obj = chord.Chord(ac_data, quarterLength=duracion)
            s.insert(offset_actual, acorde_obj)
        offset_actual += duracion
        
    # Usamos un nombre de archivo base simple: "acordes"
    return _exportar_a_midi(s, "acordes")


def exportar_melodia_midi(melodia, bpm):
    s = stream.Stream()
    s.insert(0, tempo.MetronomeMark(number=bpm))
    s.append(instrument.Violin())
    
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

    return _exportar_a_midi(s, "melodia")

def transponer_musica(datos_musica, semitonos):
    """
    Toma un diccionario de datos musicales y lo transpone por un número de semitonos.
    """
    try:
        acordes = datos_musica.get("acordes", [])
        melodia = datos_musica.get("melodia", []) # Maneja el caso de que aún no haya melodía

        # Llamamos a la función de transposición que ya existe en tu código
        acordes_transpuestos, melodia_transpuesta = transponer_progresion(acordes, semitonos, melodia)

        # Creamos un nuevo diccionario con los datos actualizados
        nuevos_datos = datos_musica.copy()
        nuevos_datos["acordes"] = acordes_transpuestos
        nuevos_datos["melodia"] = melodia_transpuesta
        # La siguiente línea es la que tienes que añadir
        nuevos_datos["progresion_str"] = datos_musica.get("progresion_str", "")
        nuevos_datos["error"] = ""

        print(f">>> Python API: Música transpuesta por {semitonos} semitonos.")
        return nuevos_datos

    except Exception as e:
        error_msg = f"Error al transponer: {e}\\n{traceback.format_exc()}"
        print(f"!!! Python API Error: {error_msg}")
        return {"error": error_msg}