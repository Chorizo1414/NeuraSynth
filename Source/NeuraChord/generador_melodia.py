# generador_melodia.py
import random
import re
from music21 import note, pitch, scale, harmony, stream, interval, key, roman, chord as m21_chord

from generador_acordes import nota_equivalente

class ParametrosMelodicos:
    # Esta clase ahora es más simple, ya que la lógica principal la dictan los perfiles de género.
    def __init__(self, bpm=120, octava_melodia_min=4, octava_melodia_max=5, pulsos_por_compas=4):
        self.bpm = bpm
        self.octava_melodia_min = octava_melodia_min
        self.octava_melodia_max = octava_melodia_max
        self.pulsos_por_compas = pulsos_por_compas
        self.melodia_grid_unit_ql = 0.25  # Semicorchea como base

# --- ¡NUEVO! CEREBRO MUSICAL: PERFILES DE GÉNERO v5 ---
PERFILES_GENERO = {
    "pop": {
        "tecnicas_preferidas": [("motivo", 0.85), ("arpegio", 0.15)],
        "prob_variacion_A": 0.5,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.7, # Ligeramente más denso
        # Ritmo Pop: Pegadizo, mezcla corcheas, semis, negras y silencios
        "complejidad_ritmica": [2, 1, 1, 2, 0, 2, 4, 1, 1, 2, 0, 4], # 0 representa silencio de semicorchea
        "complejidad_motivo": 3,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.3, # Más notas de paso para fluidez
        "intervalos_preferidos": [(1, 0.4), (2, 0.4), (3, 0.1), (4, 0.05), (5, 0.05)], # Favorece pasos (1, 2 semitonos)
        "prob_nota_especial": 0.0, # Sin notas especiales
    },
    "lofi": {
        "tecnicas_preferidas": [("motivo", 0.95), ("arpegio", 0.05)],
        "prob_variacion_A": 0.6,
        "estructura_frase": "continua",
        "densidad_notas": 0.4, # Muy espaciado
        # Ritmo Lofi: Lento, notas largas, silencios, algo de swing/shuffle implícito
        "complejidad_ritmica": [4, 4, 0, 8, 2, 2, 0, 4, 8],
        "complejidad_motivo": 2,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.2,
        "intervalos_preferidos": [(1, 0.3), (2, 0.3), (3, 0.15), (4, 0.1), (5, 0.1), (7, 0.05)], # Mezcla pasos y saltos
        "prob_nota_especial": 0.15, # Disonancias suaves (ej. 7ª mayor sobre acorde menor)
        "notas_especiales": [11], # Usar 7ª mayor (11 semitonos) a veces
    },
    "r&b": {
        "tecnicas_preferidas": [("motivo", 0.9), ("arpegio", 0.1)],
        "prob_variacion_A": 0.7,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.6,
        # Ritmo R&B: Sincopado, swing, notas largas + rápidas
        "complejidad_ritmica": [3, 1, 0, 4, 1, 1, 2, 0, 4], # Tresillo implícito (3) + síncopas
        "complejidad_motivo": 3,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.4, # Más adornos
        "intervalos_preferidos": [(1, 0.4), (2, 0.3), (3, 0.15), (4, 0.1), (5, 0.05)], # Principalmente pasos, algunos saltos
        "prob_nota_especial": 0.25, # Uso frecuente de blue notes
        "notas_especiales": [3, 6, 10], # Blue notes (b3, b5, b7 en semitonos relativos a la tónica del acorde)
    },
    "reggaeton": {
        "tecnicas_preferidas": [("motivo", 0.85), ("arpegio", 0.15)],
        "prob_variacion_A": 0.3,
        "estructura_frase": "continua", # Frases cortas y repetitivas
        "densidad_notas": 0.75, # Bastante lleno rítmicamente
        # Ritmo Reggaeton: Dembow variado, énfasis en upbeat
        "complejidad_ritmica": [1, 1, 2, 0, 1, 1, 2, 0, 1, 1, 1, 1, 4],
        "complejidad_motivo": 2, # Motivos muy cortos
        "max_repeticion_nota": 3,
        "prob_nota_de_paso": 0.15, # Principalmente notas del acorde
        "intervalos_preferidos": [(3, 0.4), (4, 0.3), (2, 0.1), (5, 0.1), (1, 0.1)], # Favorece saltos de tercera
    },
    "techno": {
        "tecnicas_preferidas": [("arpegio", 0.9), ("motivo", 0.1)],
        "prob_variacion_A": 0.2,
        "estructura_frase": "continua",
        "densidad_notas": 0.9, # Muy denso
        # Ritmo Techno: Flujo constante de semis con acentos y silencios ocasionales
        "complejidad_ritmica": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
        "complejidad_motivo": 3, # Para arpegios
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.05, # Casi solo notas del acorde
        "intervalos_preferidos": [(12, 0.5), (7, 0.3), (5, 0.1), (2, 0.1)], # Saltos de octava, quinta, tercera para arpegios
    },
    "default": { # Fallback más musical
        "tecnicas_preferidas": [("motivo", 0.7), ("arpegio", 0.3)],
        "prob_variacion_A": 0.4,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.6,
        "complejidad_ritmica": [4, 2, 2, 4, 0, 2, 2, 4],
        "complejidad_motivo": 2,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.2,
        "intervalos_preferidos": [(1, 0.3), (2, 0.3), (3, 0.2), (5, 0.1), (7, 0.1)],
    }
}

