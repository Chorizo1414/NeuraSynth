# generador_melodia.py
import random
from music21 import note, pitch, scale, harmony, stream, interval, key, chord as m21_chord

class ParametrosMelodicos:
    # Esta clase ahora es más simple, ya que la lógica principal la dictan los perfiles de género.
    def __init__(self, bpm=120, octava_melodia_min=4, octava_melodia_max=5, pulsos_por_compas=4):
        self.bpm = bpm
        self.octava_melodia_min = octava_melodia_min
        self.octava_melodia_max = octava_melodia_max
        self.pulsos_por_compas = pulsos_por_compas
        self.melodia_grid_unit_ql = 0.25  # Semicorchea como base

PERFILES_GENERO = {
    "pop": {
        "tecnicas_preferidas": [("motivo", 0.8), ("arpegio", 0.2)],
        "prob_variacion_A": 0.5,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.65,
        # Ritmo dinámico: mezcla de corcheas, semis y negras
        "complejidad_ritmica": [2, 1, 1, 2, 2, 4, 1, 1, 1, 1, 4],
        "complejidad_motivo": 3,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.25,
    },
    "lofi": {
        "tecnicas_preferidas": [("motivo", 0.95), ("arpegio", 0.05)],
        "prob_variacion_A": 0.6,
        "estructura_frase": "continua",
        "densidad_notas": 0.45,
        # Ritmo dinámico: notas largas (negras, blancas) con corcheas ocasionales
        "complejidad_ritmica": [4, 8, 4, 2, 2, 8, 4],
        "complejidad_motivo": 2,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.3,
    },
    "r&b": {
        "tecnicas_preferidas": [("motivo", 0.9), ("arpegio", 0.1)],
        "prob_variacion_A": 0.7,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.6,
        # Ritmo dinámico: muy sincopado, con tresillos y silencios
        "complejidad_ritmica": [3, 1, 4, 2, 2, 1, 1, 2],
        "complejidad_motivo": 3,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.35,
    },
    "reggaeton": {
        "tecnicas_preferidas": [("motivo", 0.85), ("arpegio", 0.15)],
        "prob_variacion_A": 0.3,
        "estructura_frase": "continua",
        "densidad_notas": 0.7,
        # Ritmo dinámico: patrón dembow clásico pero con variaciones
        "complejidad_ritmica": [1, 1, 2, 1, 1, 4, 2, 1, 1, 2, 4],
        "complejidad_motivo": 2,
        "max_repeticion_nota": 3,
        "prob_nota_de_paso": 0.1,
    },
    "techno": {
        "tecnicas_preferidas": [("arpegio", 0.9), ("motivo", 0.1)],
        "prob_variacion_A": 0.2,
        "estructura_frase": "continua",
        "densidad_notas": 0.85,
        # Ritmo dinámico: flujo de semicorcheas con pausas y corcheas
        "complejidad_ritmica": [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2],
        "complejidad_motivo": 3,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.05,
    },
    "default": {
        "tecnicas_preferidas": [("motivo", 0.7), ("arpegio", 0.3)],
        "prob_variacion_A": 0.4,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.5,
        # Ritmo dinámico: mezcla simple de negras y corcheas
        "complejidad_ritmica": [4, 4, 2, 2, 4, 2, 2, 4],
        "complejidad_motivo": 2,
        "max_repeticion_nota": 2,
        "prob_nota_de_paso": 0.15,
    }
}

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

def _agregar_evento(lista_eventos, pitch_str, duracion):
    duracion = round(duracion, 3)
    if duracion <= 0:
        return lista_eventos
    if pitch_str == "0" and lista_eventos and lista_eventos[-1][0] == "0":
        ultima_dur = float(lista_eventos[-1][1])
        lista_eventos[-1] = ("0", str(round(ultima_dur + duracion, 3)))
    else:
        lista_eventos.append((pitch_str, str(duracion)))
    return lista_eventos

# --- NUEVO MOTOR DE COMPOSICIÓN (A-B-A') ---

def _crear_motivo_musical(notas_acorde_inicial, perfil):
    """Crea un motivo rítmico y melódico que servirá de base (el 'hook')."""
    num_notas = perfil["complejidad_motivo"]
    motivo_ritmico = random.choices(perfil["complejidad_ritmica"], k=num_notas)
    notas_base = random.sample(notas_acorde_inicial, min(num_notas, len(notas_acorde_inicial)))
    if len(notas_base) < num_notas:
        notas_base.extend(random.choices(notas_acorde_inicial, k=num_notas - len(notas_base)))
    return notas_base, motivo_ritmico

