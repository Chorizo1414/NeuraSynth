# neurachord_api.py (VERSIÓN FUNCIONAL)
import traceback
import os
import json
from music21 import stream, note, chord, instrument, tempo, midi, pitch
from generador_acordes import transponer_progresion
from sound_designer import generate_synth_patch
from sound_prompt_processor import parse_sound_prompt
import appdirs

# Definimos una ruta de exportación fija para el plugin
RUTA_BASE_PLUGIN = os.path.dirname(os.path.abspath(__file__))
CARPETA_MIDI_EXPORTADO_PLUGIN = os.path.join(RUTA_BASE_PLUGIN, "MIDI_EXPORTADO_PLUGIN")

# RUTA_BASE_PLUGIN = os.path.dirname(os.path.abspath(__file__)) # Comentado o eliminado
# CARPETA_MIDI_EXPORTADO_PLUGIN = os.path.join(RUTA_BASE_PLUGIN, "MIDI_EXPORTADO_PLUGIN") # Comentado o eliminado

# --- NUEVAS RUTAS DE USUARIO ---
APP_NAME = "NeuraSynth"
APP_AUTHOR = "Chorizo1414" # Puedes cambiar esto si quieres

# Obtiene la carpeta de datos de usuario específica de la aplicación (AppData\Roaming\...)
USER_DATA_DIR = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
# Crea la carpeta si no existe
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Define las subcarpetas dentro de los datos de usuario
CARPETA_MIDI_EXPORTADO_PLUGIN = os.path.join(USER_DATA_DIR, "MIDI_Exportado")
os.makedirs(CARPETA_MIDI_EXPORTADO_PLUGIN, exist_ok=True) # Crea la carpeta MIDI también

RUTA_LEARNED_SOUNDS = os.path.join(USER_DATA_DIR, 'learned_sounds.json')
# --- FIN NUEVAS RUTAS ---

last_generated_patch = None

# Importamos las funciones clave de tus otros módulos
from generos import detectar_estilo
from generador_acordes import (
    extraer_tonalidad,
    generar_progresion_acordes_smart,
    INFO_GENERO,
    MAPEO_GENERO_BPM,
    # --- ¡ESTAS LÍNEAS AHORA FUNCIONARÁN! ---
    puntuar_acordes_positivamente,
    puntuar_acordes_negativamente,
    obtener_ultima_fuente_generada,
    obtener_ultimo_tipo_generacion
)
from generador_melodia import generar_melodia_sobre_acordes, extraer_progresion_de_prompt
from procesador_sentimientos import detectar_sentimiento_en_prompt, inferir_parametros_desde_sentimiento



def _parse_melody_events(melodia):
    """Convierte una lista de (nota, duracion) en eventos temporales absolutos."""
    eventos = []
    if not melodia:
        return eventos

    tiempo_actual = 0.0
    for entrada in melodia:
        try:
            nombre = entrada[0]
            dur = float(entrada[1])
        except Exception:
            tiempo_actual += 0.0
            continue

        if dur <= 0:
            continue

        inicio = tiempo_actual
        fin = tiempo_actual + dur
        tiempo_actual = fin

        if nombre and nombre != "0":
            eventos.append((inicio, fin, nombre))
    return eventos


def _normalize_chord_voicing(acorde):
    """Devuelve una lista de nombres de nota a partir de un acorde en distintos formatos."""
    if acorde in (None, "", "0"):
        return []

    notas = []
    if isinstance(acorde, (list, tuple)):
        for elemento in acorde:
            if not elemento or elemento == "0":
                continue
            if isinstance(elemento, str) and elemento.startswith("SN_"):
                elemento = elemento[3:]
            notas.append(str(elemento))
    elif isinstance(acorde, str):
        valor = acorde
        if valor.startswith("SN_"):
            valor = valor[3:]
        if valor not in ("", "0"):
            notas.append(valor)
    else:
        notas.append(str(acorde))

    return notas


def _note_name_to_midi(note_name):
    try:
        return pitch.Pitch(note_name).midi
    except Exception:
        return None


def _midi_to_note_name(value):
    try:
        return pitch.Pitch(midi=int(round(value))).nameWithOctave
    except Exception:
        return None