_ROMAN_TOKEN_RE = re.compile(r"\b[#b♭♯-]*[ivx]+[0-9°ø+]*\b", re.IGNORECASE)
_CHORD_TOKEN_PATTERN = re.compile(
    r"\b(?:acorde\s+de\s+)?((?:do|re|mi|fa|sol|la|si|[a-g])[#b]?"
    r"(?:\s*(?:mayor|menor|maj7|maj9|min7|min|dim|aug|sus2|sus4|m|\+|°)?"
    r"(?:\s*(?:7|9|6|11|13))?)?)(?=\b|[\s,.;:-])",
    re.IGNORECASE,
)


def _normalizar_texto_para_notas(texto):
    """Normaliza texto para facilitar la detección de nombres de notas en español o inglés."""

    if not texto:
        return ""

    texto_norm = texto.lower()
    texto_norm = texto_norm.replace("♯", "#").replace("♭", "b")
    texto_norm = re.sub(r"sostenid[ao]s?", "#", texto_norm)
    texto_norm = re.sub(r"sharp", "#", texto_norm)
    texto_norm = re.sub(r"bemoles?", "b", texto_norm)
    texto_norm = re.sub(r"flat", "b", texto_norm)
    texto_norm = re.sub(r"(do|re|mi|fa|sol|la|si)\s*(#|b)", r"\1\2", texto_norm)
    texto_norm = re.sub(r"([a-g])\s*(#|b)", r"\1\2", texto_norm)
    return texto_norm


def _resolver_nota_canonica(base, accidental=""):
    clave_directa = f"{base}{accidental}".lower()
    if clave_directa in nota_equivalente:
        return nota_equivalente[clave_directa]
    if base.lower() in nota_equivalente:
        nota_base = nota_equivalente[base.lower()]
        if accidental:
            try:
                pitch_obj = pitch.Pitch(nota_base)
                if accidental == "#":
                    pitch_obj = pitch_obj.transpose(1)
                elif accidental == "b":
                    pitch_obj = pitch_obj.transpose(-1)
                return pitch_obj.name
            except Exception:  # noqa: BLE001
                return nota_base
        return nota_base
    return None


def _token_a_notas_de_acorde(token):
    token = token.strip()
    if not token:
        return None

    coincidencia = re.match(
        r"^(?:acorde\s+de\s+)?(do|re|mi|fa|sol|la|si|[a-g])([#b]?)(.*)$",
        token,
        re.IGNORECASE,
    )
    if not coincidencia:
        return None

    base = coincidencia.group(1).lower()
    accidental = coincidencia.group(2).lower()
    resto = coincidencia.group(3).strip().lower()
    nota_canonica = _resolver_nota_canonica(base, accidental)
    if not nota_canonica:
        return None

    resto = resto.replace("-", " ")
    calidad = ""
    if re.search(r"(menor|minor|\bmin\b|\bm\b)", resto) and not re.search(r"maj", resto):
        calidad = "m"
    elif re.search(r"(dim|disminu|°)", resto):
        calidad = "dim"
    elif re.search(r"(aug|aum|\+)", resto):
        calidad = "aug"

    simbolo = nota_canonica + calidad

    extension = None
    if re.search(r"maj7", resto):
        extension = "maj7"
    elif re.search(r"maj9", resto):
        extension = "maj9"
    elif re.search(r"\b9\b", resto):
        extension = "9"
    elif re.search(r"\b7\b", resto):
        extension = "7"
    elif re.search(r"\b6\b", resto):
        extension = "6"

    if extension:
        simbolo += extension

    try:
        cs = harmony.ChordSymbol(simbolo)
        return [p.name for p in cs.pitches]
    except Exception:  # noqa: BLE001
        try:
            pitch_base = pitch.Pitch(nota_canonica)
            if calidad == "m":
                tercera = pitch_base.transpose(3)
                quinta = pitch_base.transpose(7)
            elif calidad == "dim":
                tercera = pitch_base.transpose(3)
                quinta = pitch_base.transpose(6)
            elif calidad == "aug":
                tercera = pitch_base.transpose(4)
                quinta = pitch_base.transpose(8)
            else:
                tercera = pitch_base.transpose(4)
                quinta = pitch_base.transpose(7)
            return [pitch_base.name, tercera.name, quinta.name]
        except Exception:  # noqa: BLE001
            return [nota_canonica]


def _extraer_tokens_de_notas(texto_normalizado):
    tokens = []
    for coincidencia in _CHORD_TOKEN_PATTERN.finditer(texto_normalizado):
        token = coincidencia.group(1)
        if not token:
            continue
        token = token.strip()
        if not token:
            continue
        tokens.append(token)
    return tokens


def _extraer_romanos_desde_prompt(prompt_texto):
    tokens = []
    for coincidencia in _ROMAN_TOKEN_RE.finditer(prompt_texto):
        candidato = coincidencia.group(0)
        if not candidato:
            continue
        letras = "".join(ch for ch in candidato.lower() if ch.isalpha())
        if letras and set(letras) <= {"i", "v", "x"}:
            tokens.append(candidato.replace("♭", "b").replace("♯", "#"))
    return tokens


