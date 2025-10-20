# generador_acordes.py
import random
import re
import os
import sys
import pprint
from collections import defaultdict, deque
from music21 import key, roman, pitch, harmony, chord as m21_chord
import importlib.util

# --- Mapeo de BPM por Género ---
# (min_bpm, max_bpm, default_bpm_sugerido)
MAPEO_GENERO_BPM = {
    "jazz": (80, 120, 100),
    "lofi": (70, 90, 80),
    "r&b": (60, 110, 90), # Amplio, 90 como punto medio
    "vals": (84, 180, 120),
    "pop": (100, 130, 115),
    "techno": (125, 140, 130),
    "reggaeton": (85, 100, 95),
    # Añade más géneros y sus BPMs aquí si es necesario
    "normal": (80, 120, 100) # Un default si el género es "normal"
}

# --- Variables Globales para Aprendizaje y Estado ---
_ultima_progresion_generada = None
_ultimo_ritmo_generado = None 
_ultimo_genero = None
_ultima_tonalidad_str = None

# Importar INFO_GENERO directamente desde base_estilos
# Asegúrate que base_estilos.py esté en el mismo directorio o en PYTHONPATH
try:
    from base_estilos import INFO_GENERO
except ImportError:
    print("ADVERTENCIA (generador_acordes.py): No se pudo importar INFO_GENERO de base_estilos.py.")
    INFO_GENERO = {}


nota_equivalente = {
    "do": "C", "re": "D", "mi": "E", "fa": "F", "sol": "G", "la": "A", "si": "B",
    "do#": "C#", "re#": "D#", "fa#": "F#", "sol#": "G#", "la#": "A#",
    "reb": "Db", "mib": "Eb", "fab": "Fb", "solb": "Gb", "lab": "Ab", "sib": "Bb",
    "c": "C", "d": "D", "e": "E", "f": "F", "g": "G", "a": "A", "b": "B",
    "cm": "C", "dm": "D", "em": "E", "fm": "F", "gm": "G", "am": "A", "bm": "B",
    "c#": "C#", "d#": "D#", "f#": "F#", "g#": "G#", "a#": "A#",
    "db": "Db", "eb": "Eb", "gb": "Gb", "ab": "Ab", "bb": "Bb"
}

_CANONICAL_TONIC_NAMES_LIST = ["c", "c#", "d", "eb", "e", "f", "f#", "g", "g#", "a", "bb", "b"]

def resource_path(relative_path):
    """ Obtiene la ruta absoluta a un recurso, funciona para desarrollo y para el bundle de PyInstaller. """
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # base_path será la ruta del script en desarrollo
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def _get_canonical_tonic_name_for_generator(tonic_name_input):
    """
    Convierte un nombre de tónica (posiblemente en español o con variaciones)
    a un nombre canónico en inglés usado internamente (ej. "c", "c#", "bb").
    """
    if tonic_name_input is None: return None # Manejar None
    # Primero, intentar una conversión directa usando el diccionario nota_equivalente
    processed_tonic_input = nota_equivalente.get(tonic_name_input.lower(), tonic_name_input)
    # Luego, usar music21 para normalizar y asegurar que esté en la lista canónica
    try:
        temp_pitch = pitch.Pitch(processed_tonic_input)
    except Exception:
        # Si music21 no puede parsearlo, usar la versión simplificada (minúsculas, b para bemoles)
        return processed_tonic_input.lower().replace("♯", "#").replace("♭", "b")

    simple_normalized_name = temp_pitch.name.lower().replace('-', 'b') # music21 usa '-' para bemoles

    if simple_normalized_name in _CANONICAL_TONIC_NAMES_LIST:
        return simple_normalized_name
    else:
        # Si no está en la lista (ej. "d--"), buscar un equivalente enarmónico que sí esté
        for standard_name_str in _CANONICAL_TONIC_NAMES_LIST:
            try:
                standard_pitch_obj = pitch.Pitch(standard_name_str)
                if temp_pitch.ps == standard_pitch_obj.ps: # Comparar por valor MIDI
                    return standard_name_str
            except Exception:
                continue
    # Fallback final si no se encontró un equivalente enarmónico en la lista
    return simple_normalized_name


# Variables globales para el modo de generación y el índice de progresión aprendida
_current_learned_prog_indices = defaultdict(lambda: defaultdict(int)) # estilo -> tonalidad -> índice
_generator_mode = defaultdict(lambda: defaultdict(lambda: "learned"))  # estilo -> tonalidad -> "learned" o "markov"
_ultima_fuente_generada = ""
_ultimo_tipo_generacion = ""


def obtener_ultima_fuente_generada():
    """Devuelve una descripción detallada de la última fuente de progresión generada."""
    return _ultima_fuente_generada or ""


def obtener_ultimo_tipo_generacion():
    """Devuelve el tipo resumido (learned/markov/fallback) de la última progresión generada."""
    return _ultimo_tipo_generacion or ""

def obtener_altura_promedio_midi(voicing_tupla_o_lista):
    """Calcula la altura MIDI promedio de un voicing (tupla o lista de nombres de notas)."""
    if isinstance(voicing_tupla_o_lista, str) and voicing_tupla_o_lista.startswith("SN_"): # Nota individual
        try:
            return pitch.Pitch(voicing_tupla_o_lista[3:]).ps # ps es el valor MIDI
        except:
            return None # No se pudo parsear la nota
    elif isinstance(voicing_tupla_o_lista, (tuple, list)):
        alturas_midi = []
        for nota_str in voicing_tupla_o_lista:
            try:
                alturas_midi.append(pitch.Pitch(nota_str).ps)
            except:
                continue # Ignorar si una nota no se puede parsear
        if alturas_midi:
            return sum(alturas_midi) / len(alturas_midi)
    return None # No es un formato de voicing reconocible

def suavizar_transicion_voicing(voicing_actual, voicing_anterior, max_dif_promedio=7):
    """Mantiene el voicing actual en un rango cercano al anterior evitando saltos grandes de octava."""
    if not voicing_actual or not voicing_anterior:
        return voicing_actual

    if isinstance(voicing_actual, str) or isinstance(voicing_anterior, str):
        # Para formatos no reconocidos (por ejemplo "0"), no modificar
        return voicing_actual

    midi_prev = obtener_altura_promedio_midi(voicing_anterior)
    midi_actual = obtener_altura_promedio_midi(voicing_actual)

    if midi_prev is None or midi_actual is None:
        return voicing_actual

    offset = 0
    # Traer la media del acorde actual a una distancia razonable del anterior
    while midi_actual - midi_prev > max_dif_promedio:
        offset -= 12
        midi_actual -= 12
    while midi_prev - midi_actual > max_dif_promedio:
        offset += 12
        midi_actual += 12

    if offset != 0:
        voicing_suavizado = []
        for nota in voicing_actual:
            try:
                pitch_obj = pitch.Pitch(nota)
                pitch_obj.midi += offset
                voicing_suavizado.append(pitch_obj.nameWithOctave)
            except Exception:
                voicing_suavizado.append(nota)
        voicing_actual = voicing_suavizado
        midi_actual = obtener_altura_promedio_midi(voicing_actual) or midi_actual

    # Ajuste fino si todavía hay gran diferencia
    if abs(midi_actual - midi_prev) > max_dif_promedio:
        voicing_suavizado = []
        for nota in voicing_actual:
            try:
                pitch_obj = pitch.Pitch(nota)
                while pitch_obj.midi - midi_prev > max_dif_promedio:
                    pitch_obj.octave -= 1
                while midi_prev - pitch_obj.midi > max_dif_promedio:
                    pitch_obj.octave += 1
                voicing_suavizado.append(pitch_obj.nameWithOctave)
            except Exception:
                voicing_suavizado.append(nota)
        return voicing_suavizado

    return voicing_actual

def _normalizar_evento_markov(evento):
    """Convierte listas en tuplas (hashables) para comparaciones consistentes."""
    if isinstance(evento, list):
        return tuple(evento)
    return evento

def ajustar_pesos_para_diversidad(eventos, pesos, historial_reciente, evento_actual):
    """Penaliza opciones ya usadas recientemente para fomentar variedad en la cadena de Markov."""
    if not eventos or not pesos:
        return pesos

    historial_set = {_normalizar_evento_markov(ev) for ev in historial_reciente if ev is not None}
    evento_actual_norm = _normalizar_evento_markov(evento_actual)
    # Identificar repeticiones consecutivas del mismo evento para reforzar la penalización
    run_length_mismo_evento = 0
    ultimo_evento_hist = None
    for ev_hist in reversed(historial_reciente):
        if ev_hist is None:
            continue
        ev_hist_norm = _normalizar_evento_markov(ev_hist)
        if ultimo_evento_hist is None:
            ultimo_evento_hist = ev_hist_norm
            run_length_mismo_evento = 1
        elif ev_hist_norm == ultimo_evento_hist:
            run_length_mismo_evento += 1
        else:
            break
    pesos_ajustados = []
    for ev, peso in zip(eventos, pesos):
        nuevo_peso = float(peso)
        # Penalizar repetir el mismo evento consecutivamente cuando existen alternativas
        if evento_actual_norm is not None and _normalizar_evento_markov(ev) == evento_actual_norm and len(eventos) > 1:
            if run_length_mismo_evento >= 2:
                nuevo_peso *= 0.1
            else:
                nuevo_peso *= 0.45
        if _normalizar_evento_markov(ev) in historial_set:
            nuevo_peso *= 0.6
            
        if historial_reciente.count(ev) >= 2:
            nuevo_peso *= 0.3  # Penalización por repetición excesiva

        if nuevo_peso < 0:
            nuevo_peso = 0.0
        pesos_ajustados.append(nuevo_peso)

    if sum(pesos_ajustados) == 0:
        return pesos
    return pesos_ajustados

KEY_C_MAJOR = key.Key("C", "major")
KEY_C_MINOR = key.Key("C", "minor")

_COMMON_DEGREE_TRANSITIONS = {
    1: {4, 5, 6, 2},
    2: {5, 7},
    3: {6, 4},
    4: {5, 1, 2},
    5: {1, 6},
    6: {4, 2, 5},
    7: {1, 6},
}

_FUNCION_PESOS = {
    "tonic": {"tonic": 2.5, "predominant": 1.2, "dominant": 0.8, "other": 0.65},
    "predominant": {"predominant": 2.4, "tonic": 1.0, "dominant": 1.2, "other": 0.7},
    "dominant": {"dominant": 2.6, "predominant": 1.3, "tonic": 0.85, "other": 0.6},
}


def _clasificar_funcion_armonica(evento_func, modo="major"):
    """Clasifica un numeral romano en función tonal (tónica, predominante, dominante)."""
    if not evento_func or not isinstance(evento_func, str):
        return "other"
    if evento_func == "0" or evento_func.startswith("SN_"):
        return "other"

    roman_input = evento_func.strip()
    referencia_key = KEY_C_MINOR if modo == "minor" else KEY_C_MAJOR

    try:
        rn_obj = roman.RomanNumeral(roman_input, referencia_key)
        grado = rn_obj.scaleDegree
    except Exception:
        base_match = re.match(r"^[#b♯♭-]*[ivIV]+", roman_input)
        if not base_match:
            return "other"
        try:
            rn_obj = roman.RomanNumeral(base_match.group(0), referencia_key)
            grado = rn_obj.scaleDegree
        except Exception:
            return "other"

    if modo == "minor":
        if grado in (1, 3, 6):
            return "tonic"
        if grado in (2, 4):
            return "predominant"
        if grado in (5, 7):
            return "dominant"
    else:
        if grado in (1, 3, 6):
            return "tonic"
        if grado in (2, 4):
            return "predominant"
        if grado in (5, 7):
            return "dominant"
    return "other"

