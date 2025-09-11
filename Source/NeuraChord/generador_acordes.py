# generador_acordes.py
import random
import re
import os
import sys
import pprint
from music21 import key, roman, pitch, harmony, chord as m21_chord
import importlib.util
from collections import defaultdict # Para _current_learned_prog_indices

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

    print(f"DEBUG (Markov): Longitud Objetivo Realizada: {longitud_objetivo_realizada}, Mín Acordes Reales Requeridos: {MIN_ACORDES_REALES_OBJETIVO}")


    progresion_realizada_final = []
    secuencia_eventos_func_debug = [] # Para depuración
    acordes_reales_count = 0 # Contador de acordes que no son silencios

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


    k_generacion = key.Key(canonical_raiz_generator, canonical_modo_generator) # Tonalidad para realizar RNs
    voicings_disponibles_rn_map = modelo_tonalidad.get("voicings_for_rn", {})

    # Para rellenar si la cadena de Markov se atasca
    diatonic_options_fill_markov = ['I', 'V', 'vi', 'IV'] if canonical_modo_generator == "major" else ['i', 'VI', 'III', 'VII']
    fill_idx_markov = 0

    fue_nota_individual_anterior = False # Para evitar dos SN_ seguidas si es posible

    # Generar la progresión
    while len(progresion_realizada_final) < longitud_objetivo_realizada:
        secuencia_eventos_func_debug.append(evento_func_actual) # Guardar para depuración
        voicing_realizado_actual = "0" # Default a silencio

        es_nota_individual_actual = isinstance(evento_func_actual, str) and evento_func_actual.startswith("SN_")

        if evento_func_actual == "0":
            voicing_realizado_actual = "0"
            fue_nota_individual_anterior = False
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

        progresion_realizada_final.append(voicing_realizado_actual)
        if voicing_realizado_actual != "0":
            acordes_reales_count += 1

        # Transición al siguiente estado
        evento_func_previo_loop = evento_func_actual # Guardar el evento actual antes de cambiarlo
        transiciones_posibles_dict = modelo_tonalidad["markov_transitions"].get(evento_func_previo_loop, {})

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
             evento_func_actual = random.choices(siguientes_eventos_filtrados, weights=pesos_filtrados, k=1)[0]
             # print(f"INFO (Markov): Desde SN, elegido (filtrado): {evento_func_actual}")
        elif transiciones_posibles_dict: # Si no fue SN anterior o el filtro no dio resultados, usar todas las transiciones
            siguientes_eventos_orig = list(transiciones_posibles_dict.keys())
            pesos_transicion_orig = [float(transiciones_posibles_dict.get(ev, 0)) for ev in siguientes_eventos_orig]
            if sum(pesos_transicion_orig) > 0:
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
                     evento_func_actual = diatonic_options_fill_markov[fill_idx_markov % len(diatonic_options_fill_markov)]
                     fill_idx_markov += 1
                     # print(f"INFO (Markov): Desde SN, callejón sin salida, rellenando con acorde diatónico '{evento_func_actual}'.")
                else: # Si no, rellenar con diatónico
                    evento_func_actual = diatonic_options_fill_markov[fill_idx_markov % len(diatonic_options_fill_markov)]
                    fill_idx_markov += 1
                    # print(f"INFO (Markov): Callejón sin salida o fin de cadena, rellenando con '{evento_func_actual}'.")
            else: # Ya hemos generado suficientes o alcanzado la longitud deseada
                break # Salir del bucle while

    # Rellenar con silencios si es necesario para alcanzar la longitud objetivo
    if len(progresion_realizada_final) < longitud_objetivo_realizada:
        progresion_realizada_final.extend(["0"] * (longitud_objetivo_realizada - len(progresion_realizada_final)))

    # Asegurar un mínimo de acordes reales si el usuario no especificó longitud
    if num_acordes_deseado is None:
        while acordes_reales_count < MIN_ACORDES_REALES_OBJETIVO and len(progresion_realizada_final) < MAX_PROG_LENGTH_GENERAL:
            evento_func_relleno_post = diatonic_options_fill_markov[fill_idx_markov % len(diatonic_options_fill_markov)]
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
        # Si aún no se alcanza el mínimo, rellenar con silencios
        if len(progresion_realizada_final) < MIN_ACORDES_REALES_OBJETIVO:
             progresion_realizada_final.extend(["0"] * (MIN_ACORDES_REALES_OBJETIVO - len(progresion_realizada_final)))


    # Ajustar a la longitud deseada si se especificó num_acordes_deseado
    if num_acordes_deseado is not None and len(progresion_realizada_final) > num_acordes_deseado:
        progresion_realizada_final = progresion_realizada_final[:num_acordes_deseado]

    # Cargar o generar ritmo
    ritmo_final = cargar_patron_ritmico_acordes(estilo, len(progresion_realizada_final), True) # True para preferir simples para Markov

    print(f"DEBUG (Markov): Progresión final: {progresion_realizada_final} (Reales: {sum(1 for ac in progresion_realizada_final if ac != '0')})")
    print(f"DEBUG (Markov): Ritmo: {ritmo_final}")
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

    print(f"INFO (Smart): Solicitud para {estilo}, {raiz if raiz else '?'} {modo if modo else '?'} ({clave_tonalidad}), Longitud UI: {num_acordes_deseado_ui if num_acordes_deseado_ui is not None else 'Sin límite'}.")

    if usar_markov_directamente:
        print(f"INFO (Smart): Forzando generación Markov.")
        acordes_generados, ritmo_asociado = generar_progresion_markov(canonical_raiz_generator, canonical_modo_generator, estilo, num_acordes_deseado_ui)
        source_info = "Markov (forzado)"
    else:
        # MODIFICADO: Cambiar probabilidad
        prob_intentar_aprendido_primero = 0.9 # 90% de probabilidad de intentar aprendido primero

        if random.random() < prob_intentar_aprendido_primero:
            print(f"INFO (Smart): Intentando obtener progresión aprendida primero ({prob_intentar_aprendido_primero*100:.0f}% de probabilidad).")
            acordes_generados, ritmo_asociado = obtener_progresion_aprendida(estilo, canonical_raiz_generator, canonical_modo_generator, num_acordes_deseado_ui)
            source_info = "Aprendida (intento principal)"

            if acordes_generados:
                # Si se especificó una longitud y la aprendida no coincide, se considera un fallo para este intento
                if num_acordes_deseado_ui is not None and len(acordes_generados) != num_acordes_deseado_ui:
                    print(f"AVISO (Smart): Prog. aprendida ({len(acordes_generados)}) no coincide con longitud deseada ({num_acordes_deseado_ui}). Intentando Markov como fallback.")
                    acordes_generados = None # Forzar fallback a Markov

            if not acordes_generados: # Si falló el intento aprendido o la longitud no coincidió
                print(f"INFO (Smart): Falló intento aprendido o longitud incorrecta. Usando Markov como fallback.")
                acordes_generados, ritmo_asociado = generar_progresion_markov(canonical_raiz_generator, canonical_modo_generator, estilo, num_acordes_deseado_ui)
                source_info = "Markov (fallback de aprendido)"
        else: # Intentar Markov primero (10% de probabilidad)
            print(f"INFO (Smart): Intentando generar con Markov primero ({(1-prob_intentar_aprendido_primero)*100:.0f}% de probabilidad).")
            acordes_generados, ritmo_asociado = generar_progresion_markov(canonical_raiz_generator, canonical_modo_generator, estilo, num_acordes_deseado_ui)
            source_info = "Markov (intento principal)"

            if not acordes_generados: # Si Markov falló
                print(f"INFO (Smart): Falló intento de Markov. Usando progresión aprendida como fallback.")
                acordes_generados, ritmo_asociado = obtener_progresion_aprendida(estilo, canonical_raiz_generator, canonical_modo_generator, num_acordes_deseado_ui)
                source_info = "Aprendida (fallback de Markov)"
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


    print(f"INFO (Smart): Progresión final de '{source_info}'. Longitud: {len(acordes_generados)}. Ritmo: {ritmo_asociado}")
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