def extraer_progresion_de_prompt(prompt_texto, raiz=None, modo=None):
    """Extrae una progresión de acordes del prompt del usuario si detecta múltiples acordes."""

    if not prompt_texto:
        return []

    acordes_detectados = []
    romanos_en_prompt = _extraer_romanos_desde_prompt(prompt_texto)
    if raiz and modo and len(romanos_en_prompt) >= 2:
        try:
            tonalidad_usuario = key.Key(raiz, modo)
        except Exception:  # noqa: BLE001
            tonalidad_usuario = None
        if tonalidad_usuario:
            for roman_fig in romanos_en_prompt:
                try:
                    rn_obj = roman.RomanNumeral(roman_fig, tonalidad_usuario)
                    acordes_detectados.append([p.name for p in rn_obj.pitches])
                except Exception:  # noqa: BLE001
                    continue
            if len(acordes_detectados) >= 2:
                return acordes_detectados

    texto_normalizado = _normalizar_texto_para_notas(prompt_texto)
    tokens_notas = _extraer_tokens_de_notas(texto_normalizado)
    if len(tokens_notas) >= 2:
        for token in tokens_notas:
            notas_acorde = _token_a_notas_de_acorde(token)
            if notas_acorde:
                acordes_detectados.append(notas_acorde)
        if len(acordes_detectados) >= 2:
            return acordes_detectados

    return []


def _generar_progresion_base_para_melodia(raiz, modo, longitud_objetivo=None):
    longitud = longitud_objetivo if longitud_objetivo and longitud_objetivo > 0 else 8
    longitud = max(4, int(longitud))
    try:
        tonalidad_obj = key.Key(raiz, modo)
    except Exception:  # noqa: BLE001
        tonalidad_obj = key.Key("C", "major")

    if tonalidad_obj.mode == "minor":
        patron = ["i", "v", "VI", "iv"]
    else:
        patron = ["I", "V", "vi", "IV"]

    acordes = []
    for i in range(longitud):
        rn_str = patron[i % len(patron)]
        try:
            rn_obj = roman.RomanNumeral(rn_str, tonalidad_obj)
            acordes.append([p.name for p in rn_obj.pitches])
        except Exception:  # noqa: BLE001
            acordes.append([tonalidad_obj.tonic.name])

    ritmo = [2.0] * len(acordes)
    return acordes, ritmo

def notas_del_acorde_music21(acorde_data_o_lista_str):
    pitches_obj_list = []
    lista_notas_str = []
    if isinstance(acorde_data_o_lista_str, list):
        lista_notas_str = acorde_data_o_lista_str
    elif isinstance(acorde_data_o_lista_str, str) and acorde_data_o_lista_str not in ["0", "N/A"]:
        try:
            cs = harmony.ChordSymbol(acorde_data_o_lista_str)
            lista_notas_str = [p.name for p in cs.pitches]
        except Exception:  # noqa: BLE001
            pass
    elif isinstance(acorde_data_o_lista_str, str) and acorde_data_o_lista_str.startswith("SN_"):
        lista_notas_str = [acorde_data_o_lista_str[3:]]

    for n_str in lista_notas_str:
        try:
            p = pitch.Pitch(n_str)
            pitches_obj_list.append(p)
        except Exception as exc:  # noqa: BLE001
            print(f"Advertencia (notas_del_acorde): No se pudo crear Pitch para '{n_str}': {exc}")
    return pitches_obj_list


def obtener_escala_actual(raiz_str, modo_str):
    try:
        modo_m21 = modo_str.lower()
        if modo_m21 == "mayor":
            modo_m21 = "major"
        elif modo_m21 == "menor":
            modo_m21 = "minor"
        k_raiz_pitch = pitch.Pitch(raiz_str)
        k_raiz_nombre = k_raiz_pitch.name
        tonalidad = key.Key(k_raiz_nombre, modo_m21)
        return tonalidad.getScale()
    except Exception as exc:  # noqa: BLE001
        print(f"Error obteniendo escala para {raiz_str} {modo_str}: {exc}. Usando C Mayor.")
        return scale.MajorScale("C")
    
# --- INICIO DEL BLOQUE PARA PEGAR ---

# --- Funciones Auxiliares (Helpers) ---

def _pitch_from_midi(midi_val):
    p = pitch.Pitch()
    p.midi = int(round(midi_val))
    return p

def _extraer_midi_de_acordes(acordes_progresion):
    midi_vals = []
    for acorde in acordes_progresion:
        if isinstance(acorde, dict):
            posibles_claves = ("voicing", "notas", "notes")
            for clave in posibles_claves:
                if clave in acorde and isinstance(acorde[clave], (list, tuple)):
                    acorde = acorde[clave]
                    break
        if isinstance(acorde, (list, tuple)):
            for nota in acorde:
                try:
                    pitch_obj = pitch.Pitch(nota)
                    midi_vals.append(pitch_obj.midi)
                except Exception as exc:  # noqa: BLE001
                    print(f"Advertencia (extraer_midi): No se pudo leer '{nota}': {exc}")
        elif isinstance(acorde, str) and acorde not in {"0", "N/A"}:
            for nota in notas_del_acorde_music21(acorde):
                midi_vals.append(nota.midi)
    return midi_vals

def _ajustar_rango_melodia_a_progresion(params: ParametrosMelodicos, acordes_progresion):
    midi_vals = _extraer_midi_de_acordes(acordes_progresion)
    if not midi_vals:
        return
    highest_pitch = _pitch_from_midi(max(midi_vals))
    rango_original = max(1, params.octava_melodia_max - params.octava_melodia_min)
    objetivo_min_octava = max(params.octava_melodia_min, min(8, highest_pitch.octave + 1))
    objetivo_max_octava = min(9, objetivo_min_octava + rango_original)
    if objetivo_max_octava <= objetivo_min_octava:
        objetivo_max_octava = min(9, objetivo_min_octava + 1)
    params.octava_melodia_min = int(objetivo_min_octava)
    params.octava_melodia_max = int(objetivo_max_octava)