def _planificar_frases_markov(longitud):
    """Devuelve longitudes y límites (inicio, fin) de cada frase."""
    if longitud <= 0:
        return [], []

    longitudes_frases = []
    restante = longitud

    while restante > 0:
        if restante >= 8:
            frase_len = 4
        elif restante >= 4:
            frase_len = 3 if restante == 5 else 4
        else:
            frase_len = restante

        longitudes_frases.append(frase_len)
        restante -= frase_len

    if longitudes_frases and longitudes_frases[-1] == 1:
        if len(longitudes_frases) >= 2:
            longitudes_frases[-2] += 1
            longitudes_frases.pop()
        else:
            longitudes_frases[0] = max(2, longitudes_frases[0])

    limites = []
    cursor = 0
    for frase_len in longitudes_frases:
        limites.append((cursor, cursor + frase_len - 1))
        cursor += frase_len

    return longitudes_frases, limites

def _construir_plan_funcional(longitud, modo="major"):
    """Crea una guía de funciones armónicas distribuida por frases."""
    if longitud <= 0:
        return [], []

    longitudes_frases, limites_frases = _planificar_frases_markov(longitud)
    plan = []
    ciclo_interior = ["predominant", "tonic", "predominant", "dominant"]
    indice_global = 0

    for frase_len in longitudes_frases:
        for pos in range(frase_len):
            if pos == 0:
                plan.append("tonic")
            elif pos == frase_len - 1:
                plan.append("tonic")
            elif pos == frase_len - 2:
                plan.append("dominant")
            else:
                plan.append(ciclo_interior[(indice_global + pos) % len(ciclo_interior)])
        indice_global += frase_len

    if longitud > 2 and "dominant" not in plan:
        plan[-2] = "dominant"
    if longitud > 3 and "predominant" not in plan:
        plan[1] = "predominant"
        
    # Refuerzo explícito de cadencia final
    if longitud >= 4:
        plan[-2] = "dominant"
        plan[-1] = "tonic"

    return plan, limites_frases


def _ajustar_pesos_por_plan_funcional(eventos, pesos, funcion_objetivo, modo="major"):
    """Refuerza los pesos para favorecer la función armónica objetivo en el siguiente acorde."""
    if not eventos or not pesos or not funcion_objetivo:
        return pesos

    matriz = _FUNCION_PESOS.get(funcion_objetivo)
    if not matriz:
        return pesos

    pesos_ajustados = []
    for ev, peso in zip(eventos, pesos):
        funcion = _clasificar_funcion_armonica(ev, modo)
        factor = matriz.get(funcion, matriz.get("other", 1.0))
        pesos_ajustados.append(float(peso) * factor)

    if sum(pesos_ajustados) == 0:
        return pesos
    return pesos_ajustados

def _ajustar_pesos_por_transicion_musical(eventos, pesos, evento_previo, modo, tonalidad_key_obj, historial_eventos):
    """Favorece transiciones comunes y evita repeticiones excesivas."""
    if not eventos or not pesos or not evento_previo:
        return pesos

    evento_previo_norm = _normalizar_evento_markov(evento_previo)
    if evento_previo_norm in (None, "0") or (isinstance(evento_previo_norm, str) and evento_previo_norm.startswith("SN_")):
        return pesos

    run_length_previo = 0
    for ev_hist in reversed(historial_eventos):
        if ev_hist is None:
            continue
        if _normalizar_evento_markov(ev_hist) == evento_previo_norm:
            run_length_previo += 1
        else:
            break

    try:
        rn_previo = roman.RomanNumeral(evento_previo_norm, tonalidad_key_obj)
        grado_previo = rn_previo.scaleDegree
        es_prev_diatonico = rn_previo.secondaryRomanNumeral is None
    except Exception:
        grado_previo = None
        es_prev_diatonico = False

    pesos_ajustados = []
    for ev, peso in zip(eventos, pesos):
        nuevo_peso = float(peso)
        ev_norm = _normalizar_evento_markov(ev)

        if ev_norm == evento_previo_norm and run_length_previo >= 2:
            pesos_ajustados.append(0.0)
            continue

        if ev_norm == "0":
            nuevo_peso *= 0.35
            pesos_ajustados.append(nuevo_peso)
            continue
        if isinstance(ev_norm, str) and ev_norm.startswith("SN_"):
            nuevo_peso *= 0.45
            pesos_ajustados.append(nuevo_peso)
            continue

        try:
            rn_cand = roman.RomanNumeral(ev_norm, tonalidad_key_obj)
            grado_cand = rn_cand.scaleDegree
            es_cand_diatonico = rn_cand.secondaryRomanNumeral is None
        except Exception:
            nuevo_peso *= 0.15
            pesos_ajustados.append(nuevo_peso)
            continue

        if not es_cand_diatonico:
            nuevo_peso *= 0.6
        if not es_prev_diatonico and not es_cand_diatonico:
            nuevo_peso *= 0.85

        if grado_previo is not None and grado_cand is not None:
            preferidos = _COMMON_DEGREE_TRANSITIONS.get(grado_previo, set())
            if grado_cand in preferidos:
                nuevo_peso *= 2.3
            elif grado_cand == grado_previo:
                nuevo_peso *= 0.4
            else:
                nuevo_peso *= 0.9

            distancia = min((grado_cand - grado_previo) % 7, (grado_previo - grado_cand) % 7)
            if distancia >= 4:
                nuevo_peso *= 0.7

        if nuevo_peso < 0:
            nuevo_peso = 0.0
        pesos_ajustados.append(nuevo_peso)

    if sum(pesos_ajustados) == 0:
        return pesos
    return pesos_ajustados

def _obtener_opciones_diatonicas_por_funcion(modo="major"):
    """Devuelve listas de numerales diatónicos representativos por función tonal."""
    if modo == "minor":
        return {
            "tonic": ["i", "i6", "i64", "III", "VI"],
            "predominant": ["ii°", "iiø65", "iv", "iv6"],
            "dominant": ["V", "V7", "V6", "V65", "vii°", "vii°7"],
        }
    return {
        "tonic": ["I", "I6", "I64", "iii", "vi"],
        "predominant": ["ii", "ii6", "ii7", "IV", "IV6"],
        "dominant": ["V", "V7", "V6", "V65", "vii°", "vii°7"],
    }


def _seleccionar_diatonico_por_funcion(funcion_objetivo, modo, contadores, opciones_generales, indice_general):
    opciones_por_funcion = _obtener_opciones_diatonicas_por_funcion(modo)
    candidatos_funcion = opciones_por_funcion.get(funcion_objetivo, [])
    if candidatos_funcion:
        idx = contadores[funcion_objetivo]
        contadores[funcion_objetivo] += 1
        return candidatos_funcion[idx % len(candidatos_funcion)]
    if opciones_generales:
        return opciones_generales[indice_general % len(opciones_generales)]
    return "I" if modo == "major" else "i"


def _realizar_evento_a_voicing(evento_func, tonalidad_key_obj, voicings_map):
    if not evento_func or evento_func == "0" or (isinstance(evento_func, str) and evento_func.startswith("SN_")):
        return evento_func
    voicings_candidatos = voicings_map.get(evento_func, [])
    if voicings_candidatos:
        return list(random.choice(voicings_candidatos))
    try:
        rn_obj = roman.RomanNumeral(evento_func, tonalidad_key_obj)
        chord_m21 = m21_chord.Chord(rn_obj.pitches)
        chord_m21.closedPosition(forceOctave=3, inPlace=True)
        return [p.nameWithOctave for p in chord_m21.pitches[:3]]
    except Exception:
        return "0"

def _reforzar_cadencias_por_frase(progresion, eventos_func, limites_frases, modo, tonalidad_key_obj, voicings_map):
    """Ajusta cada cierre de frase para asegurar respiración tonal."""
    if not progresion or not eventos_func or not limites_frases:
        return

    cambios = set()
    objetivo_tonica = "I" if modo == "major" else "i"
    objetivo_dominante = "V"

    for inicio, fin in limites_frases:
        if fin >= len(eventos_func):
            continue
        if _clasificar_funcion_armonica(eventos_func[fin], modo) != "tonic":
            eventos_func[fin] = objetivo_tonica
            cambios.add(fin)
        previo = fin - 1
        if previo >= inicio and previo >= 0:
            if _clasificar_funcion_armonica(eventos_func[previo], modo) not in ("dominant", "predominant"):
                eventos_func[previo] = objetivo_dominante
                cambios.add(previo)

    for idx in sorted(cambios):
        if idx < len(progresion):
            progresion[idx] = _realizar_evento_a_voicing(eventos_func[idx], tonalidad_key_obj, voicings_map)


def _validar_progresion_markov(eventos_func, modo, tonalidad_key_obj, limites_frases):
    reales = [ev for ev in eventos_func if isinstance(ev, str) and ev not in ("0", "") and not ev.startswith("SN_")]
    if len(reales) < 4:
        return False

    try:
        for ev in reales:
            roman.RomanNumeral(ev, tonalidad_key_obj)
    except Exception:
        return False

    run = 0
    ultimo = None
    for ev in eventos_func:
        if not isinstance(ev, str) or ev in ("0", "") or ev.startswith("SN_"):
            continue
        if ev == ultimo:
            run += 1
            if run >= 2:
                return False
        else:
            run = 0
            ultimo = ev

    if not any(_clasificar_funcion_armonica(ev, modo) == "dominant" for ev in eventos_func if isinstance(ev, str)):
        return False

    for inicio, fin in limites_frases:
        if fin < len(eventos_func):
            if _clasificar_funcion_armonica(eventos_func[fin], modo) != "tonic":
                return False
            if fin - 1 >= inicio and _clasificar_funcion_armonica(eventos_func[fin - 1], modo) not in ("dominant", "predominant"):
                return False

    return True


def _reparar_progresion_markov(eventos_func, plan_funcional, modo, tonalidad_key_obj):
    if not eventos_func:
        return

    contadores = defaultdict(int)
    opciones_generales = ['I', 'V', 'vi', 'IV'] if modo == "major" else ['i', 'VI', 'III', 'VII']

    for idx, ev in enumerate(eventos_func):
        if not isinstance(ev, str) or ev in ("0", "") or ev.startswith("SN_"):
            continue
        try:
            rn_check = roman.RomanNumeral(ev, tonalidad_key_obj)
            if rn_check.secondaryRomanNumeral is not None:
                raise Exception("non-diatonic")
        except Exception:
            funcion = plan_funcional[idx] if idx < len(plan_funcional) else None
            eventos_func[idx] = _seleccionar_diatonico_por_funcion(funcion, modo, contadores, opciones_generales, idx)

    run = 0
    ultimo = None
    for idx, ev in enumerate(eventos_func):
        if not isinstance(ev, str) or ev in ("0", "") or ev.startswith("SN_"):
            continue
        if ev == ultimo:
            run += 1
            if run >= 2:
                funcion = plan_funcional[idx] if idx < len(plan_funcional) else None
                nuevo_ev = _seleccionar_diatonico_por_funcion(funcion, modo, contadores, opciones_generales, idx + 3)
                if nuevo_ev == ev:
                    alternativas = [opt for opt in opciones_generales if opt != ev]
                    if alternativas:
                        nuevo_ev = random.choice(alternativas)
                eventos_func[idx] = nuevo_ev
                ultimo = nuevo_ev
                run = 0
        else:
            ultimo = ev
            run = 0