def _revoice_to_range(notas, minimo=48, maximo=76):
    """Reubica una lista de notas dentro de un rango cómodo (C3–E5 aprox.)."""
    if not notas:
        return []

    midi_values = []
    leftovers = []
    for nota in notas:
        midi_val = _note_name_to_midi(nota)
        if midi_val is not None:
            value = midi_val
            while value < minimo:
                value += 12
            while value > maximo:
                value -= 12
            midi_values.append(value)
        else:
            leftovers.append(nota)

    if not midi_values:
        return notas

    midi_values.sort()

    # Evita duplicados exactos subiendo por octavas cuando sea posible
    cleaned = []
    used = set()
    for value in midi_values:
        original = value
        while int(round(value)) in used and value + 12 <= maximo:
            value += 12
        rounded = int(round(value))
        if rounded in used:
            value = original
            rounded = int(round(value))
        used.add(rounded)
        cleaned.append(value)

    resultado = [n for n in (_midi_to_note_name(v) for v in cleaned) if n]
    if not resultado:
        return notas

    resultado.extend(leftovers)
    return resultado


def _project_pitch_class_to_voicing(notas, nota_melodia, minimo=48, maximo=76):
    """Añade la clase de pitch de la melodía dentro del rango del acorde."""
    try:
        mel_pitch = pitch.Pitch(nota_melodia)
    except Exception:
        return notas

    objetivo_pc = mel_pitch.pitchClass
    existentes = []
    for nota in notas:
        midi_val = _note_name_to_midi(nota)
        if midi_val is None:
            continue
        if pitch.Pitch(nota).pitchClass == objetivo_pc:
            return notas
        existentes.append(midi_val)

    if not existentes:
        base = mel_pitch.midi
    else:
        base = sum(existentes) / len(existentes)

    candidato = mel_pitch.midi
    if base:
        while candidato - base > 6:
            candidato -= 12
        while base - candidato > 6:
            candidato += 12

    while candidato < minimo:
        candidato += 12
    while candidato > maximo:
        candidato -= 12

    nombre = _midi_to_note_name(candidato)
    if nombre and nombre not in notas:
        notas.append(nombre)
    return notas


def _transpose_note_name(note_name, semitones):
    """Devuelve el nombre de nota transpuesto en semitonos (con límites MIDI)."""
    if not note_name or note_name == "0":
        return note_name

    try:
        original_pitch = pitch.Pitch(note_name)
        new_midi = int(round(original_pitch.midi + semitones))
    except Exception:
        return note_name

    # Limita el rango MIDI válido
    new_midi = max(0, min(127, new_midi))

    try:
        transposed_pitch = pitch.Pitch(midi=new_midi)
        return transposed_pitch.nameWithOctave
    except Exception:
        return note_name


def _triad_from_root(raiz, modo):
    """Construye una triada básica a partir de la raíz y modo."""
    try:
        base_pitch = pitch.Pitch(raiz if raiz else "C")
    except Exception:
        base_pitch = pitch.Pitch("C")

    modo_norm = (modo or "major").lower()
    if "dim" in modo_norm:
        intervalos = [0, 3, 6]
    elif "min" in modo_norm and "maj" not in modo_norm:
        intervalos = [0, 3, 7]
    else:
        intervalos = [0, 4, 7]

    resultado = []
    for semitonos in intervalos:
        try:
            resultado.append(base_pitch.transpose(semitonos).nameWithOctave)
        except Exception:
            continue
    return resultado


def ajustar_acordes_a_melodia(acordes, ritmo, melodia, raiz, modo):
    """Devuelve acordes ajustados para incluir las notas importantes de la melodía."""
    if not melodia or not acordes:
        return acordes, ritmo, None, None

    eventos = _parse_melody_events(melodia)
    if not eventos:
        return acordes, ritmo, None, None

    ritmo_seguro = list(ritmo) if ritmo else []
    if len(ritmo_seguro) < len(acordes):
        ultimo = ritmo_seguro[-1] if ritmo_seguro else 1.0
        ritmo_seguro.extend([ultimo] * (len(acordes) - len(ritmo_seguro)))
    elif len(ritmo_seguro) > len(acordes):
        ritmo_seguro = ritmo_seguro[:len(acordes)]

    acordes_ajustados = []
    detalles = []
    tiempos = []
    cursor = 0.0

    for indice, acorde in enumerate(acordes):
        duracion = float(ritmo_seguro[indice]) if indice < len(ritmo_seguro) else 1.0
        inicio = cursor
        cursor += duracion
        tiempos.append(inicio)

        notas = _normalize_chord_voicing(acorde)
        if not notas:
            notas = _triad_from_root(raiz, modo)
        if not notas:
            notas = ["C4", "E4", "G4"]

        notas = _revoice_to_range(notas)

        notas_melodia = [evento[2] for evento in eventos if evento[0] < inicio + duracion and evento[1] > inicio]
        for nota_mel in notas_melodia:
            notas = _project_pitch_class_to_voicing(notas, nota_mel)

        notas_finales = _revoice_to_range(notas)

        acordes_ajustados.append(notas_finales)
        detalles.append([(nota, 0.0, float(duracion)) for nota in notas_finales])

    return acordes_ajustados, ritmo_seguro, detalles, tiempos