def _calcular_rango_midi(params: ParametrosMelodicos):
    min_pitch = pitch.Pitch(f"C{params.octava_melodia_min}").midi
    max_pitch = pitch.Pitch(f"B{params.octava_melodia_max}").midi
    if max_pitch < min_pitch:
        max_pitch = min_pitch
    return min_pitch, max_pitch

def _clamp_pitch_to_range(p_obj, params: ParametrosMelodicos):
    if p_obj is None:
        return None
    min_midi, max_midi = _calcular_rango_midi(params)
    midi_val = p_obj.midi
    while midi_val < min_midi:
        midi_val += 12
    while midi_val > max_midi:
        midi_val -= 12
    clamped = pitch.Pitch()
    clamped.midi = midi_val
    return clamped

def _expandir_notas_acorde_en_rango(acorde_data, params: ParametrosMelodicos):
    notas_base = notas_del_acorde_music21(acorde_data)
    if not notas_base:
        return []
    min_midi, max_midi = _calcular_rango_midi(params)
    notas_expandidas = []
    for base in notas_base:
        for octava in range(params.octava_melodia_min, params.octava_melodia_max + 1):
            try:
                cand = pitch.Pitch(base.name)
                cand.octave = octava
                if min_midi <= cand.midi <= max_midi:
                    notas_expandidas.append(pitch.Pitch(cand.nameWithOctave))
            except Exception:  # noqa: BLE001
                continue
    notas_unicas = {}
    for nota in sorted(notas_expandidas, key=lambda p: p.midi):
        notas_unicas.setdefault(nota.midi, nota)
    return list(notas_unicas.values())

def _agregar_evento(lista_eventos, pitch_str, duracion_ql):
    # Redondear la duración en Quarter Lengths ANTES de convertir a string
    duracion_redondeada = round(duracion_ql, 3)
    if duracion_redondeada <= 0:
        return lista_eventos

    # Convertir a string DESPUÉS de redondear
    duracion_str = str(duracion_redondeada)

    if pitch_str == "0" and lista_eventos and lista_eventos[-1][0] == "0":
        # Sumar duraciones como floats y redondear el resultado
        ultima_dur = float(lista_eventos[-1][1])
        nueva_dur_total = round(ultima_dur + duracion_redondeada, 3)
        lista_eventos[-1] = ("0", str(nueva_dur_total))
    else:
        lista_eventos.append((pitch_str, duracion_str))
    return lista_eventos

# --- NUEVO MOTOR DE COMPOSICIÓN (A-B-A') ---

def _crear_motivo_musical(notas_acorde_inicial, perfil, escala_obj):
    """Crea un motivo rítmico y melódico inicial, priorizando notas estables."""
    num_notas = perfil["complejidad_motivo"]
    motivo_ritmico = random.choices(perfil["complejidad_ritmica"], k=num_notas)

    # --- ¡CORRECCIÓN! Comprobar si la lista de notas está vacía ---
    if not notas_acorde_inicial:
        print("ADVERTENCIA (_crear_motivo_musical): La lista de notas del acorde inicial está vacía. Usando motivo por defecto.")
        # Fallback: Usar una nota por defecto (ej. C4) y un ritmo simple
        notas_base = [pitch.Pitch("C4")] * num_notas # Crear lista con nota por defecto
        motivo_ritmico = [2] * num_notas # Ritmo simple de corcheas
        return notas_base, motivo_ritmico
    # --- FIN CORRECCIÓN ---

    # Priorizar tónica, tercera y quinta del acorde para el inicio del motivo
    tonica = notas_acorde_inicial[0] # Ahora es seguro acceder a [0]
    try:
      # Intentar obtener tercera y quinta de la escala relativa a la tónica del acorde
      # Esto asume que la tonalidad general es relevante, incluso si el acorde es alterado
      p_tonica_temp = pitch.Pitch(tonica.name) # Usar solo el nombre, sin octava, para grados
      escala_temp = escala_obj.__class__(tonic=p_tonica_temp) # Crear escala temporal en la tónica del acorde
      tercera_pitch = escala_temp.pitchFromDegree(3)
      quinta_pitch = escala_temp.pitchFromDegree(5)
      # Buscar notas en el voicing que coincidan con los nombres de tónica, tercera, quinta
      notas_estables_acorde = [n for n in notas_acorde_inicial if n.name == tonica.name or n.name == tercera_pitch.name or n.name == quinta_pitch.name]
    except Exception as e: # Fallback si falla obtener grados
      print(f"Advertencia calculando estables: {e}. Usando T-3-5 simple.")
      notas_estables_acorde = notas_acorde_inicial[:min(3, len(notas_acorde_inicial))] # Tomar las 3 primeras como fallback


    if not notas_estables_acorde: notas_estables_acorde = notas_acorde_inicial

    # Elegir notas base, favoreciendo las estables
    notas_base = []
    if notas_estables_acorde:
        notas_base.append(random.choice(notas_estables_acorde)) # Empezar con una estable
    else: # Si AÚN no hay estables (caso raro), empezar con cualquiera
         notas_base.append(random.choice(notas_acorde_inicial))

    while len(notas_base) < num_notas:
        # Añadir más notas, mezclando estables y otras del acorde
        if random.random() < 0.6 and notas_estables_acorde:
            notas_base.append(random.choice(notas_estables_acorde))
        else:
            notas_base.append(random.choice(notas_acorde_inicial))

    return notas_base, motivo_ritmico