def _reconstruir_voicings_desde_eventos(eventos_func, tonalidad_key_obj, voicings_map):
    progresion = []
    ultimo_voicing = None
    for ev in eventos_func:
        voicing = _realizar_evento_a_voicing(ev, tonalidad_key_obj, voicings_map)
        if isinstance(voicing, list) and ultimo_voicing:
            voicing = suavizar_transicion_voicing(voicing, ultimo_voicing)
        progresion.append(voicing)
        if isinstance(voicing, list):
            ultimo_voicing = voicing
    return progresion


def _construir_progresion_diatonica_desde_plan(plan_funcional, modo, tonalidad_key_obj, voicings_map):
    eventos = []
    contadores = defaultdict(int)
    opciones_generales = ['I', 'V', 'vi', 'IV'] if modo == "major" else ['i', 'VI', 'III', 'VII']
    for idx, funcion in enumerate(plan_funcional):
        evento = _seleccionar_diatonico_por_funcion(funcion, modo, contadores, opciones_generales, idx)
        eventos.append(evento)
    progresion = _reconstruir_voicings_desde_eventos(eventos, tonalidad_key_obj, voicings_map)
    return progresion, eventos

def _asegurar_cadencia_final(progresion, eventos_func, modo, tonalidad_key_obj, voicings_map):
    """Ajusta los últimos acordes para garantizar una cadencia dominante-tónica."""
    if not progresion:
        return

    ultimo_indice_real = None
    for idx in range(len(progresion) - 1, -1, -1):
        evento = progresion[idx]
        if evento != "0" and not (isinstance(evento, str) and evento.startswith("SN_")):
            ultimo_indice_real = idx
            break

    if ultimo_indice_real is None:
        return

    penultimo_indice_real = None
    for idx in range(ultimo_indice_real - 1, -1, -1):
        evento = progresion[idx]
        if evento != "0" and not (isinstance(evento, str) and evento.startswith("SN_")):
            penultimo_indice_real = idx
            break

    objetivo_tonica = "I" if modo == "major" else "i"
    objetivo_dominante = "V"

    cambio_tonica = False
    if _clasificar_funcion_armonica(eventos_func[ultimo_indice_real] if ultimo_indice_real < len(eventos_func) else None, modo) != "tonic":
        nuevo_voicing = _realizar_evento_a_voicing(objetivo_tonica, tonalidad_key_obj, voicings_map)
        if nuevo_voicing != "0":
            progresion[ultimo_indice_real] = nuevo_voicing
            if ultimo_indice_real < len(eventos_func):
                eventos_func[ultimo_indice_real] = objetivo_tonica
            cambio_tonica = True

    if penultimo_indice_real is not None and _clasificar_funcion_armonica(eventos_func[penultimo_indice_real] if penultimo_indice_real < len(eventos_func) else None, modo) != "dominant":
        nuevo_voicing_dom = _realizar_evento_a_voicing(objetivo_dominante, tonalidad_key_obj, voicings_map)
        if nuevo_voicing_dom != "0":
            progresion[penultimo_indice_real] = nuevo_voicing_dom
            if penultimo_indice_real < len(eventos_func):
                eventos_func[penultimo_indice_real] = objetivo_dominante
            if cambio_tonica and penultimo_indice_real < ultimo_indice_real:
                progresion[penultimo_indice_real] = suavizar_transicion_voicing(progresion[penultimo_indice_real], progresion[ultimo_indice_real])

def ajustar_pesos_por_patron_ritmico(eventos, pesos, duracion_objetivo, evento_previo_norm, fue_nota_individual_anterior=False):
    """Modula los pesos en función de la duración que dicta el patrón rítmico."""
    if not eventos or not pesos or duracion_objetivo is None:
        return pesos

    pesos_ajustados = []
    for ev, peso in zip(eventos, pesos):
        nuevo_peso = float(peso)
        ev_norm = _normalizar_evento_markov(ev)
        es_silencio = ev_norm == "0"
        es_nota_individual = isinstance(ev_norm, str) and ev_norm.startswith("SN_")

        if duracion_objetivo >= 1.5:
            if es_silencio:
                nuevo_peso *= 0.15
                
            # Penalizar silencios largos adicionales
            if duracion_objetivo >= 1.5 and ev_norm == "0":
                nuevo_peso *= 0.2

            elif es_nota_individual:
                nuevo_peso *= 0.4
        elif duracion_objetivo >= 1.0:
            if es_silencio:
                nuevo_peso *= 0.35
            elif es_nota_individual and not fue_nota_individual_anterior:
                nuevo_peso *= 0.6
        elif duracion_objetivo <= 0.5:
            if evento_previo_norm not in (None, "0") and ev_norm == evento_previo_norm:
                nuevo_peso *= 1.25
            elif es_silencio:
                if evento_previo_norm == "0":
                    nuevo_peso *= 0.25
                else:
                    nuevo_peso *= 1.15
            elif not es_nota_individual and evento_previo_norm not in (None, "0"):
                nuevo_peso *= 0.85
        else:  # Duraciones intermedias (0.5 - 1.0 aprox.)
            if es_silencio and evento_previo_norm == "0":
                nuevo_peso *= 0.4

        if nuevo_peso < 0:
            nuevo_peso = 0.0
        pesos_ajustados.append(nuevo_peso)

    if sum(pesos_ajustados) == 0:
        return pesos
    return pesos_ajustados

def set_generator_mode(estilo, raiz, modo, mode_type="learned"):
    """Establece el modo de generación (aprendido o Markov) para un estilo y tonalidad."""
    global _generator_mode
    canonical_raiz_generator = _get_canonical_tonic_name_for_generator(raiz)
    canonical_modo_generator = modo.lower() if modo else None
    if not canonical_raiz_generator or not canonical_modo_generator: return # Evitar error si son None
    clave_tonalidad = f"{canonical_raiz_generator} {canonical_modo_generator}"

    _generator_mode[estilo][clave_tonalidad] = mode_type
    if mode_type == "learned": # Si se cambia a aprendido, resetear el índice
        reset_learned_prog_index(estilo, raiz, modo)


def reset_learned_prog_index(estilo, raiz, modo):
    """Resetea el índice de la próxima progresión aprendida a mostrar para un estilo y tonalidad."""
    global _current_learned_prog_indices
    canonical_raiz_generator = _get_canonical_tonic_name_for_generator(raiz)
    canonical_modo_generator = modo.lower() if modo else None
    if not canonical_raiz_generator or not canonical_modo_generator: return
    clave_tonalidad = f"{canonical_raiz_generator} {canonical_modo_generator}"

    _current_learned_prog_indices[estilo][clave_tonalidad] = 0
    print(f"Índice de progresión aprendida reseteado para {estilo} - {clave_tonalidad}")

def tuplificar_acorde_feedback(acorde_data):
    """Convierte una lista de notas de acorde a una tupla ordenada para el feedback."""
    if isinstance(acorde_data, list):
        return tuple(sorted(acorde_data))
    return acorde_data # Mantener "0" o nombres de acordes como están