def generar_progresion(prompt: str, num_acordes: int = -1, melodia=None, bpm: int = 0):
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

        acordes_detallados = None
        acordes_tiempos = None

        if melodia:
            try:
                acordes_generados, ritmo_obtenido, acordes_detallados, acordes_tiempos = ajustar_acordes_a_melodia(
                    acordes_generados,
                    ritmo_obtenido,
                    melodia,
                    raiz_final,
                    modo_final,
                )
            except Exception as ajuste_ex:
                print(f"Advertencia: no se pudo ajustar acordes a la melodía: {ajuste_ex}")

        # Devolvemos el resultado incluyendo el BPM
        resultado = {
            "acordes": acordes_generados,
            "ritmo": ritmo_obtenido,
            "raiz": raiz_final,
            "modo": modo_final,
            "estilo": estilo_final,
            "bpm": bpm if bpm > 0 else bpm_sugerido,
            "tipo_generacion": obtener_ultimo_tipo_generacion(),
            "fuente_generacion": obtener_ultima_fuente_generada(),
            "error": "",
        }

        if melodia:
            resultado["melodia"] = melodia
            if acordes_detallados is not None:
                resultado["acordes_detallados"] = acordes_detallados
            if acordes_tiempos is not None:
                resultado["acordes_tiempos"] = acordes_tiempos

        return resultado

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

def generar_melodia_desde_prompt(prompt, num_acordes=-1, bpm=0):
    """Genera una melodía únicamente a partir del prompt del usuario."""
    try:
        if not prompt or not str(prompt).strip():
            return {"error": "Prompt vacío."}

        estilo_explicito = detectar_estilo(prompt)
        raiz_explicita, modo_explicito = extraer_tonalidad(prompt, estilo_detectado_param=estilo_explicito)
        sentimiento_detectado = detectar_sentimiento_en_prompt(prompt)

        generos_entrenados = {
            g
            for g in INFO_GENERO.keys()
            if g != "patrones_ritmicos"
            and isinstance(INFO_GENERO.get(g), dict)
            and any(INFO_GENERO[g].get(k) for k in INFO_GENERO[g] if k != "patrones_ritmicos")
        }
        if not generos_entrenados and INFO_GENERO:
            generos_entrenados = {g for g in INFO_GENERO.keys() if g != "patrones_ritmicos"}

        estilo_final, raiz_final, modo_final = inferir_parametros_desde_sentimiento(
            sentimiento_detectado,
            estilo_explicito,
            raiz_explicita,
            modo_explicito,
            generos_entrenados,
        )

        if not estilo_final or estilo_final == "normal" or estilo_final not in INFO_GENERO or not INFO_GENERO.get(estilo_final):
            estilo_ref = estilo_explicito or estilo_final or "desconocido"
            return {"error": f"No se encontró un género válido para '{estilo_ref}'."}

        if not raiz_final:
            raiz_final = "C"
        if not modo_final:
            modo_final = "major"

        bpm_utilizado = int(bpm) if bpm and int(bpm) > 0 else MAPEO_GENERO_BPM.get(estilo_final, MAPEO_GENERO_BPM["normal"])[2]

        acordes_prompt = extraer_progresion_de_prompt(prompt, raiz_final, modo_final)
        ritmo_prompt = [2.0] * len(acordes_prompt) if acordes_prompt else []

        longitud_objetivo = num_acordes if num_acordes and num_acordes > 0 else None

        melodia_generada, acordes_generados, ritmo_generado = generar_melodia_sobre_acordes(
            acordes_prompt,
            ritmo_prompt,
            raiz_final,
            modo_final,
            genero=estilo_final,
            bpm=bpm_utilizado,
            longitud_objetivo=longitud_objetivo,
            devolver_contexto=True,
        )

        if not melodia_generada:
            return {"error": "No se pudo generar la melodía."}

        return {
            "acordes": acordes_generados,
            "ritmo": ritmo_generado,
            "melodia": melodia_generada,
            "raiz": raiz_final,
            "modo": modo_final,
            "estilo": estilo_final,
            "bpm": bpm_utilizado,
            "tipo_generacion": "melody_prompt",
            "fuente_generacion": "Melodía generada desde prompt",
            "error": ""
        }
    except Exception as e:
        error_message = f"Error en generar_melodia_desde_prompt: {str(e)}\n{traceback.format_exc()}"
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