def _generar_arpegio_melodico(unidades_totales, notas_acorde, ultima_nota, perfil, params):
    """Genera un arpegio rítmico y melódico (Quantizado y Seguro)."""
    # --- ¡NUEVA COMPROBACIÓN! ---
    if not notas_acorde:
        print("ADVERTENCIA (_generar_arpegio_melodico): Lista 'notas_acorde' vacía. Generando silencio.")
        duracion_silencio_total = unidades_totales * params.melodia_grid_unit_ql
        return [_agregar_evento([], "0", duracion_silencio_total)][0], ultima_nota
    # --- FIN COMPROBACIÓN ---

    eventos_arpegio = []
    unidades_usadas = 0
    ritmo_arpegio_units = perfil["complejidad_ritmica"]

    direccion = random.choice([1, -1])
    notas_arpegio = sorted(notas_acorde, key=lambda p: p.midi * direccion)

    # --- ¡NUEVA COMPROBACIÓN (ZeroDivisionError)! ---
    if not notas_arpegio: # Doble chequeo por si el sort falla o algo raro pasa
        print("ADVERTENCIA (_generar_arpegio_melodico): Lista 'notas_arpegio' vacía después de ordenar. Generando silencio.")
        duracion_silencio_total = unidades_totales * params.melodia_grid_unit_ql
        return [_agregar_evento([], "0", duracion_silencio_total)][0], ultima_nota
    # --- FIN COMPROBACIÓN ---

    posicion_nota = 0
    while unidades_usadas < unidades_totales:
        dur_units = ritmo_arpegio_units[posicion_nota % len(ritmo_arpegio_units)]
        if dur_units == 0: dur_units = 1

        unidades_restantes = unidades_totales - unidades_usadas
        if dur_units > unidades_restantes: dur_units = unidades_restantes

        dur_ql = dur_units * params.melodia_grid_unit_ql
        if dur_ql <= 0: break

        poner_nota = (ritmo_arpegio_units[posicion_nota % len(ritmo_arpegio_units)] != 0) and (random.random() < perfil["densidad_notas"])

        if poner_nota:
             # Ahora es seguro hacer el módulo porque len(notas_arpegio) > 0
            nota_actual_arp = notas_arpegio[posicion_nota % len(notas_arpegio)]
            candidato_pitch = _clamp_pitch_to_range(nota_actual_arp, params)
            eventos_arpegio = _agregar_evento(eventos_arpegio, candidato_pitch.nameWithOctave, dur_ql)
            ultima_nota = candidato_pitch
        else:
            eventos_arpegio = _agregar_evento(eventos_arpegio, "0", dur_ql)

        unidades_usadas += dur_units
        posicion_nota += 1

    return eventos_arpegio, ultima_nota