def _generar_arpegio_melodico(unidades_totales, notas_acorde, ultima_nota, perfil, params):
    """Genera un arpegio rítmico y melódico."""
    eventos_arpegio = []
    unidades_usadas = 0
    direccion = random.choice([1, -1])
    notas_arpegio = sorted(notas_acorde, key=lambda p: p.midi * direccion)
    posicion_nota = 0
    while unidades_usadas < unidades_totales:
        dur_units = perfil["complejidad_ritmica"][posicion_nota % len(perfil["complejidad_ritmica"])]
        if unidades_usadas + dur_units > unidades_totales: dur_units = unidades_totales - unidades_usadas
        dur_ql = round(dur_units * params.melodia_grid_unit_ql, 3)
        if dur_ql <= 0: break
        if random.random() < perfil["densidad_notas"]:
            nota_actual = notas_arpegio[posicion_nota % len(notas_arpegio)]
            candidato_pitch = _clamp_pitch_to_range(nota_actual, params)
            eventos_arpegio = _agregar_evento(eventos_arpegio, candidato_pitch.nameWithOctave, dur_ql)
            ultima_nota = candidato_pitch
        else:
            eventos_arpegio = _agregar_evento(eventos_arpegio, "0", dur_ql)
        unidades_usadas += dur_units
        posicion_nota += 1
    return eventos_arpegio, ultima_nota

def _generar_frase(unidades_totales, notas_acorde, notas_escala, ultima_nota, motivo, perfil, params, es_respuesta=False):
    """Genera una frase musical (pregunta o respuesta) desarrollando un motivo."""
    eventos_frase = []
    unidades_usadas = 0
    posicion_motivo = 0
    notas_motivo, ritmo_motivo = motivo
    repeticiones_nota_actual = 0
    while unidades_usadas < unidades_totales:
        dur_units = ritmo_motivo[posicion_motivo % len(ritmo_motivo)]
        if unidades_usadas + dur_units > unidades_totales: dur_units = unidades_totales - unidades_usadas
        dur_ql = round(dur_units * params.melodia_grid_unit_ql, 3)
        if dur_ql <= 0: break
        if random.random() < perfil["densidad_notas"]:
            nota_base = notas_motivo[posicion_motivo % len(notas_motivo)]
            if es_respuesta and random.random() < 0.6:
                nota_base = min(notas_acorde, key=lambda n: abs(n.midi - notas_acorde[0].midi))
            if ultima_nota and nota_base.midi == ultima_nota.midi:
                repeticiones_nota_actual += 1
                if repeticiones_nota_actual >= perfil["max_repeticion_nota"]:
                    alternativas = [n for n in notas_acorde if n.midi != ultima_nota.midi]
                    if alternativas: nota_base = random.choice(alternativas)
            else:
                repeticiones_nota_actual = 0
            if random.random() < perfil["prob_nota_de_paso"]:
                vecinos = [p for p in notas_escala if 0 < abs(p.midi - nota_base.midi) <= 2]
                if vecinos: nota_base = random.choice(vecinos)
            candidato_pitch = _clamp_pitch_to_range(nota_base, params)
            eventos_frase = _agregar_evento(eventos_frase, candidato_pitch.nameWithOctave, dur_ql)
            ultima_nota = candidato_pitch
        else:
            eventos_frase = _agregar_evento(eventos_frase, "0", dur_ql)
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
        eventos_frase, ultima_nota_obj = _generar_frase(unidades_frase_actual, notas_acorde_frase, notas_escala_obj, ultima_nota_obj, motivo, perfil, params, es_respuesta)
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
    if not acordes:
        total_dur = sum(float(r) for r in ritmo)
        return [("0", str(total_dur))] if total_dur > 0 else []
    notas_primer_acorde = _expandir_notas_acorde_en_rango(acordes[0], params_mel)
    if not notas_primer_acorde:
        total_dur = sum(float(r) for r in ritmo)
        return [("0", str(total_dur))] if total_dur > 0 else []
    motivo = _crear_motivo_musical(notas_primer_acorde, perfil_actual)
    return _generar_seccion_melodica(acordes, ritmo, "motivo", motivo, perfil_actual, escala_actual, notas_escala_obj, params_mel, None)[0]