def exportar_acordes_midi(acordes, ritmo, bpm, acordes_detallados=None, acordes_tiempos=None):
    s = stream.Stream()
    s.insert(0, tempo.MetronomeMark(number=bpm))
    s.append(instrument.Piano())

    offset_actual = 0.0
    for i, ac_data in enumerate(acordes):
        duracion = float(ritmo[i]) if i < len(ritmo) else 1.0
        base_offset = offset_actual
        if acordes_tiempos and i < len(acordes_tiempos):
            try:
                base_offset = float(acordes_tiempos[i])
            except Exception:
                base_offset = offset_actual

        detalle_actual = None
        if acordes_detallados and i < len(acordes_detallados):
            detalle_actual = acordes_detallados[i]

        if detalle_actual:
            for detalle in detalle_actual:
                try:
                    nombre_nota = detalle[0] if len(detalle) > 0 else "0"
                    offset = float(detalle[1]) if len(detalle) > 1 else 0.0
                    dur_detalle = float(detalle[2]) if len(detalle) > 2 else duracion
                    if nombre_nota and nombre_nota != "0":
                        transposed_name = _transpose_note_name(nombre_nota, -12)
                        if transposed_name and transposed_name != "0":
                            nota_obj = note.Note(transposed_name, quarterLength=dur_detalle)
                            s.insert(base_offset + offset, nota_obj)
                        else:
                            nota_obj = note.Note(nombre_nota, quarterLength=dur_detalle)
                            s.insert(base_offset + offset, nota_obj)
                except Exception as e_det:
                    print(f"Advertencia (exportar_acordes_midi): detalle inválido {detalle}: {e_det}")
        else:
            if isinstance(ac_data, list):
                notas_transpuestas = []
                for nombre in ac_data:
                    transposed_name = _transpose_note_name(nombre, -12)
                    if transposed_name and transposed_name != "0":
                        notas_transpuestas.append(transposed_name)
                if not notas_transpuestas:
                    notas_transpuestas = [str(nombre) for nombre in ac_data if nombre not in (None, "", "0")]
                if notas_transpuestas:
                    acorde_obj = chord.Chord(notas_transpuestas, quarterLength=duracion)
                    s.insert(base_offset, acorde_obj)
            elif ac_data not in (None, "", "0"):
                transposed_name = _transpose_note_name(ac_data, -12)
                if not transposed_name or transposed_name == "0":
                    transposed_name = str(ac_data)
                acorde_obj = chord.Chord([transposed_name], quarterLength=duracion)
                s.insert(base_offset, acorde_obj)

        if acordes_tiempos and i + 1 < len(acordes_tiempos):
            try:
                offset_actual = float(acordes_tiempos[i + 1])
            except Exception:
                offset_actual = base_offset + duracion
        else:
            offset_actual = base_offset + duracion

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
            transposed_name = _transpose_note_name(nombre_nota, -12)
            if not transposed_name or transposed_name == "0":
                transposed_name = nombre_nota
            elemento = note.Note(transposed_name, quarterLength=duracion)

        s.insert(offset_actual, elemento)
        offset_actual += duracion

    return _exportar_a_midi(s, "melodia")