def _generar_frase(unidades_totales, notas_acorde, notas_escala, ultima_nota, motivo, perfil, params, escala_obj, es_respuesta=False):
    """Genera una frase musical aplicando principios musicales fundamentales (Quantizada y Segura)."""
    # --- ¡NUEVA COMPROBACIÓN! ---
    if not notas_acorde:
        print("ADVERTENCIA (_generar_frase): Lista 'notas_acorde' vacía. Generando silencio.")
        duracion_silencio_total = unidades_totales * params.melodia_grid_unit_ql
        return [_agregar_evento([], "0", duracion_silencio_total)][0], ultima_nota # Devuelve lista con el silencio y la última nota sin cambios
    # --- FIN COMPROBACIÓN ---

    eventos_frase = []
    unidades_usadas = 0 # Usar enteros para acumular unidades
    posicion_motivo = 0
    notas_motivo_base, ritmo_motivo_units = motivo

    repeticiones_nota_actual = 0
    # Empezar desde la última nota si existe Y está en el acorde actual, si no, elegir una del acorde
    # Asegurarse de que nota_actual no sea None si notas_acorde no está vacía
    if ultima_nota and any(abs(ultima_nota.midi - n.midi) < 0.5 for n in notas_acorde):
         nota_actual = ultima_nota
    else:
         nota_actual = random.choice(notas_acorde) # Seguro porque ya comprobamos que notas_acorde no está vacía

    ultimo_intervalo = 0

    # Variación del motivo
    variacion_semitonos = random.choice([0, 0, 0, 1, -1, 2]) if not es_respuesta else 0
    notas_motivo_variado = []
    for n_base in notas_motivo_base:
        try:
            p_variado = pitch.Pitch(n_base.nameWithOctave)
            p_variado.transpose(variacion_semitonos, inPlace=True)
            # Ajustar a la escala (si hay notas en la escala)
            if notas_escala:
                 p_ajustado = min(notas_escala, key=lambda p_esc: abs(p_esc.midi - p_variado.midi))
                 notas_motivo_variado.append(p_ajustado)
            else: # Si no hay escala, usar la nota variada directamente
                 notas_motivo_variado.append(p_variado)
        except:
            notas_motivo_variado.append(n_base)

    while unidades_usadas < unidades_totales:
        dur_units = ritmo_motivo_units[posicion_motivo % len(ritmo_motivo_units)]
        es_silencio_ritmico = (dur_units == 0)
        if es_silencio_ritmico: dur_units = 1

        unidades_restantes = unidades_totales - unidades_usadas
        if dur_units > unidades_restantes: dur_units = unidades_restantes

        dur_ql = dur_units * params.melodia_grid_unit_ql
        if dur_ql <= 0: break

        poner_nota = (not es_silencio_ritmico) and (random.random() < perfil["densidad_notas"])

        if poner_nota:
            nota_candidata = None
            es_fuerte = (unidades_usadas * params.melodia_grid_unit_ql) % (params.pulsos_por_compas / 2) < params.melodia_grid_unit_ql

            if es_fuerte:
                # Ahora seguro llamar a min porque notas_acorde no está vacía
                nota_candidata = min(notas_acorde, key=lambda n: abs(n.midi - nota_actual.midi))
            else:
                 # Resto de la lógica de selección (B.1, B.2, B.3) - necesita notas_escala
                 # B.1 Resolver salto anterior?
                if abs(ultimo_intervalo) > 5 and notas_escala: # Solo si hay notas de escala
                    direccion_opuesta = -1 if ultimo_intervalo > 0 else 1
                    vecinos_resolucion = [p for p in notas_escala if 0 < (p.midi - nota_actual.midi) * direccion_opuesta <= 2]
                    if vecinos_resolucion:
                         nota_candidata = random.choice(vecinos_resolucion)

                # B.2 Seguir motivo variado?
                if nota_candidata is None and random.random() < 0.6 and notas_motivo_variado:
                     nota_del_motivo = notas_motivo_variado[posicion_motivo % len(notas_motivo_variado)]
                     if abs(nota_del_motivo.midi - nota_actual.midi) <= 7:
                          nota_candidata = nota_del_motivo

                # B.3 Nota de paso/aproximación?
                if nota_candidata is None and notas_escala: # Solo si hay notas de escala
                    vecinos = [p for p in notas_escala if 0 < abs(p.midi - nota_actual.midi) <= 2]
                    nota_cromatica_cercana = pitch.Pitch()
                    nota_cromatica_cercana.midi = nota_actual.midi + random.choice([-1, 1])
                    if nota_cromatica_cercana.name not in [p.name for p in notas_escala]:
                         # Ahora seguro llamar a min porque notas_acorde no está vacía
                         nota_resolucion = min(notas_acorde, key=lambda n: abs(n.midi - nota_cromatica_cercana.midi))
                         if abs(nota_resolucion.midi - nota_cromatica_cercana.midi) == 1: vecinos.append(nota_cromatica_cercana)
                    if vecinos:
                        nota_candidata = random.choice(vecinos)


            # C. Fallback: Nota del acorde más cercana (seguro)
            if nota_candidata is None:
                 nota_candidata = min(notas_acorde, key=lambda n: abs(n.midi - nota_actual.midi))

            # D. Resolución al final de la frase (seguro)
            if unidades_usadas + dur_units >= unidades_totales:
                 tonica_acorde_final = notas_acorde[0]
                 try: tercera_acorde_final = min([n for n in notas_acorde if n.name != tonica_acorde_final.name], key=lambda x:x.midi)
                 except: tercera_acorde_final = notas_acorde[1] if len(notas_acorde) > 1 else notas_acorde[0]
                 quinta_acorde_final = max(notas_acorde, key=lambda x:x.midi)
                 notas_resolucion = [tonica_acorde_final, tercera_acorde_final, quinta_acorde_final]
                 nota_candidata = min(notas_resolucion, key=lambda n: abs(n.midi - nota_actual.midi))

            # E. Evitar repetición excesiva (seguro)
            if nota_candidata.midi == nota_actual.midi:
                repeticiones_nota_actual += 1
                if repeticiones_nota_actual >= perfil["max_repeticion_nota"]:
                    alternativas = [n for n in notas_escala if n.midi != nota_actual.midi and abs(n.midi-nota_actual.midi)<=2] if notas_escala else []
                    if not alternativas: alternativas = [n for n in notas_acorde if n.midi != nota_actual.midi]
                    if alternativas: nota_candidata = random.choice(alternativas)
            else:
                repeticiones_nota_actual = 0
                ultimo_intervalo = nota_candidata.midi - nota_actual.midi

            nota_final = _clamp_pitch_to_range(nota_candidata, params)
            eventos_frase = _agregar_evento(eventos_frase, nota_final.nameWithOctave, dur_ql)
            nota_actual = nota_final
            ultima_nota = nota_actual
        else:
            eventos_frase = _agregar_evento(eventos_frase, "0", dur_ql)
            ultimo_intervalo = 0

        unidades_usadas += dur_units
        posicion_motivo += 1

    return eventos_frase, ultima_nota