# --- Función Principal de Generación de Melodía ---
def generar_melodia_sobre_acordes(
    acordes_progresion,
    ritmo_acordes,
    raiz_tonalidad,
    modo_tonalidad,
    genero="default",
    bpm=120,
    octava_melodia_min=4,
    octava_melodia_max=5,
):
    if not acordes_progresion or not ritmo_acordes or len(acordes_progresion) < 4:
        return _generar_melodia_simple(acordes_progresion, ritmo_acordes, raiz_tonalidad, modo_tonalidad, genero, bpm, octava_melodia_min, octava_melodia_max)

    perfil_actual = PERFILES_GENERO.get(str(genero).lower(), PERFILES_GENERO["default"])
    params_mel = ParametrosMelodicos(bpm=bpm, octava_melodia_min=octava_melodia_min, octava_melodia_max=octava_melodia_max)
    _ajustar_rango_melodia_a_progresion(params_mel, acordes_progresion)
    escala_actual = obtener_escala_actual(raiz_tonalidad, modo_tonalidad)
    notas_escala_disponibles_obj = _obtener_notas_escala_en_rango(escala_actual, params_mel)
    
    tecnicas, pesos = zip(*perfil_actual["tecnicas_preferidas"])
    tecnica_elegida = random.choices(tecnicas, weights=pesos, k=1)[0]
    print(f"DEBUG (Melodia): ESTRUCTURA A-B-A'. Técnica elegida: {tecnica_elegida}")

    num_acordes = len(acordes_progresion)
    punto_corte_A = num_acordes // 2
    punto_corte_B = punto_corte_A + max(2, num_acordes // 4)
    if punto_corte_B >= num_acordes: punto_corte_B = num_acordes -1
    if punto_corte_A >= punto_corte_B: punto_corte_A = 0
    if punto_corte_A < 0: punto_corte_A = 0
    
    segmento_A_acordes, segmento_A_ritmos = acordes_progresion[:punto_corte_A], ritmo_acordes[:punto_corte_A]
    segmento_B_acordes, segmento_B_ritmos = acordes_progresion[punto_corte_A:punto_corte_B], ritmo_acordes[punto_corte_A:punto_corte_B]
    segmento_A2_acordes, segmento_A2_ritmos = acordes_progresion[punto_corte_B:], ritmo_acordes[punto_corte_B:]

    if not segmento_A_acordes or not segmento_B_acordes or not segmento_A2_acordes:
         return _generar_melodia_simple(acordes_progresion, ritmo_acordes, raiz_tonalidad, modo_tonalidad, genero, bpm, octava_melodia_min, octava_melodia_max)

    notas_primer_acorde = _expandir_notas_acorde_en_rango(segmento_A_acordes[0], params_mel)
    if not notas_primer_acorde:
        total_dur = sum(float(r) for r in ritmo_acordes)
        return [("0", str(total_dur))] if total_dur > 0 else []

    motivo_principal = _crear_motivo_musical(notas_primer_acorde, perfil_actual)
    melodia_A, ultima_nota_A = _generar_seccion_melodica(segmento_A_acordes, segmento_A_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)
    
    notas_acorde_B = _expandir_notas_acorde_en_rango(segmento_B_acordes[0], params_mel) if segmento_B_acordes else notas_primer_acorde
    motivo_B = _crear_motivo_musical(notas_acorde_B, perfil_actual)
    melodia_B, _ = _generar_seccion_melodica(segmento_B_acordes, segmento_B_ritmos, tecnica_elegida, motivo_B, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, ultima_nota_A)
    
    if random.random() < perfil_actual["prob_variacion_A"]:
        print("DEBUG (Melodia): Generando variación A'")
        melodia_A_base_para_variacion, _ = _generar_seccion_melodica(segmento_A2_acordes, segmento_A2_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)
        melodia_A2 = _variar_melodia(melodia_A_base_para_variacion, notas_escala_disponibles_obj, params_mel)
    else:
        print("DEBUG (Melodia): Repitiendo sección A")
        melodia_A2, _ = _generar_seccion_melodica(segmento_A2_acordes, segmento_A2_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)

    return melodia_A + melodia_B + melodia_A2


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

# --- FIN DEL BLOQUE PARA PEGAR ---