def actualizar_progresion_editada(datos_musica):
    """Actualiza el estado interno con una progresión editada desde el plugin."""
    global _ultima_progresion_generada, _ultimo_ritmo_generado, _ultimo_genero, _ultima_tonalidad_str, _ultima_fuente_generada, _ultimo_tipo_generacion

    try:
        acordes = datos_musica.get("acordes", []) or []
        ritmo = datos_musica.get("ritmo", []) or []
        _ultima_progresion_generada = [list(a) if isinstance(a, list) else a for a in acordes]
        _ultimo_ritmo_generado = ritmo

        estilo = datos_musica.get("estilo")
        if estilo:
            _ultimo_genero = estilo

        raiz = datos_musica.get("raiz")
        modo = datos_musica.get("modo")
        if raiz:
            modo_str = modo.lower() if isinstance(modo, str) and modo else "major"
            _ultima_tonalidad_str = f"{raiz.lower()} {modo_str}".strip()

        _ultima_fuente_generada = datos_musica.get("fuente_generacion", "Plugin Editado") or "Plugin Editado"
        _ultimo_tipo_generacion = datos_musica.get("tipo_generacion", "plugin_edit") or "plugin_edit"

        return {"status": "ok"}
    except Exception as e:
        error_msg = f"Error actualizando progresión editada: {e}"
        print(f"!!! Python API Error: {error_msg}")
        return {"status": "error", "error": error_msg}

def transponer_musica(datos_musica, semitonos):
    """
    Toma un diccionario de datos musicales y lo transpone por un número de semitonos.
    """
    try:
        acordes = datos_musica.get("acordes", [])
        melodia = datos_musica.get("melodia", []) # Maneja el caso de que aún no haya melodía

        # Llamamos a la función de transposición que ya existe en tu código
        acordes_transpuestos, melodia_transpuesta = transponer_progresion(acordes, semitonos, melodia)

        detalles = datos_musica.get("acordes_detallados")
        detalles_transpuestos = None
        if detalles:
            detalles_transpuestos = []
            for detalle_acorde in detalles:
                if not detalle_acorde:
                    detalles_transpuestos.append([])
                    continue

                acorde_detalle_transformado = []
                for detalle in detalle_acorde:
                    try:
                        nombre = detalle[0] if len(detalle) > 0 else "0"
                        offset = float(detalle[1]) if len(detalle) > 1 else 0.0
                        duracion = float(detalle[2]) if len(detalle) > 2 else 0.0

                        if nombre and nombre not in ("0", ""):
                            nombre_base = nombre if any(ch.isdigit() for ch in nombre) else f"{nombre}4"
                            nombre_transpuesto = pitch.Pitch(nombre_base).transpose(semitonos).nameWithOctave
                        else:
                            nombre_transpuesto = "0"

                        acorde_detalle_transformado.append((nombre_transpuesto, offset, duracion))
                    except Exception as e_det:
                        print(f"Advertencia (transponer_musica.detalle): {e_det}")
                        acorde_detalle_transformado.append(detalle)

                detalles_transpuestos.append(acorde_detalle_transformado)

        # Creamos un nuevo diccionario con los datos actualizados
        nuevos_datos = datos_musica.copy()
        nuevos_datos["acordes"] = acordes_transpuestos
        nuevos_datos["melodia"] = melodia_transpuesta
        if detalles_transpuestos is not None:
            nuevos_datos["acordes_detallados"] = detalles_transpuestos
        nuevos_datos["error"] = ""
        
        print(f">>> Python API: Música transpuesta por {semitonos} semitonos.")
        return nuevos_datos

    except Exception as e:
        error_msg = f"Error al transponer: {e}\\n{traceback.format_exc()}"
        print(f"!!! Python API Error: {error_msg}")
        return {"error": error_msg}

def puntuar_positivamente():
    """
    Endpoint de la API para el feedback positivo.
    """
    print(">>> Python API: Recibida puntuación positiva.")
    puntuar_acordes_positivamente()
    return {"status": "ok"}

def puntuar_negativamente():
    """
    Endpoint de la API para el feedback negativo.
    """
    print(">>> Python API: Recibida puntuación negativa.")
    puntuar_acordes_negativamente()
    return {"status": "ok"}