def _generar_seccion_melodica(segmento_acordes_seccion, segmento_ritmos_seccion, tecnica, motivo, perfil, escala_obj, notas_escala_obj, params, ultima_nota_obj):
    """Genera la melodía para una sección específica (A o B) usando la técnica elegida."""
    if tecnica == "arpegio":
        unidades_totales = sum(int(round(float(r) / params.melodia_grid_unit_ql)) for r in segmento_ritmos_seccion)
        notas_acorde = _expandir_notas_acorde_en_rango(segmento_acordes_seccion[0], params)
        return _generar_arpegio_melodico(unidades_totales, notas_acorde, ultima_nota_obj, perfil, params)
    melodia_seccion = []
    unidades_por_frase = int((params.pulsos_por_compas * 2) / params.melodia_grid_unit_ql)
    unidades_procesadas = 0
    total_unidades_seccion = sum(int(round(float(r) / params.melodia_grid_unit_ql)) for r in segmento_ritmos_seccion)
    acorde_idx_en_seccion = 0
    while unidades_procesadas < total_unidades_seccion:
        unidades_frase_actual = min(unidades_por_frase, total_unidades_seccion - unidades_procesadas)
        acorde_actual = segmento_acordes_seccion[acorde_idx_en_seccion % len(segmento_acordes_seccion)]
        notas_acorde_frase = _expandir_notas_acorde_en_rango(acorde_actual, params)
        if not notas_acorde_frase: notas_acorde_frase = _expandir_notas_acorde_en_rango(segmento_acordes_seccion[0], params)
        es_respuesta = (unidades_procesadas // unidades_por_frase) % 2 == 1 and perfil["estructura_frase"] == "pregunta_respuesta"
        
        eventos_frase, ultima_nota_obj = _generar_frase(unidades_frase_actual, notas_acorde_frase, notas_escala_obj, ultima_nota_obj, motivo, perfil, params, escala_obj, es_respuesta)
        melodia_seccion.extend(eventos_frase)
        unidades_procesadas += unidades_frase_actual
        acorde_idx_en_seccion += 1

    return melodia_seccion, ultima_nota_obj

def _variar_melodia(eventos_melodia, escala_obj, params):
    """Aplica pequeñas variaciones a una melodía existente para crear la sección A'."""
    eventos_variados = []
    for nota, duracion in eventos_melodia:
        if nota != "0" and random.random() < 0.3:
            p_original = pitch.Pitch(nota)
            vecinos = [p for p in escala_obj if 0 < abs(p.midi - p_original.midi) <= 2]
            if vecinos:
                p_variado = random.choice(vecinos)
                eventos_variados.append((_clamp_pitch_to_range(p_variado, params).nameWithOctave, duracion))
            else:
                eventos_variados.append((nota, duracion))
        else:
            eventos_variados.append((nota, duracion))
    return eventos_variados

def _obtener_notas_escala_en_rango(escala_actual, params):
    notas_escala_disponibles_obj = []
    for p_escala_base in escala_actual.pitches:
        if isinstance(p_escala_base, pitch.Pitch):
            for oct_num in range(params.octava_melodia_min, params.octava_melodia_max + 1):
                try:
                    p_temp = pitch.Pitch(p_escala_base.name)
                    p_temp.octave = oct_num
                    if p_temp not in notas_escala_disponibles_obj: notas_escala_disponibles_obj.append(p_temp)
                except Exception: continue
    return sorted(set(notas_escala_disponibles_obj), key=lambda p: p.ps)

def _generar_melodia_simple(acordes, ritmo, raiz, modo, genero, bpm, oct_min, oct_max):
    """Función de fallback para progresiones cortas que no pueden usar A-B-A'."""
    print("ADVERTENCIA: Progresión muy corta para estructura A-B-A'. Usando lógica simple.")
    perfil_actual = PERFILES_GENERO.get(str(genero).lower(), PERFILES_GENERO["default"])
    params_mel = ParametrosMelodicos(bpm=bpm, octava_melodia_min=oct_min, octava_melodia_max=oct_max)
    escala_actual = obtener_escala_actual(raiz, modo)
    notas_escala_obj = _obtener_notas_escala_en_rango(escala_actual, params_mel)
    acordes_para_simple = list(acordes) if acordes else []
    ritmo_para_simple = list(ritmo) if ritmo else []
    if not acordes_para_simple:
        acordes_para_simple, ritmo_generado = _generar_progresion_base_para_melodia(raiz, modo, len(ritmo_para_simple) or 4)
        ritmo_para_simple = ritmo_generado
    if not ritmo_para_simple:
        ritmo_para_simple = [1.0] * len(acordes_para_simple)
    notas_primer_acorde = _expandir_notas_acorde_en_rango(acordes_para_simple[0], params_mel)

    if not notas_primer_acorde:
        total_dur = sum(float(r) for r in ritmo_para_simple)
        return [("0", str(total_dur))] if total_dur > 0 else []
    motivo = _crear_motivo_musical(notas_primer_acorde, perfil_actual)
    return _generar_seccion_melodica(
        acordes_para_simple,
        ritmo_para_simple,
        "motivo",
        motivo,
        perfil_actual,
        escala_actual,
        notas_escala_obj,
        params_mel,
        None,
    )[0]

# --- Función Principal de Generación de Melodía ---
def generar_melodia_sobre_acordes(
    acordes_progresion=None,
    ritmo_acordes=None,
    raiz_tonalidad="C",
    modo_tonalidad="major",
    genero="default",
    bpm=120,
    octava_melodia_min=4,
    octava_melodia_max=5,
    longitud_objetivo=None,
    devolver_contexto=False,
):
    acordes_para_melodia = list(acordes_progresion) if acordes_progresion else []
    ritmo_para_melodia = list(ritmo_acordes) if ritmo_acordes else []

    if not acordes_para_melodia:
        acordes_para_melodia, ritmo_generado = _generar_progresion_base_para_melodia(
            raiz_tonalidad,
            modo_tonalidad,
            longitud_objetivo,
        )
        ritmo_para_melodia = ritmo_generado

    if not ritmo_para_melodia:
        ritmo_para_melodia = [1.0] * len(acordes_para_melodia)
    elif len(ritmo_para_melodia) != len(acordes_para_melodia):
        ritmo_alineado = ritmo_para_melodia[: len(acordes_para_melodia)]
        if len(ritmo_alineado) < len(acordes_para_melodia):
            ultimo_valor = ritmo_para_melodia[-1] if ritmo_para_melodia else 1.0
            ritmo_alineado.extend([ultimo_valor] * (len(acordes_para_melodia) - len(ritmo_alineado)))
        ritmo_para_melodia = ritmo_alineado

    if not acordes_para_melodia:
        resultado_vacio = []
        return (resultado_vacio, acordes_para_melodia, ritmo_para_melodia) if devolver_contexto else resultado_vacio

    if len(acordes_para_melodia) < 4:
        melodia_simple = _generar_melodia_simple(
            acordes_para_melodia,
            ritmo_para_melodia,
            raiz_tonalidad,
            modo_tonalidad,
            genero,
            bpm,
            octava_melodia_min,
            octava_melodia_max,
        )
        return (melodia_simple, acordes_para_melodia, ritmo_para_melodia) if devolver_contexto else melodia_simple

    perfil_actual = PERFILES_GENERO.get(str(genero).lower(), PERFILES_GENERO["default"])
    params_mel = ParametrosMelodicos(bpm=bpm, octava_melodia_min=octava_melodia_min, octava_melodia_max=octava_melodia_max)
    _ajustar_rango_melodia_a_progresion(params_mel, acordes_para_melodia)
    escala_actual = obtener_escala_actual(raiz_tonalidad, modo_tonalidad)
    notas_escala_disponibles_obj = _obtener_notas_escala_en_rango(escala_actual, params_mel)
    
    tecnicas, pesos = zip(*perfil_actual["tecnicas_preferidas"])
    tecnica_elegida = random.choices(tecnicas, weights=pesos, k=1)[0]
    print(f"DEBUG (Melodia): ESTRUCTURA A-B-A'. Técnica elegida: {tecnica_elegida}")

    num_acordes = len(acordes_para_melodia)
    punto_corte_A = num_acordes // 2
    punto_corte_B = punto_corte_A + max(2, num_acordes // 4)
    if punto_corte_B >= num_acordes: punto_corte_B = num_acordes -1
    if punto_corte_A >= punto_corte_B: punto_corte_A = 0
    if punto_corte_A < 0: punto_corte_A = 0
    
    segmento_A_acordes = acordes_para_melodia[:punto_corte_A]
    segmento_A_ritmos = ritmo_para_melodia[:punto_corte_A]
    segmento_B_acordes = acordes_para_melodia[punto_corte_A:punto_corte_B]
    segmento_B_ritmos = ritmo_para_melodia[punto_corte_A:punto_corte_B]
    segmento_A2_acordes = acordes_para_melodia[punto_corte_B:]
    segmento_A2_ritmos = ritmo_para_melodia[punto_corte_B:]

    if not segmento_A_acordes or not segmento_B_acordes or not segmento_A2_acordes:
         melodia_simple = _generar_melodia_simple(
             acordes_para_melodia,
             ritmo_para_melodia,
             raiz_tonalidad,
             modo_tonalidad,
             genero,
             bpm,
             octava_melodia_min,
             octava_melodia_max,
         )
         return (melodia_simple, acordes_para_melodia, ritmo_para_melodia) if devolver_contexto else melodia_simple

    notas_primer_acorde = _expandir_notas_acorde_en_rango(segmento_A_acordes[0], params_mel)
    if not notas_primer_acorde:
        total_dur = sum(float(r) for r in ritmo_para_melodia)
        melodia_silencio = [("0", str(total_dur))] if total_dur > 0 else []
        return (melodia_silencio, acordes_para_melodia, ritmo_para_melodia) if devolver_contexto else melodia_silencio

    motivo_principal = _crear_motivo_musical(notas_primer_acorde, perfil_actual, escala_actual)
    melodia_A, ultima_nota_A = _generar_seccion_melodica(segmento_A_acordes, segmento_A_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)
    
    notas_acorde_B = _expandir_notas_acorde_en_rango(segmento_B_acordes[0], params_mel) if segmento_B_acordes else notas_primer_acorde
    motivo_B = _crear_motivo_musical(notas_acorde_B, perfil_actual, escala_actual) # Pasar escala_actual
    melodia_B, _ = _generar_seccion_melodica(segmento_B_acordes, segmento_B_ritmos, tecnica_elegida, motivo_B, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, ultima_nota_A)

    if random.random() < perfil_actual["prob_variacion_A"]:
        print("DEBUG (Melodia): Generando variación A'")
        melodia_A_base_para_variacion, _ = _generar_seccion_melodica(segmento_A2_acordes, segmento_A2_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)
        melodia_A2 = _variar_melodia(melodia_A_base_para_variacion, notas_escala_disponibles_obj, params_mel)
    else:
        print("DEBUG (Melodia): Repitiendo sección A")
        melodia_A2, _ = _generar_seccion_melodica(segmento_A2_acordes, segmento_A2_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)

    melodia_final = melodia_A + melodia_B + melodia_A2
    if devolver_contexto:
        return melodia_final, acordes_para_melodia, ritmo_para_melodia
    return melodia_final


# --- Bloque de Pruebas ---
if __name__ == "__main__":
    acordes_test = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"], ["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
    ritmo_test = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0] # Progresión de 8 acordes
    raiz_test = "C"
    modo_test = "major"

    print("\n--- Prueba de generación por GÉNERO (Estructura A-B-A') ---")
    
    for genero_actual in ["pop", "lofi", "reggaeton", "r&b", "techno"]:
        print(f"\n--- Generando melodía para: {genero_actual.upper()} ---")
        melodia_resultado = generar_melodia_sobre_acordes(
            acordes_test,
            ritmo_test,
            raiz_test,
            modo_test,
            genero=genero_actual,
            bpm=120,
            octava_melodia_min=4,
            octava_melodia_max=5,
        )
        print(f"Melodía generada ({len(melodia_resultado)} eventos): {melodia_resultado}")