def reforzar_progresion_con_feedback(genero, tonalidad_str, progresion_tuplas_feedback, ritmo, es_buena):
    """Actualiza el modelo de un género/tonalidad basado en el feedback del usuario."""
    print(f"🧠 Recibido feedback para Género: {genero}, Tonalidad: {tonalidad_str}, Buena: {es_buena}")
    print(f"Progresión (tuplas): {progresion_tuplas_feedback}")

    ruta_directorio_estilos = resource_path("estilos")
    os.makedirs(ruta_directorio_estilos, exist_ok=True) # Asegurar que exista # Asumiendo que está en la misma carpeta que este script
    ruta_archivo_estilo = os.path.join(ruta_directorio_estilos, f"base_{genero}.py")

    info_genero_para_guardar = {}
    if os.path.exists(ruta_archivo_estilo):
        try:
            # Usar un nombre de módulo único para evitar conflictos si se recarga
            module_name_fb = f"base_{genero}_feedback_module_{random.randint(1,100000)}"
            spec_fb = importlib.util.spec_from_file_location(module_name_fb, ruta_archivo_estilo)
            modulo_fb = importlib.util.module_from_spec(spec_fb)
            if spec_fb.loader:
                spec_fb.loader.exec_module(modulo_fb)
                info_genero_para_guardar = getattr(modulo_fb, "INFO_GENERO", {})
            else:
                print(f"Error crítico: No se pudo obtener el loader para {ruta_archivo_estilo} en feedback.")
                return False
        except Exception as e_load_fb:
            print(f"Error crítico cargando {ruta_archivo_estilo} para feedback: {e_load_fb}.")
            return False
    else:
        print(f"Info: Archivo de estilo {ruta_archivo_estilo} no encontrado. Creando nueva estructura para feedback para el género '{genero}'.")
        info_genero_para_guardar = {} # Crear diccionario vacío si el archivo no existe

    # Asegurar estructura de diccionarios
    if genero not in info_genero_para_guardar:
        info_genero_para_guardar[genero] = {}

    if tonalidad_str not in info_genero_para_guardar[genero]:
        info_genero_para_guardar[genero][tonalidad_str] = {
            "markov_transitions": {}, "start_chords": {}, "end_chords": {}, "learned_progressions": []
        }
    # Asegurar que todas las sub-claves necesarias existan
    modelo_tonalidad_actual = info_genero_para_guardar[genero][tonalidad_str]
    for key_model in ["markov_transitions", "start_chords", "end_chords", "learned_progressions"]:
        if key_model not in modelo_tonalidad_actual:
            modelo_tonalidad_actual[key_model] = {} if key_model != "learned_progressions" else []

    if "patrones_ritmicos" not in info_genero_para_guardar[genero]: # Patrones rítmicos a nivel de género
        info_genero_para_guardar[genero]["patrones_ritmicos"] = []


    if es_buena:
        if not progresion_tuplas_feedback: # No reforzar si la progresión está vacía
            print("Advertencia: Se intentó reforzar una progresión vacía con feedback positivo.")
            return False
        incremento = 3 # Mayor refuerzo para feedback positivo
        # Reforzar modelo de Markov
        ac_inicial_fb = progresion_tuplas_feedback[0]
        modelo_tonalidad_actual["start_chords"][ac_inicial_fb] = modelo_tonalidad_actual["start_chords"].get(ac_inicial_fb, 0) + incremento
        if len(progresion_tuplas_feedback) > 1:
            for i in range(len(progresion_tuplas_feedback) - 1):
                ac_actual_fb = progresion_tuplas_feedback[i]
                siguiente_ac_fb = progresion_tuplas_feedback[i+1]
                if ac_actual_fb not in modelo_tonalidad_actual["markov_transitions"]:
                    modelo_tonalidad_actual["markov_transitions"][ac_actual_fb] = {}
                modelo_tonalidad_actual["markov_transitions"][ac_actual_fb][siguiente_ac_fb] = \
                    modelo_tonalidad_actual["markov_transitions"][ac_actual_fb].get(siguiente_ac_fb, 0) + incremento
        ac_final_fb = progresion_tuplas_feedback[-1]
        modelo_tonalidad_actual["end_chords"][ac_final_fb] = modelo_tonalidad_actual["end_chords"].get(ac_final_fb, 0) + incremento
        # Reforzar/Añadir patrón rítmico
        if isinstance(ritmo, list) and ritmo:
            ritmo_tupla = tuple(ritmo) # Convertir a tupla para hashear
            patrones_existentes_tuplas = {tuple(p) for p in info_genero_para_guardar[genero]["patrones_ritmicos"]}
            if ritmo_tupla not in patrones_existentes_tuplas:
                 info_genero_para_guardar[genero]["patrones_ritmicos"].append(list(ritmo_tupla)) # Guardar como lista

        print(f"👍 Modelo reforzado para {genero} - {tonalidad_str}.")
        try:
            with open(ruta_archivo_estilo, "w", encoding="utf-8") as f:
                f.write(f"# Archivo de estilo para {genero}\n")
                f.write("# Contiene modelos de Markov, patrones rítmicos y progresiones aprendidas.\n\n")
                f.write("INFO_GENERO = ")
                f.write(pprint.pformat(info_genero_para_guardar, indent=4, width=120, sort_dicts=False))
            print(f"💾 Feedback (positivo) guardado en {ruta_archivo_estilo}")
            return True
        except Exception as e_write_fb:
            print(f"CRÍTICO: No se pudo guardar el feedback en {ruta_archivo_estilo}: {e_write_fb}")
            return False
    elif not es_buena: # Feedback negativo
        print(f"👎 Feedback negativo recibido para {genero} - {tonalidad_str}. Aplicando penalización…")
        decremento = 1 # Penalización más suave
        if progresion_tuplas_feedback: # Solo penalizar si hay progresión
            ac_inicial_pen = progresion_tuplas_feedback[0]
            sc = modelo_tonalidad_actual["start_chords"]
            sc[ac_inicial_pen] = max(0, sc.get(ac_inicial_pen, 0) - decremento)
            if len(progresion_tuplas_feedback) > 1:
                for i in range(len(progresion_tuplas_feedback) - 1):
                    actual_pen = progresion_tuplas_feedback[i]
                    siguiente_pen = progresion_tuplas_feedback[i+1]
                    mt = modelo_tonalidad_actual["markov_transitions"].setdefault(actual_pen, {})
                    mt[siguiente_pen] = max(0, mt.get(siguiente_pen, 0) - decremento)
            ac_final_pen = progresion_tuplas_feedback[-1]
            ec = modelo_tonalidad_actual["end_chords"]
            ec[ac_final_pen] = max(0, ec.get(ac_final_pen, 0) - decremento)
        # Considerar si se debe penalizar el patrón rítmico.
        # Por ahora, solo se elimina si es exactamente el mismo.
        pr = info_genero_para_guardar[genero]["patrones_ritmicos"]
        if isinstance(ritmo, list) and ritmo and ritmo in pr: # ritmo debe ser lista aquí
            try:
                pr.remove(ritmo)
                print(f"🥁 Patrón rítmico asociado a la progresión negativa eliminado de '{genero}'.")
            except ValueError: pass # No estaba, no hay problema
        try:
            with open(ruta_archivo_estilo, "w", encoding="utf-8") as f:
                f.write(f"# Archivo de estilo para {genero}\n")
                f.write("# Contiene modelos de Markov, patrones rítmicos y progresiones aprendidas.\n\n")
                f.write("INFO_GENERO = ")
                f.write(pprint.pformat(info_genero_para_guardar, indent=4, width=120, sort_dicts=False))
            print(f"💾 Feedback negativo (penalización) guardado en {ruta_archivo_estilo}")
            return True
        except Exception as e_pen:
            print(f"CRÍTICO: No se pudo guardar penalización en {ruta_archivo_estilo}: {e_pen}")
            return False
    return False # Si no es ni buena ni mala (caso no esperado)

def listificar_acorde(acorde_data_tupla):
    """Convierte un acorde de tupla a lista, manteniendo "0" y strings como están."""
    if isinstance(acorde_data_tupla, tuple):
        return list(acorde_data_tupla)
    return acorde_data_tupla # Para "0" o nombres de acordes ya en string

def extraer_tonalidad(prompt_texto, estilo_detectado_param="normal"):
    """
    Extrae la raíz y el modo de un prompt de texto.
    Devuelve (raiz_canonica, modo_canonico) o (None, None).
    """
    prompt_lower = prompt_texto.lower()
    palabras_clave_mayor = ["mayor", "major", "maj"]
    palabras_clave_menor = ["menor", "minor", "min", "m ", " m"] # Espacio para 'C m'
    modo_explicito_detectado = None

    # Detección de modo
    for palabra_mayor in palabras_clave_mayor:
        if palabra_mayor in prompt_lower: # Búsqueda simple de substring
            modo_explicito_detectado = "major"
            break
    if not modo_explicito_detectado:
        for palabra_menor in palabras_clave_menor:
            # Usar regex para asegurar que 'm' sea una palabra o esté al final de una nota
            if re.search(r'\b' + re.escape(palabra_menor) + r'\b', prompt_lower) or \
               (palabra_menor.strip() == "m" and re.search(r'[a-g][#b]?\s*m\b', prompt_lower)):
                modo_explicito_detectado = "minor"
                break

    # Detección de raíz
    # Priorizar frases más largas como "Do sostenido" antes que "Do"
    # Esto es un poco más complejo y podría necesitar un parseo más estructurado.
    # Por ahora, una búsqueda simple de las notas.
    palabras = re.findall(r"[a-zA-Z#♭b]+", prompt_lower) # Obtener "palabras" que podrían ser notas
    raiz_encontrada = None

    # Intentar encontrar la raíz más específica primero (ej. "do#", "solb")
    posibles_notas_con_alteracion = sorted([k for k in nota_equivalente.keys() if '#' in k or 'b' in k], key=len, reverse=True)
    for nota_alt_str in posibles_notas_con_alteracion:
        if nota_alt_str in prompt_lower:
            raiz_encontrada = nota_equivalente[nota_alt_str]
            break

    if not raiz_encontrada: # Si no se encontró con alteración, buscar notas naturales
        posibles_notas_naturales = sorted([k for k in nota_equivalente.keys() if '#' not in k and 'b' not in k and len(k) <=3], key=len, reverse=True)
        for nota_nat_str in posibles_notas_naturales:
            # Usar regex para buscar la nota como palabra completa para evitar falsos positivos (ej. "la" en "balada")
            if re.search(r'\b' + re.escape(nota_nat_str) + r'\b', prompt_lower):
                raiz_encontrada = nota_equivalente[nota_nat_str]
                break
    
    # Si aún no se encontró, intentar con las palabras individuales (menos preciso)
    if not raiz_encontrada:
        for palabra_o_nota in palabras:
            normalizada = palabra_o_nota.lower().replace("♯", "#").replace("♭", "b")
            if normalizada in nota_equivalente:
                raiz_encontrada = nota_equivalente[normalizada]
                break
            # Comprobar si es una nota válida para music21 (C, C#, Dbb, etc.)
            elif re.match(r"^[a-g][#b]{0,2}$", normalizada):
                try:
                    p_temp = pitch.Pitch(normalizada)
                    raiz_encontrada = p_temp.name # Usar el nombre canónico de music21
                    break
                except:
                    continue # No es una nota válida para music21

    if raiz_encontrada:
        print(f"INFO (extraer_tonalidad): Raíz explícita detectada: '{raiz_encontrada}'")
    else:
        print(f"INFO (extraer_tonalidad): No se detectó raíz explícita.")
        raiz_encontrada = None

    if modo_explicito_detectado:
        print(f"INFO (extraer_tonalidad): Modo explícito detectado: '{modo_explicito_detectado}'")
    else:
        print(f"INFO (extraer_tonalidad): No se detectó modo explícito.")
        modo_explicito_detectado = None

    return raiz_encontrada, modo_explicito_detectado