#Generacion de sonido
def generar_sonido(prompt: str):
    """
    Función principal para generar un patch de sintetizador desde JUCE.
    """
    global last_generated_patch

    try:
        print(f">>> Python API: Recibido prompt de sonido: '{prompt}'")
        
        parse_result = parse_sound_prompt(prompt)
        # Lógica simple de parsing: separamos el prompt por espacios o comas
        tags = parse_result["tags"]
        
        patch = generate_synth_patch(tags)
        
        if "error" in patch:
            print(f"!!! Python API Error: {patch['error']}")
            last_generated_patch = None
            return patch

        print(f">>> Python API: Patch generado con éxito: {patch}")
        last_generated_patch = {"tags": tags, "patch": patch.copy()}
        return patch

    except Exception as e:
        last_generated_patch = None
        error_message = f"Error en generar_sonido: {str(e)}"
        print(error_message)
        return {"error": error_message}

# --- NUEVA FUNCIÓN PARA GUARDAR EL SONIDO APRENDIDO ---
def like_last_sound():
    """
    Toma el último sonido generado que se guardó en 'last_generated_patch',
    y lo añade al archivo 'learned_sounds.json' para el aprendizaje.
    """
    global last_generated_patch
    if not last_generated_patch:
        print("!!! Python API Warning: No hay un sonido reciente para guardar.")
        return {"status": "error", "message": "No hay un sonido reciente para guardar."}
    
    # file_path = os.path.join(RUTA_BASE_PLUGIN, 'learned_sounds.json') # Línea original comentada/eliminada
    file_path = RUTA_LEARNED_SOUNDS # Usar la nueva ruta definida arriba
    
    try:
        # 1. Cargar los sonidos que ya hemos aprendido
        learned_data = []
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as f:
                learned_data = json.load(f)

        # 2. Añadir el nuevo sonido a la lista
        learned_data.append(last_generated_patch)

        # 3. Guardar la lista completa de nuevo en el archivo
        with open(file_path, 'w') as f:
            json.dump(learned_data, f, indent=4) # indent=4 lo hace legible
        
        print(">>> Python API: Sonido guardado en la base de conocimiento.")
        return {"status": "ok"}
    except Exception as e:
        error_message = f"Error al guardar el sonido aprendido: {str(e)}"
        print(f"!!! Python API Error: {error_message}")
        return {"status": "error", "message": error_message}
    
def get_learned_sounds():
    """
    Lee el archivo 'learned_sounds.json' y devuelve una lista de los presets guardados.
    Cada preset tendrá un nombre único y su correspondiente patch de parámetros.
    """
    
    # file_path = os.path.join(RUTA_BASE_PLUGIN, 'learned_sounds.json') # Línea original comentada/eliminada
    file_path = RUTA_LEARNED_SOUNDS # Usar la nueva ruta definida arriba
    
    if not os.path.exists(file_path):
        return {"error": "El archivo de sonidos aprendidos no existe."}
    
    try:
        with open(file_path, 'r') as f:
            learned_data = json.load(f)

        presets = {}
        name_counts = {}
        # Procesamos cada sonido para darle un nombre legible y único
        for sound in learned_data:
            # Creamos un nombre base a partir de los tags (ej: "pad_warm_bright")
            base_name = "_".join(sound.get("tags", ["preset"]))
            
            # Gestionamos nombres duplicados añadiendo un número (ej: "pad_warm_2")
            if base_name in name_counts:
                name_counts[base_name] += 1
                display_name = f"{base_name}_{name_counts[base_name]}"
            else:
                name_counts[base_name] = 1
                display_name = base_name

            # Guardamos el patch completo bajo su nuevo nombre
            presets[display_name] = sound.get("patch", {})
            
        print(f">>> Python API: Devolviendo {len(presets)} presets aprendidos.")
        return presets

    except Exception as e:
        error_message = f"Error al leer los sonidos aprendidos: {str(e)}"
        print(f"!!! Python API Error: {error_message}")
        return {"error": error_message}

def get_sound_archetypes():
    """
    Devuelve una lista con los nombres de todos los arquetipos de sonido disponibles.
    """
    try:
        # Importamos los arquetipos directamente desde el módulo de diseño de sonido
        from sound_designer import ARCHETYPES
        
        # Las claves del diccionario son los nombres que queremos mostrar
        archetype_names = list(ARCHETYPES.keys())
        
        print(f">>> Python API: Devolviendo {len(archetype_names)} arquetipos de sonido.")
        return archetype_names
    except Exception as e:
        error_message = f"Error al obtener los arquetipos de sonido: {str(e)}"
        print(f"!!! Python API Error: {error_message}")
        # Devolvemos una lista vacía en caso de error
        return []