def cargar_patron_ritmico_acordes(estilo, num_acordes_deseado=4, preferir_ritmos_simples_para_markov=False):
    """Carga o genera un patrón rítmico para un estilo y número de acordes dado."""
    info_estilo_completo = INFO_GENERO.get(estilo, {})
    patrones_ritmicos_disponibles_tuplas = info_estilo_completo.get("patrones_ritmicos", [])
    # Convertir tuplas a listas para el procesamiento interno si vienen como tuplas del archivo
    patrones_ritmicos_disponibles = [list(p) for p in patrones_ritmicos_disponibles_tuplas if isinstance(p, tuple)]

    if not patrones_ritmicos_disponibles:
        default_len = num_acordes_deseado if num_acordes_deseado is not None else 4
        return [1.0] * default_len # Fallback a ritmo de 1.0 por acorde

    ritmo_final_seleccionado = None

    # Si se desea un número específico de acordes
    if num_acordes_deseado is not None:
        patrones_compatibles = [p for p in patrones_ritmicos_disponibles if len(p) == num_acordes_deseado]
        if preferir_ritmos_simples_para_markov and patrones_compatibles:
            # Priorizar ritmos donde todas las duraciones son >= 0.5 (corchea o más)
            patrones_simples_compatibles = [p for p in patrones_compatibles if all(float(d) >= 0.5 for d in p)]
            if patrones_simples_compatibles: ritmo_final_seleccionado = random.choice(patrones_simples_compatibles)
            elif patrones_compatibles: ritmo_final_seleccionado = random.choice(patrones_compatibles) # Si no hay simples, tomar cualquiera compatible
        elif patrones_compatibles: # Si no se prefiere simple, o no hay simples, tomar cualquiera compatible
            ritmo_final_seleccionado = random.choice(patrones_compatibles)

        # Si no se encontró un patrón compatible exacto, intentar adaptar uno existente
        if not ritmo_final_seleccionado and patrones_ritmicos_disponibles:
            chosen_pattern = random.choice(patrones_ritmicos_disponibles)
            if len(chosen_pattern) < num_acordes_deseado: # Repetir si es más corto
                ritmo_final_seleccionado = (chosen_pattern * (num_acordes_deseado // len(chosen_pattern) + 1))[:num_acordes_deseado]
            else: # Truncar si es más largo
                ritmo_final_seleccionado = chosen_pattern[:num_acordes_deseado]
        elif not ritmo_final_seleccionado: # Fallback si todo falla
             ritmo_final_seleccionado = [1.0] * num_acordes_deseado

    # Si no se desea un número específico de acordes (num_acordes_deseado es None)
    if ritmo_final_seleccionado is None:
        if preferir_ritmos_simples_para_markov and patrones_ritmicos_disponibles:
            patrones_simples = [p for p in patrones_ritmicos_disponibles if all(float(d) >= 0.5 for d in p)]
            if patrones_simples: ritmo_final_seleccionado = random.choice(patrones_simples)
            elif patrones_ritmicos_disponibles: ritmo_final_seleccionado = random.choice(patrones_ritmicos_disponibles)
        elif patrones_ritmicos_disponibles:
            ritmo_final_seleccionado = random.choice(patrones_ritmicos_disponibles)
        else: # Fallback si no hay patrones disponibles
            ritmo_final_seleccionado = [1.0] * 4 # Default a 4 acordes de 1.0

    # Asegurar que el resultado sea una lista de floats
    if ritmo_final_seleccionado:
        try: return [float(d) for d in ritmo_final_seleccionado]
        except (TypeError, ValueError): # Si algo sale mal en la conversión
            default_len_final = num_acordes_deseado if num_acordes_deseado is not None else len(ritmo_final_seleccionado) if ritmo_final_seleccionado else 4
            return [1.0] * default_len_final

    # Último fallback
    default_len_final_fallback = num_acordes_deseado if num_acordes_deseado is not None else 4
    return [1.0] * default_len_final_fallback

def obtener_progresion_aprendida(estilo, raiz, modo, num_acordes_deseado=None):
    """
    Obtiene una progresión aprendida de la base de datos para el estilo y tonalidad dados.
    Intenta coincidir con num_acordes_deseado si se especifica.
    Cicla a través de las progresiones aprendidas disponibles.
    """
    global _current_learned_prog_indices
    canonical_raiz_generator = _get_canonical_tonic_name_for_generator(raiz)
    canonical_modo_generator = modo.lower() if modo else None
    if not canonical_raiz_generator or not canonical_modo_generator : return None, None # Si no hay tonalidad completa
    clave_tonalidad_markov = f"{canonical_raiz_generator} {canonical_modo_generator}"

    if estilo not in INFO_GENERO or clave_tonalidad_markov not in INFO_GENERO[estilo]:
        return None, None # No hay datos para este estilo/tonalidad

    modelo_tonalidad = INFO_GENERO[estilo][clave_tonalidad_markov]
    all_learned_progs_data = modelo_tonalidad.get("learned_progressions", [])

    if not all_learned_progs_data:
        return None, None # No hay progresiones aprendidas

    # Filtrar progresiones por longitud deseada si se especifica
    progs_filtradas = []
    if num_acordes_deseado is not None:
        for prog_entry in all_learned_progs_data:
            if len(prog_entry.get('chords', [])) == num_acordes_deseado:
                progs_filtradas.append(prog_entry)
    else: # Si no se especifica longitud, usar todas las aprendidas
        progs_filtradas = all_learned_progs_data

    if not progs_filtradas:
        print(f"INFO (Aprendida): No hay progresiones aprendidas de longitud {num_acordes_deseado if num_acordes_deseado is not None else 'cualquiera'} para {estilo} - {clave_tonalidad_markov}.")
        return None, None

    # Usar una clave de índice más específica para el ciclado
    clave_indice_especifica = f"{estilo}_{clave_tonalidad_markov}_{num_acordes_deseado if num_acordes_deseado is not None else 'any'}"
    idx = _current_learned_prog_indices[estilo].get(clave_indice_especifica, 0) # Usar defaultdict interno

    if idx >= len(progs_filtradas):
        print(f"INFO (Aprendida): Todas las ({len(progs_filtradas)}) progresiones aprendidas (longitud: {num_acordes_deseado if num_acordes_deseado is not None else 'cualquiera'}) para {estilo} - {clave_tonalidad_markov} mostradas. Reiniciando índice para esta longitud.")
        idx = 0 # Resetear índice para esta combinación específica
    prog_data_entry = progs_filtradas[idx]
    _current_learned_prog_indices[estilo][clave_indice_especifica] = idx + 1

    acordes_originales_tuplas = prog_data_entry['chords'] # Deberían ser tuplas o "0"
    ritmo_original = prog_data_entry['rhythm']
    # Convertir acordes de tuplas a listas para el resto del sistema (excepto "0")
    acordes_listas_final = [listificar_acorde(ac_tupla) for ac_tupla in acordes_originales_tuplas]

    print(f"INFO (Aprendida): Obtenida progresión aprendida #{idx} (longitud real: {len(acordes_listas_final)}, deseada: {num_acordes_deseado if num_acordes_deseado is not None else 'cualquiera'}) para {estilo} - {clave_tonalidad_markov}")
    return acordes_listas_final, ritmo_original


def generar_progresion_markov(raiz, modo, estilo="normal", num_acordes_deseado=4):
    """Genera una progresión de acordes usando el modelo de Markov."""
    print(f"\n--- DEBUG: generar_progresion_markov ---")
    print(f"Request: Estilo='{estilo}', Raiz='{raiz}', Modo='{modo}', NumAcordes UI='{num_acordes_deseado}'")

    MIN_ACORDES_REALES_OBJETIVO = 4 # Mínimo de acordes no-silencio que intentaremos generar
    MAX_PROG_LENGTH_GENERAL = 16 # Límite superior general para la longitud de la progresión

    # Normalizar raíz y modo
    canonical_raiz_generator = _get_canonical_tonic_name_for_generator(raiz)
    canonical_modo_generator = modo.lower() if modo else "major" # Default a major si modo es None
    if not canonical_raiz_generator: canonical_raiz_generator = "c" # Default a C si raíz es None

    clave_tonalidad_markov = f"{canonical_raiz_generator} {canonical_modo_generator}"

    modelo_tonalidad = INFO_GENERO.get(estilo, {}).get(clave_tonalidad_markov)

    # Fallback si no hay modelo o está incompleto
    if not modelo_tonalidad or \
       not modelo_tonalidad.get("markov_transitions") or \
       not modelo_tonalidad.get("start_chords") or \
       not modelo_tonalidad.get("voicings_for_rn"):
        print(f"ADVERTENCIA (Markov): Modelo no encontrado/incompleto para '{estilo} - {clave_tonalidad_markov}'. Usando fallback diatónico.")
        long_fallback = num_acordes_deseado if num_acordes_deseado is not None else MIN_ACORDES_REALES_OBJETIVO
        # Asegurar que el fallback tenga al menos MIN_ACORDES_REALES_OBJETIVO si num_acordes_deseado es None o muy pequeño
        if num_acordes_deseado is None or num_acordes_deseado >= MIN_ACORDES_REALES_OBJETIVO:
            long_fallback = max(long_fallback, MIN_ACORDES_REALES_OBJETIVO)

        k_fallback = key.Key(canonical_raiz_generator, canonical_modo_generator)
        prog_numerals_fb = ['I', 'V', 'vi', 'IV'] if canonical_modo_generator == "major" else ['i', 'VI', 'III', 'VII'] # Simplificado
        fallback_prog = []
        for i in range(long_fallback):
            rn_str_fb = prog_numerals_fb[i % len(prog_numerals_fb)]
            try:
                chord_obj_fb = roman.RomanNumeral(rn_str_fb, k_fallback).pitches
                chord_m21_fb = m21_chord.Chord(chord_obj_fb) # Crear objeto Chord
                chord_m21_fb.closedPosition(forceOctave=3, inPlace=True) # Normalizar voicing
                fallback_prog.append([p.nameWithOctave for p in chord_m21_fb.pitches[:3]]) # Tomar hasta 3 notas
            except Exception as e_fb_inner:
                 print(f"Error en fallback diatónico interno: {e_fb_inner}")
                 fallback_prog.append(["C4", "E4", "G4"]) # Último recurso
        return fallback_prog, [1.0] * len(fallback_prog) # Ritmo simple para fallback

    # Determinar la longitud objetivo de la progresión
    longitud_objetivo_realizada = 0
    if num_acordes_deseado is None: # Si el usuario no especificó, intentar usar longitud de patrones rítmicos
        patrones_ritmo_genero = INFO_GENERO.get(estilo, {}).get("patrones_ritmicos", [])
        patrones_ritmo_listas = [list(p) for p in patrones_ritmo_genero if isinstance(p, tuple)] # Convertir tuplas a listas
        longitudes_patrones = [len(p) for p in patrones_ritmo_listas if isinstance(p, list) and p and len(p) >= MIN_ACORDES_REALES_OBJETIVO]

        if longitudes_patrones:
            longitud_objetivo_realizada = random.choice(longitudes_patrones)
        else: # Si no hay patrones rítmicos adecuados, elegir una longitud aleatoria común
            longitud_objetivo_realizada = random.choice([l for l in [4, 5, 6, 7, 8] if l >= MIN_ACORDES_REALES_OBJETIVO])
    else: # Si el usuario especificó, usar esa longitud
        longitud_objetivo_realizada = num_acordes_deseado

    # Asegurar que la longitud objetivo esté dentro de los límites razonables
    if num_acordes_deseado is None or num_acordes_deseado >= MIN_ACORDES_REALES_OBJETIVO:
        longitud_objetivo_realizada = max(longitud_objetivo_realizada, MIN_ACORDES_REALES_OBJETIVO)

    longitud_objetivo_realizada = min(longitud_objetivo_realizada, MAX_PROG_LENGTH_GENERAL) # Limitar la longitud máxima

    # Obtener un patrón rítmico a seguir y sincronizar la longitud con él
    ritmo_planificado = cargar_patron_ritmico_acordes(estilo, longitud_objetivo_realizada, True)
    if ritmo_planificado and isinstance(ritmo_planificado, list):
        if len(ritmo_planificado) >= MIN_ACORDES_REALES_OBJETIVO:
            longitud_objetivo_realizada = min(len(ritmo_planificado), MAX_PROG_LENGTH_GENERAL)
        else:
            ritmo_planificado = ritmo_planificado + [1.0] * (MIN_ACORDES_REALES_OBJETIVO - len(ritmo_planificado))
            longitud_objetivo_realizada = MIN_ACORDES_REALES_OBJETIVO
    else:
        ritmo_planificado = [1.0] * longitud_objetivo_realizada

    ritmo_planificado = ritmo_planificado[:longitud_objetivo_realizada]

    print(f"DEBUG (Markov): Longitud Objetivo Realizada: {longitud_objetivo_realizada}, Mín Acordes Reales Requeridos: {MIN_ACORDES_REALES_OBJETIVO}")

    plan_funcional, limites_frases = _construir_plan_funcional(longitud_objetivo_realizada, canonical_modo_generator)
    contadores_funcion_fallback = defaultdict(int)

    progresion_realizada_final = []
    secuencia_eventos_func_debug = [] # Para depuración
    acordes_reales_count = 0 # Contador de acordes que no son silencios
    funciones_usadas = set()

    # Elegir acorde inicial
    start_events_dict = modelo_tonalidad["start_chords"]
    evento_func_actual = None
    if start_events_dict:
        eventos_inicio_posibles = list(start_events_dict.keys())
        pesos_inicio = [float(start_events_dict.get(ev, 0)) for ev in eventos_inicio_posibles]

        # Priorizar eventos que no sean "0" si tienen peso
        if any(p > 0 for p in pesos_inicio):
            eventos_no_cero = [ev for i, ev in enumerate(eventos_inicio_posibles) if ev != "0" and pesos_inicio[i] > 0]
            pesos_no_cero = [pesos_inicio[i] for i, ev in enumerate(eventos_inicio_posibles) if ev != "0" and pesos_inicio[i] > 0]

            if eventos_no_cero and sum(pesos_no_cero) > 0:
                evento_func_actual = random.choices(eventos_no_cero, weights=pesos_no_cero, k=1)[0]
            else: # Si todos los pesos no cero son 0 (raro), o solo hay "0" con peso
                evento_func_actual = random.choices(eventos_inicio_posibles, weights=pesos_inicio, k=1)[0] if sum(pesos_inicio) > 0 else None


    if evento_func_actual is None: # Si no se pudo elegir un acorde inicial del modelo
        evento_func_actual = "I" if canonical_modo_generator == "major" else "i" # Default simple
        print(f"WARN (Markov): No se pudo elegir acorde inicial del modelo. Usando '{evento_func_actual}'.")
    
    if plan_funcional:
        funcion_inicio = _clasificar_funcion_armonica(evento_func_actual, canonical_modo_generator)
        if funcion_inicio != plan_funcional[0]:
            candidatos_tonica = [ev for ev in start_events_dict.keys() if _clasificar_funcion_armonica(ev, canonical_modo_generator) == plan_funcional[0]] if start_events_dict else []
            if candidatos_tonica:
                pesos_candidatos = [float(start_events_dict.get(ev, 0)) for ev in candidatos_tonica]
                if sum(pesos_candidatos) > 0:
                    evento_func_actual = random.choices(candidatos_tonica, weights=pesos_candidatos, k=1)[0]

    if ritmo_planificado and evento_func_actual == "0":
        dur_inicio = ritmo_planificado[0] if ritmo_planificado else None
        if dur_inicio is None or dur_inicio >= 0.75:
            eventos_no_cero_inicio = [ev for ev in start_events_dict.keys() if ev != "0"] if start_events_dict else []
            if eventos_no_cero_inicio:
                pesos_no_cero_inicio = [float(start_events_dict.get(ev, 0)) for ev in eventos_no_cero_inicio]
                if sum(pesos_no_cero_inicio) > 0:
                    evento_func_actual = random.choices(eventos_no_cero_inicio, weights=pesos_no_cero_inicio, k=1)[0]


    k_generacion = key.Key(canonical_raiz_generator, canonical_modo_generator) # Tonalidad para realizar RNs
    voicings_disponibles_rn_map = modelo_tonalidad.get("voicings_for_rn", {})

    # Para rellenar si la cadena de Markov se atasca
    diatonic_options_fill_markov = ['I', 'V', 'vi', 'IV'] if canonical_modo_generator == "major" else ['i', 'VI', 'III', 'VII']
    diatonic_options_fill_markov = diatonic_options_fill_markov[:]  # Copia para poder barajar
    random.shuffle(diatonic_options_fill_markov)
    fill_idx_markov = 0

    fue_nota_individual_anterior = False # Para evitar dos SN_ seguidas si es posible
    historial_eventos_recientes = deque(maxlen=5)
    ultimo_voicing_para_suavizado = None

    # Generar la progresión
    while len(progresion_realizada_final) < longitud_objetivo_realizada:
        secuencia_eventos_func_debug.append(evento_func_actual) # Guardar para depuración
        funcion_actual = _clasificar_funcion_armonica(evento_func_actual, canonical_modo_generator)
        if funcion_actual != "other":
            funciones_usadas.add(funcion_actual)
        voicing_realizado_actual = "0" # Default a silencio

        es_nota_individual_actual = isinstance(evento_func_actual, str) and evento_func_actual.startswith("SN_")

        if evento_func_actual == "0":
            voicing_realizado_actual = "0"
            
        elif es_nota_individual_actual: # Si es una nota individual (SN_Nota)
            voicing_realizado_actual = [evento_func_actual[3:]] # Guardar solo el nombre de la nota
            fue_nota_individual_anterior = True
        else: # Es un símbolo de RN o un voicing concreto (tupla)
            voicings_candidatos = []
            if isinstance(evento_func_actual, str): # Es un RN
                voicings_candidatos = voicings_disponibles_rn_map.get(evento_func_actual, [])
            elif isinstance(evento_func_actual, tuple): # Ya es un voicing
                voicings_candidatos = [evento_func_actual]

            if voicings_candidatos:
                voicing_elegido_tupla = random.choice(voicings_candidatos)
                voicing_realizado_actual = list(voicing_elegido_tupla) # Convertir a lista
            else: # Fallback: realizar RN diatónicamente si no hay voicing aprendido
                try:
                    if isinstance(evento_func_actual, str): # Solo si es un RN string
                        rn_obj_fb = roman.RomanNumeral(evento_func_actual, k_generacion)
                        pitches_rn_fb = rn_obj_fb.pitches
                        if pitches_rn_fb:
                            chord_m21_fb = m21_chord.Chord(pitches_rn_fb)
                            chord_m21_fb.closedPosition(forceOctave=3, inPlace=True)
                            voicing_realizado_actual = [p.nameWithOctave for p in chord_m21_fb.pitches[:3]]
                except Exception as e_realize_fb:
                    print(f"WARN (Markov Realize): Fallo al realizar RN '{evento_func_actual}' como fallback: {e_realize_fb}. Usando silencio.")
                    voicing_realizado_actual = "0"
            fue_nota_individual_anterior = False

        if voicing_realizado_actual != "0" and ultimo_voicing_para_suavizado:
            voicing_ajustado = suavizar_transicion_voicing(voicing_realizado_actual, ultimo_voicing_para_suavizado)
            if voicing_ajustado:
                voicing_realizado_actual = voicing_ajustado

        progresion_realizada_final.append(voicing_realizado_actual)
        if voicing_realizado_actual != "0":
            acordes_reales_count += 1
            if not es_nota_individual_actual:
                ultimo_voicing_para_suavizado = voicing_realizado_actual


        # Transición al siguiente estado
        evento_func_previo_loop = evento_func_actual # Guardar el evento actual antes de cambiarlo
        historial_eventos_recientes.append(evento_func_previo_loop)
        transiciones_posibles_dict = modelo_tonalidad["markov_transitions"].get(evento_func_previo_loop, {})
        evento_previo_norm = _normalizar_evento_markov(evento_func_previo_loop)
        indice_siguiente = len(progresion_realizada_final)
        duracion_siguiente = ritmo_planificado[indice_siguiente] if ritmo_planificado and indice_siguiente < len(ritmo_planificado) else None
        funcion_objetivo_siguiente = plan_funcional[indice_siguiente] if indice_siguiente < len(plan_funcional) else None

        siguientes_eventos_filtrados = []
        pesos_filtrados = []

        # Lógica para evitar dos SN_ seguidas si es posible
        if fue_nota_individual_anterior and transiciones_posibles_dict:
            # print(f"INFO (Markov): Evento anterior fue SN ('{evento_func_previo_loop}'). Filtrando siguientes para que sean acordes.")
            for ev_sig, peso_sig in transiciones_posibles_dict.items():
                if not (isinstance(ev_sig, str) and (ev_sig == "0" or ev_sig.startswith("SN_"))): # No silencio, no SN_
                    siguientes_eventos_filtrados.append(ev_sig)
                    pesos_filtrados.append(float(peso_sig))

            if not siguientes_eventos_filtrados: # Si no hay acordes, permitir silencios
                # print(f"WARN (Markov): No hay transiciones a acordes desde SN '{evento_func_previo_loop}'. Considerando silencios.")
                for ev_sig, peso_sig in transiciones_posibles_dict.items():
                     if ev_sig == "0": # Solo permitir silencio como siguiente si no hay acordes
                        siguientes_eventos_filtrados.append(ev_sig)
                        pesos_filtrados.append(float(peso_sig))

        if siguientes_eventos_filtrados and sum(pesos_filtrados) > 0 :
            pesos_filtrados = ajustar_pesos_para_diversidad(siguientes_eventos_filtrados, pesos_filtrados, historial_eventos_recientes, evento_func_previo_loop)
            pesos_filtrados = _ajustar_pesos_por_plan_funcional(siguientes_eventos_filtrados, pesos_filtrados, funcion_objetivo_siguiente, canonical_modo_generator)
            pesos_filtrados = _ajustar_pesos_por_transicion_musical(siguientes_eventos_filtrados, pesos_filtrados, evento_func_previo_loop, canonical_modo_generator, k_generacion, historial_eventos_recientes)
            pesos_filtrados = ajustar_pesos_por_patron_ritmico(siguientes_eventos_filtrados, pesos_filtrados, duracion_siguiente, evento_previo_norm, fue_nota_individual_anterior)
            if sum(pesos_filtrados) <= 0:
                pesos_filtrados = [1.0] * len(siguientes_eventos_filtrados)
            evento_func_actual = random.choices(siguientes_eventos_filtrados, weights=pesos_filtrados, k=1)[0]
            # print(f"INFO (Markov): Desde SN, elegido (filtrado): {evento_func_actual}")

        elif transiciones_posibles_dict: # Si no fue SN anterior o el filtro no dio resultados, usar todas las transiciones
            siguientes_eventos_orig = list(transiciones_posibles_dict.keys())
            pesos_transicion_orig = [float(transiciones_posibles_dict.get(ev, 0)) for ev in siguientes_eventos_orig]
            if sum(pesos_transicion_orig) > 0:
                pesos_transicion_orig = ajustar_pesos_para_diversidad(siguientes_eventos_orig, pesos_transicion_orig, historial_eventos_recientes, evento_func_previo_loop)
                pesos_transicion_orig = _ajustar_pesos_por_plan_funcional(siguientes_eventos_orig, pesos_transicion_orig, funcion_objetivo_siguiente, canonical_modo_generator)
                pesos_transicion_orig = _ajustar_pesos_por_transicion_musical(siguientes_eventos_orig, pesos_transicion_orig, evento_func_previo_loop, canonical_modo_generator, k_generacion, historial_eventos_recientes)
                funcion_actual = _clasificar_funcion_armonica(evento_func_previo_loop, canonical_modo_generator)
                pesos_validados = []
                for ev, peso in zip(siguientes_eventos_orig, pesos_transicion_orig):
                    funcion_siguiente = _clasificar_funcion_armonica(ev, canonical_modo_generator)
                    if funcion_siguiente in ["tonic", "predominant", "dominant"]:
                        if funcion_actual == "tonic" and funcion_siguiente not in ["predominant", "tonic"]:
                            peso *= 0.3
                        elif funcion_actual == "predominant" and funcion_siguiente not in ["dominant", "tonic"]:
                            peso *= 0.3
                        elif funcion_actual == "dominant" and funcion_siguiente not in ["tonic", "predominant"]:
                            peso *= 0.3
                    pesos_validados.append(peso)
                pesos_transicion_orig = pesos_validados

                pesos_transicion_orig = ajustar_pesos_por_patron_ritmico(siguientes_eventos_orig, pesos_transicion_orig, duracion_siguiente, evento_previo_norm, fue_nota_individual_anterior)
                if sum(pesos_transicion_orig) <= 0:
                    pesos_transicion_orig = [1.0] * len(siguientes_eventos_orig)
                evento_func_actual = random.choices(siguientes_eventos_orig, weights=pesos_transicion_orig, k=1)[0]
            else: # No hay transiciones válidas con peso
                evento_func_actual = None
        else: # No hay transiciones definidas para el estado actual
            evento_func_actual = None

        # Si no se puede transicionar, decidir si terminar o rellenar
        if evento_func_actual is None:
            # Si aún no hemos alcanzado la longitud deseada Y (no hemos alcanzado el mínimo de acordes reales O el usuario no especificó longitud)
            if len(progresion_realizada_final) < longitud_objetivo_realizada and \
               (acordes_reales_count < MIN_ACORDES_REALES_OBJETIVO or num_acordes_deseado is None):

                if fue_nota_individual_anterior: # Si el último fue SN, intentar un acorde diatónico
                     evento_func_actual = _seleccionar_diatonico_por_funcion(funcion_objetivo_siguiente, canonical_modo_generator, contadores_funcion_fallback, diatonic_options_fill_markov, fill_idx_markov)
                else: # Si no, rellenar con diatónico
                    evento_func_actual = _seleccionar_diatonico_por_funcion(funcion_objetivo_siguiente, canonical_modo_generator, contadores_funcion_fallback, diatonic_options_fill_markov, fill_idx_markov)
                fill_idx_markov += 1
            else: # Ya hemos generado suficientes o alcanzado la longitud deseada
                break # Salir del bucle while

    # Rellenar con silencios si es necesario para alcanzar la longitud objetivo
    if len(progresion_realizada_final) < longitud_objetivo_realizada:
        deficit = longitud_objetivo_realizada - len(progresion_realizada_final)
        progresion_realizada_final.extend(["0"] * deficit)
        if ritmo_planificado and len(ritmo_planificado) < longitud_objetivo_realizada:
            ultimo_valor_ritmo = ritmo_planificado[-1] if ritmo_planificado else 1.0
            ritmo_planificado.extend([ultimo_valor_ritmo] * (longitud_objetivo_realizada - len(ritmo_planificado)))
    # Asegurar un mínimo de acordes reales si el usuario no especificó longitud
    if num_acordes_deseado is None:
        while acordes_reales_count < MIN_ACORDES_REALES_OBJETIVO and len(progresion_realizada_final) < MAX_PROG_LENGTH_GENERAL:
            indice_actual_fill = len(progresion_realizada_final)
            funcion_objetivo_fill = plan_funcional[indice_actual_fill] if indice_actual_fill < len(plan_funcional) else None
            evento_func_relleno_post = _seleccionar_diatonico_por_funcion(funcion_objetivo_fill, canonical_modo_generator, contadores_funcion_fallback, diatonic_options_fill_markov, fill_idx_markov)
            fill_idx_markov += 1
            voicing_post = "0"
            try:
                rn_obj_post = roman.RomanNumeral(evento_func_relleno_post, k_generacion)
                voicings_aprendidos_post = voicings_disponibles_rn_map.get(evento_func_relleno_post, [])
                if voicings_aprendidos_post:
                    voicing_post = list(random.choice(voicings_aprendidos_post))
                else: # Realizar diatónicamente
                    chord_m21_post = m21_chord.Chord(rn_obj_post.pitches)
                    chord_m21_post.closedPosition(forceOctave=3, inPlace=True)
                    voicing_post = [p.nameWithOctave for p in chord_m21_post.pitches[:3]]
            except: pass # Ignorar error y mantener voicing_post como "0"

            if voicing_post != "0":
                progresion_realizada_final.append(voicing_post)
                acordes_reales_count += 1
            else: # Si no se pudo realizar, añadir silencio para avanzar
                progresion_realizada_final.append("0")
            if ritmo_planificado:
                valor_extendido = ritmo_planificado[-1] if ritmo_planificado else 1.0
                ritmo_planificado.append(valor_extendido)
            else:
                ritmo_planificado = [1.0] * len(progresion_realizada_final)
        # Si aún no se alcanza el mínimo, rellenar con silencios
        if len(progresion_realizada_final) < MIN_ACORDES_REALES_OBJETIVO:
            faltantes = MIN_ACORDES_REALES_OBJETIVO - len(progresion_realizada_final)
            progresion_realizada_final.extend(["0"] * faltantes)
            if ritmo_planificado:
                valor_extendido = ritmo_planificado[-1] if ritmo_planificado else 1.0
                ritmo_planificado.extend([valor_extendido] * faltantes)
            else:
                ritmo_planificado = [1.0] * len(progresion_realizada_final)

    _reforzar_cadencias_por_frase(progresion_realizada_final, secuencia_eventos_func_debug, limites_frases, canonical_modo_generator, k_generacion, voicings_disponibles_rn_map)

    if not _validar_progresion_markov(secuencia_eventos_func_debug, canonical_modo_generator, k_generacion, limites_frases):
        _reparar_progresion_markov(secuencia_eventos_func_debug, plan_funcional, canonical_modo_generator, k_generacion)
        progresion_realizada_final = _reconstruir_voicings_desde_eventos(secuencia_eventos_func_debug, k_generacion, voicings_disponibles_rn_map)
        _reforzar_cadencias_por_frase(progresion_realizada_final, secuencia_eventos_func_debug, limites_frases, canonical_modo_generator, k_generacion, voicings_disponibles_rn_map)

    if not _validar_progresion_markov(secuencia_eventos_func_debug, canonical_modo_generator, k_generacion, limites_frases):
        progresion_realizada_final, secuencia_eventos_func_debug = _construir_progresion_diatonica_desde_plan(plan_funcional, canonical_modo_generator, k_generacion, voicings_disponibles_rn_map)
        _reforzar_cadencias_por_frase(progresion_realizada_final, secuencia_eventos_func_debug, limites_frases, canonical_modo_generator, k_generacion, voicings_disponibles_rn_map)

    _asegurar_cadencia_final(progresion_realizada_final, secuencia_eventos_func_debug, canonical_modo_generator, k_generacion, voicings_disponibles_rn_map)
    acordes_reales_count = sum(1 for ac in progresion_realizada_final if ac != "0" and not (isinstance(ac, str) and ac.startswith("SN_")))
    funciones_usadas = {func for func in (_clasificar_funcion_armonica(ev, canonical_modo_generator) for ev in secuencia_eventos_func_debug if ev) if func and func != "other"}
             


    # Ajustar a la longitud deseada si se especificó num_acordes_deseado
    if num_acordes_deseado is not None and len(progresion_realizada_final) > num_acordes_deseado:
        progresion_realizada_final = progresion_realizada_final[:num_acordes_deseado]

    if ritmo_planificado:
            ritmo_planificado = ritmo_planificado[:num_acordes_deseado]

    # Ajustar el ritmo final a la longitud real generada
    if ritmo_planificado:
        if len(ritmo_planificado) < len(progresion_realizada_final):
            ultimo_valor_ritmo = ritmo_planificado[-1] if ritmo_planificado else 1.0
            ritmo_planificado.extend([ultimo_valor_ritmo] * (len(progresion_realizada_final) - len(ritmo_planificado)))
        ritmo_final = ritmo_planificado[:len(progresion_realizada_final)]
    else:
        ritmo_final = [1.0] * len(progresion_realizada_final)
        
        # Asegurar cadencia final dominante–tónica
        _asegurar_cadencia_final(
            progresion_realizada_final,
            secuencia_eventos_func_debug,
            canonical_modo_generator,
            k_generacion,
            voicings_disponibles_rn_map
        )

    print(f"DEBUG (Markov): Progresión final: {progresion_realizada_final} (Reales: {sum(1 for ac in progresion_realizada_final if ac != '0')})")
    print(f"DEBUG (Markov): Funciones cubiertas: {sorted(funciones_usadas)}")
    
    return progresion_realizada_final, ritmo_final


def generar_progresion_acordes_smart(raiz, modo, estilo, num_acordes_deseado_ui, usar_markov_directamente=False):
    """
    Genera una progresión de acordes de forma inteligente, priorizando
    progresiones aprendidas o usando Markov como fallback.
    """
    global _generator_mode
    canonical_raiz_generator = _get_canonical_tonic_name_for_generator(raiz)
    canonical_modo_generator = modo.lower() if modo else "major"
    if not canonical_raiz_generator: canonical_raiz_generator = "c"

    clave_tonalidad = f"{canonical_raiz_generator} {canonical_modo_generator}"

    acordes_generados = None
    ritmo_asociado = None
    source_info = ""
    mode_type = None

    print(f"INFO (Smart): Solicitud para {estilo}, {raiz if raiz else '?'} {modo if modo else '?'} ({clave_tonalidad}), Longitud UI: {num_acordes_deseado_ui if num_acordes_deseado_ui is not None else 'Sin límite'}.")

    if usar_markov_directamente:
        print(f"INFO (Smart): Forzando generación Markov.")
        acordes_generados, ritmo_asociado = generar_progresion_markov(canonical_raiz_generator, canonical_modo_generator, estilo, num_acordes_deseado_ui)
        source_info = "Markov (forzado)"
        mode_type = "markov"
    else:
        # MODIFICADO: Cambiar probabilidad
        prob_intentar_aprendido_primero = 0.9 # 90% de probabilidad de intentar aprendido primero

        if random.random() < prob_intentar_aprendido_primero:
            print(f"INFO (Smart): Intentando obtener progresión aprendida primero ({prob_intentar_aprendido_primero*100:.0f}% de probabilidad).")
            acordes_generados, ritmo_asociado = obtener_progresion_aprendida(estilo, canonical_raiz_generator, canonical_modo_generator, num_acordes_deseado_ui)
            source_info = "Aprendida (intento principal)"
            if acordes_generados:
                mode_type = "learned"

            if acordes_generados:
                # Si se especificó una longitud y la aprendida no coincide, se considera un fallo para este intento
                if num_acordes_deseado_ui is not None and len(acordes_generados) != num_acordes_deseado_ui:
                    print(f"AVISO (Smart): Prog. aprendida ({len(acordes_generados)}) no coincide con longitud deseada ({num_acordes_deseado_ui}). Intentando Markov como fallback.")
                    acordes_generados = None # Forzar fallback a Markov

            if not acordes_generados: # Si falló el intento aprendido o la longitud no coincidió
                print(f"INFO (Smart): Falló intento aprendido o longitud incorrecta. Usando Markov como fallback.")
                acordes_generados, ritmo_asociado = generar_progresion_markov(canonical_raiz_generator, canonical_modo_generator, estilo, num_acordes_deseado_ui)
                source_info = "Markov (fallback de aprendido)"
                mode_type = "markov"
        else: # Intentar Markov primero (10% de probabilidad)
            print(f"INFO (Smart): Intentando generar con Markov primero ({(1-prob_intentar_aprendido_primero)*100:.0f}% de probabilidad).")
            acordes_generados, ritmo_asociado = generar_progresion_markov(canonical_raiz_generator, canonical_modo_generator, estilo, num_acordes_deseado_ui)
            source_info = "Markov (intento principal)"
            if acordes_generados:
                mode_type = "markov"

            if not acordes_generados: # Si Markov falló
                print(f"INFO (Smart): Falló intento de Markov. Usando progresión aprendida como fallback.")
                acordes_generados, ritmo_asociado = obtener_progresion_aprendida(estilo, canonical_raiz_generator, canonical_modo_generator, num_acordes_deseado_ui)
                source_info = "Aprendida (fallback de Markov)"
                if acordes_generados:
                    mode_type = "learned"
                if acordes_generados and num_acordes_deseado_ui is not None and len(acordes_generados) != num_acordes_deseado_ui:
                     print(f"AVISO (Smart): Prog. aprendida de fallback ({len(acordes_generados)}) no coincide con longitud deseada ({num_acordes_deseado_ui}). Puede llevar a fallback crítico.")
                     acordes_generados = None # Podría forzar un fallback crítico si la aprendida tampoco cumple

    # Fallback crítico si NADA funcionó
    if acordes_generados is None:
        print(f"FALLBACK CRÍTICO (Smart): No se pudo generar ninguna progresión para {estilo} {clave_tonalidad}. Devolviendo C Mayor simple.")
        num_fallback_len = num_acordes_deseado_ui if num_acordes_deseado_ui is not None else 4
        acordes_generados = [["C4", "E4", "G4"]] * num_fallback_len # Acorde de C Mayor simple
        ritmo_asociado = [1.0] * num_fallback_len # Ritmo simple
        source_info = "Fallback Crítico"
        mode_type = "fallback"

    # Asegurar que la longitud final coincida con la deseada si se especificó
    if num_acordes_deseado_ui is not None:
        if len(acordes_generados) != num_acordes_deseado_ui:
            print(f"ALERTA (Smart): Longitud final ({len(acordes_generados)}) de '{source_info}' no coincide con deseada ({num_acordes_deseado_ui}). Ajustando...")
            if len(acordes_generados) > num_acordes_deseado_ui:
                acordes_generados = acordes_generados[:num_acordes_deseado_ui]
                if ritmo_asociado and len(ritmo_asociado) > num_acordes_deseado_ui:
                    ritmo_asociado = ritmo_asociado[:num_acordes_deseado_ui]
            else: # Si es más corta, rellenar con silencios
                padding_needed = num_acordes_deseado_ui - len(acordes_generados)
                acordes_generados.extend(["0"] * padding_needed)
                if ritmo_asociado:
                    ritmo_asociado.extend([1.0] * padding_needed)
                else: # Si el ritmo era None, crear uno nuevo
                    ritmo_asociado = [1.0] * num_acordes_deseado_ui
        # Asegurar que el ritmo siempre coincida con la longitud de acordes final
        if ritmo_asociado is None or len(ritmo_asociado) != len(acordes_generados):
             print(f"INFO (Smart): Ajustando ritmo final para coincidir con {len(acordes_generados)} acordes.")
             ritmo_asociado = cargar_patron_ritmico_acordes(estilo, len(acordes_generados))

    if not mode_type:
        mode_type = "unknown"

    previous_mode = _generator_mode[estilo].get(clave_tonalidad, "learned")
    _generator_mode[estilo][clave_tonalidad] = mode_type
    if mode_type == "learned" and previous_mode != "learned":
        reset_learned_prog_index(estilo, canonical_raiz_generator, canonical_modo_generator)

    global _ultima_progresion_generada, _ultimo_ritmo_generado, _ultimo_genero, _ultima_tonalidad_str, _ultima_fuente_generada, _ultimo_tipo_generacion
    _ultima_fuente_generada = source_info or ""
    _ultimo_tipo_generacion = mode_type

    print(f"INFO (Smart): Progresión final de '{source_info}'. Longitud: {len(acordes_generados)}. Ritmo: {ritmo_asociado}")
    _ultima_progresion_generada = acordes_generados
    _ultimo_ritmo_generado = ritmo_asociado
    _ultimo_genero = estilo 
    _ultima_tonalidad_str = clave_tonalidad 
    
    return acordes_generados, ritmo_asociado


def transponer_progresion(lista_acordes, semitonos, lista_melodia=None):
    """Transpone una lista de acordes y una lista de melodía (opcional) por un número de semitonos."""
    acordes_transpuestos = []
    for item_acorde in lista_acordes:
        if isinstance(item_acorde, list): # Es un voicing de notas
            try:
                # Asegurar que todas las notas tengan octava antes de transponer
                notas_con_octava_original_ac = []
                for n_str in item_acorde:
                    if not re.search(r"\d", n_str): # Si no tiene número (octava)
                        notas_con_octava_original_ac.append(f"{n_str}4") # Añadir octava 4 por defecto
                    else:
                        notas_con_octava_original_ac.append(n_str)

                notas_t = [pitch.Pitch(n).transpose(semitonos).nameWithOctave for n in notas_con_octava_original_ac]
                acordes_transpuestos.append(notas_t)
            except Exception as e_ac:
                print(f"Advertencia (transponer_progresion): No se pudo transponer nota de acorde {item_acorde}: {e_ac}. Se mantiene original.")
                acordes_transpuestos.append(list(item_acorde)) # Mantener original si falla
        else: # Es un silencio "0" o un nombre de acorde que no se transpondrá aquí
            acordes_transpuestos.append(item_acorde)

    melodia_transpuesta = []
    if lista_melodia:
        for nombre_nota_mel, dur_nota_mel in lista_melodia:
            if nombre_nota_mel == "0" or nombre_nota_mel == "N/A": # Silencio
                melodia_transpuesta.append(("0", dur_nota_mel))
            else:
                try:
                    # Asegurar octava para la nota de melodía
                    nota_mel_con_octava_original = nombre_nota_mel
                    if not re.search(r"\d", nombre_nota_mel): # Si no tiene número (octava)
                        nota_mel_con_octava_original = f"{nombre_nota_mel}4" # Añadir octava 4 por defecto

                    p_mel = pitch.Pitch(nota_mel_con_octava_original)
                    p_mel.transpose(semitonos, inPlace=True)
                    melodia_transpuesta.append((p_mel.nameWithOctave, dur_nota_mel))
                except Exception as e_mel:
                    print(f"Advertencia (transponer_progresion): No se pudo transponer nota de melodía {nombre_nota_mel}: {e_mel}. Se mantiene original.")
                    melodia_transpuesta.append((nombre_nota_mel, dur_nota_mel)) # Mantener original

    return acordes_transpuestos, melodia_transpuesta


def limpiar_nombre_acorde(nombre_acorde_original):
    """Limpia y valida un nombre de acorde."""
    if isinstance(nombre_acorde_original, list): # Si ya es una lista de notas (voicing), no hacer nada
        return nombre_acorde_original
    nombre = nombre_acorde_original.strip().replace("♯", "#").replace("♭", "b")
    try:
        # Intentar crear un ChordSymbol para validar. Si falla, no es un nombre de acorde estándar.
        harmony.ChordSymbol(nombre)
        return nombre # Devuelve el nombre limpio si es válido
    except Exception:
        # Si no es un ChordSymbol válido, podría ser un número romano o algo más. Devolver original.
        return nombre_acorde_original

def puntuar_acordes_positivamente():
    """Llama a la función de refuerzo con los datos de la última progresión generada."""
    if _ultima_progresion_generada and _ultimo_genero and _ultima_tonalidad_str:
        print(f"Reforzando POSITIVAMENTE para género: {_ultimo_genero}, tonalidad: {_ultima_tonalidad_str}")
        progresion_tuplas = [
            tuplificar_acorde_feedback(acorde)
            for acorde in _ultima_progresion_generada
            if acorde not in (None, "")
        ]

        if not progresion_tuplas:
            print("Advertencia: Progresión vacía, no se envía feedback negativo.")
            return
        
        reforzar_progresion_con_feedback(
            _ultimo_genero,
            _ultima_tonalidad_str,
            progresion_tuplas,
            _ultimo_ritmo_generado or [],
            False
        )
    else:
        print("No hay suficiente información (progresión/género/tonalidad) para puntuar.")

def puntuar_acordes_negativamente():
    """Llama a la función de refuerzo con los datos de la última progresión generada."""
    if _ultima_progresion_generada and _ultimo_genero and _ultima_tonalidad_str:
        print(f"Reforzando NEGATIVAMENTE para género: {_ultimo_genero}, tonalidad: {_ultima_tonalidad_str}")
        progresion_tuplas = [
            tuplificar_acorde_feedback(acorde)
            for acorde in _ultima_progresion_generada
            if acorde not in (None, "")
        ]

        if not progresion_tuplas:
            print("Advertencia: Progresión vacía, no se envía feedback positivo.")
            return
        
        reforzar_progresion_con_feedback(
            _ultimo_genero,
            _ultima_tonalidad_str,
            progresion_tuplas,
            _ultimo_ritmo_generado or [],
            True
        )
    else:
        print("No hay suficiente información (progresión/género/tonalidad) para puntuar.")

if __name__ == "__main__":
    print("\nProbando generación de progresión SMART:")
    if INFO_GENERO:
        estilo_prueba = "reggaeton" # Cambia esto al género que quieras probar
        clave_tonalidad_prueba = None
        # Buscar una tonalidad entrenada para el estilo de prueba
        if estilo_prueba in INFO_GENERO and INFO_GENERO[estilo_prueba]:
            for kt, data_t in INFO_GENERO[estilo_prueba].items():
                if kt != "patrones_ritmicos" and data_t.get("learned_progressions") and data_t.get("markov_transitions"):
                    clave_tonalidad_prueba = kt
                    break
            if not clave_tonalidad_prueba and estilo_prueba in INFO_GENERO and INFO_GENERO[estilo_prueba]: # Fallback si no hay learned_progressions
                 for kt in INFO_GENERO[estilo_prueba].keys():
                     if kt != "patrones_ritmicos": clave_tonalidad_prueba = kt; break

        if clave_tonalidad_prueba:
            raiz_p, modo_p = clave_tonalidad_prueba.split()
            print(f"\n--- Probando generación SMART (90/10) para {estilo_prueba} en {raiz_p} {modo_p} ---")
            for i in range(10): # Generar 10 progresiones para ver la mezcla
                print(f"Intento {i+1}:")
                acordes_gen, ritmo_gen = generar_progresion_acordes_smart(raiz_p, modo_p, estilo_prueba, None, usar_markov_directamente=False)
                if acordes_gen:
                    print(f"  Progresión: {acordes_gen}")
                    print(f"  Ritmo: {ritmo_gen}")
                else:
                    print("  No se pudo generar/obtener progresión.")

            print(f"\n--- Forzando generación MARKOV para {estilo_prueba} en {raiz_p} {modo_p} (4 acordes) ---")
            acordes_markov, ritmo_markov = generar_progresion_acordes_smart(raiz_p, modo_p, estilo_prueba, 4, usar_markov_directamente=True)
            if acordes_markov:
                print(f"  Progresión Markov: {acordes_markov}")
                print(f"  Ritmo Markov: {ritmo_markov}")
        else:
            print(f"No se encontraron tonalidades entrenadas con datos para '{estilo_prueba}'. Ejecuta autoentrenador.py.")
    else:
        print("INFO_GENERO está vacío. Ejecuta autoentrenador.py primero.")

