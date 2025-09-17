# generador_melodia.py
import random
from music21 import note, pitch, scale, harmony, stream, interval, key, chord as m21_chord

class ParametrosMelodicos:
    def __init__(self,
                 bpm=120,
                 densidad_notas=0.65, # Probabilidad de que una subdivisión de la cuadrícula tenga una nota vs silencio
                 octava_melodia_min=4, # Octava MIDI más grave para la melodía (ej. C4 = 4)
                 octava_melodia_max=5, # Octava MIDI más aguda
                 aplicar_repeticion_estructural=True, # Para técnicas como pregunta-respuesta o si la progresión se repite
                 probabilidad_arpegio=0.15,      # Usado por técnica default/híbrida
                 probabilidad_contorno=0.25,     # Usado por técnica default/híbrida
                 melodia_grid_unit_ql=0.25,      # Cuadrícula rítmica base (0.25 = semicorchea)
                 melodia_min_note_multiples=1,   # Mínima duración = grid * min_multiples (ej. 1*0.25 = semicorchea)
                 melodia_max_note_multiples=8,   # Máxima duración = grid * max_multiples (ej. 8*0.25 = negra)
                 max_notas_cortas_consecutivas=2, # Máx. notas de duración mínima seguidas
                 priorizar_acentos_en_beats=True, # Intentar poner notas del acorde en tiempos fuertes
                 pulsos_por_compas=4,             # Para la lógica de acentos (ej. 4 para 4/4)
                 prob_preferir_paso_conjunto=0.75,# Probabilidad de moverse por grado conjunto vs salto
                 max_semitonos_salto=7,           # Límite de salto en semitonos (una 5ta justa)
                 max_consecutive_same_duration_notes=3, # Máx. notas seguidas con la misma duración
                 max_consecutive_same_pitch_eighth_notes=2, # Máx. corcheas seguidas con la misma altura
                 eighth_note_ql_ref=0.5,                  # Duración de referencia para una corchea
                 resolver_tensiones_diatonicas=True,     # Intentar resolver notas fuera del acorde
                 min_notas_contorno=3,                  # Para la técnica de contorno
                 max_notas_contorno=5                   # Para la técnica de contorno
                 ):
        self.bpm = bpm
        self.densidad_notas = densidad_notas
        self.octava_melodia_min = octava_melodia_min
        self.octava_melodia_max = octava_melodia_max
        self.aplicar_repeticion_estructural = aplicar_repeticion_estructural
        self.probabilidad_arpegio = probabilidad_arpegio
        self.probabilidad_contorno = probabilidad_contorno
        self.melodia_grid_unit_ql = melodia_grid_unit_ql
        self.melodia_min_note_multiples = melodia_min_note_multiples
        self.melodia_max_note_multiples = melodia_max_note_multiples
        self.max_notas_cortas_consecutivas = max_notas_cortas_consecutivas
        self.priorizar_acentos_en_beats = priorizar_acentos_en_beats
        self.pulsos_por_compas = pulsos_por_compas
        self.prob_preferir_paso_conjunto = prob_preferir_paso_conjunto
        self.max_semitonos_salto = max_semitonos_salto
        self.max_consecutive_same_duration_notes = max_consecutive_same_duration_notes
        self.max_consecutive_same_pitch_eighth_notes = max_consecutive_same_pitch_eighth_notes
        self.eighth_note_ql_ref = eighth_note_ql_ref
        self.resolver_tensiones_diatonicas = resolver_tensiones_diatonicas
        self.min_notas_contorno = min_notas_contorno
        self.max_notas_contorno = max_notas_contorno

def notas_del_acorde_music21(acorde_data_o_lista_str):
    pitches_obj_list = []
    lista_notas_str = []
    if isinstance(acorde_data_o_lista_str, list):
        lista_notas_str = acorde_data_o_lista_str
    elif isinstance(acorde_data_o_lista_str, str) and acorde_data_o_lista_str not in ["0", "N/A"]:
        try:
            cs = harmony.ChordSymbol(acorde_data_o_lista_str)
            lista_notas_str = [p.name for p in cs.pitches]
        except: pass
    elif isinstance(acorde_data_o_lista_str, str) and acorde_data_o_lista_str.startswith("SN_"):
        lista_notas_str = [acorde_data_o_lista_str[3:]]

    for n_str in lista_notas_str:
        try:
            p = pitch.Pitch(n_str)
            pitches_obj_list.append(p)
        except Exception as e: print(f"Advertencia (notas_del_acorde): No se pudo crear Pitch para '{n_str}': {e}")
    return pitches_obj_list

def obtener_escala_actual(raiz_str, modo_str):
    try:
        modo_m21 = modo_str.lower()
        if modo_m21 == "mayor": modo_m21 = "major"
        elif modo_m21 == "menor": modo_m21 = "minor"
        k_raiz_pitch = pitch.Pitch(raiz_str)
        k_raiz_nombre = k_raiz_pitch.name
        k = key.Key(k_raiz_nombre, modo_m21)
        return k.getScale()
    except Exception as e:
        print(f"Error obteniendo escala para {raiz_str} {modo_str}: {e}. Usando C Mayor.")
        return scale.MajorScale("C")

LISTA_TECNICAS_MELODICAS = [
    "default", "esqueleto_pasos_vecinos", "guia_terceras_septimas",
    "contornos_clasicos_variados", "pregunta_respuesta", "secuencias_motivo",
    "arpegio_hibrido_mejorado", "intervalos_3_1_relleno", "envoltura_ritmica_fija",
    "envoltura_melodica_fija_ritmo_libre", "tension_relajacion_target", "transformaciones_motivicas"
]

def generar_arpegio_simple(acorde_data, duracion_total_acorde, octava_min, octava_max, melodia_grid_unit_ql):
    arpegio_eventos = []
    ultimo_pitch_arpegio = None
    notas_del_acorde_obj_sin_octava = notas_del_acorde_music21(acorde_data)
    MAX_NOTAS_PARA_ARPEGIO_SIMPLE = 3
    notas_arpegio_en_rango = []
    if notas_del_acorde_obj_sin_octava:
        pitches_base_ordenados = sorted(list(set(p.name for p in notas_del_acorde_obj_sin_octava)))
        for nota_nombre_base in pitches_base_ordenados:
            for oct_cand in range(octava_min, octava_max + 1):
                try:
                    p_temp = pitch.Pitch(f"{nota_nombre_base}{oct_cand}")
                    if p_temp not in notas_arpegio_en_rango: notas_arpegio_en_rango.append(p_temp)
                    break
                except Exception: continue
        notas_arpegio_en_rango = sorted(list(set(notas_arpegio_en_rango)), key=lambda p: p.ps)
        if len(notas_arpegio_en_rango) > MAX_NOTAS_PARA_ARPEGIO_SIMPLE: notas_arpegio_en_rango = notas_arpegio_en_rango[:MAX_NOTAS_PARA_ARPEGIO_SIMPLE]
    if not notas_arpegio_en_rango:
        if duracion_total_acorde > 0: arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
        return arpegio_eventos, None
    num_notas_arpegio = len(notas_arpegio_en_rango)
    if num_notas_arpegio == 0:
        if duracion_total_acorde > 0: arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
        return arpegio_eventos, None
    total_grid_units_en_acorde = int(duracion_total_acorde / melodia_grid_unit_ql) if melodia_grid_unit_ql > 0 else 0
    if total_grid_units_en_acorde < num_notas_arpegio:
        if duracion_total_acorde > 0: arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
        return arpegio_eventos, None
    grid_units_por_nota = total_grid_units_en_acorde // num_notas_arpegio if num_notas_arpegio > 0 else 0
    grid_units_restantes = total_grid_units_en_acorde % num_notas_arpegio if num_notas_arpegio > 0 else 0
    if grid_units_por_nota == 0:
         if duracion_total_acorde > 0: arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
         return arpegio_eventos, None
    dur_asignada_total = 0.0
    for i_arp, p_obj in enumerate(notas_arpegio_en_rango):
        dur_actual_nota_units = grid_units_por_nota
        if grid_units_restantes > 0:
            dur_actual_nota_units += 1
            grid_units_restantes -= 1
        dur_actual_nota_ql = round(dur_actual_nota_units * melodia_grid_unit_ql, 3)
        if dur_actual_nota_ql <= 0: continue
        arpegio_eventos.append((p_obj.nameWithOctave, str(dur_actual_nota_ql)))
        ultimo_pitch_arpegio = p_obj
        dur_asignada_total += dur_actual_nota_ql
    tiempo_restante_final = round(duracion_total_acorde - dur_asignada_total, 3)
    if tiempo_restante_final > 0.01:
        if arpegio_eventos and arpegio_eventos[-1][0] == "0":
            prev_silence_dur = float(arpegio_eventos[-1][1])
            arpegio_eventos[-1] = ("0", str(round(prev_silence_dur + tiempo_restante_final, 3)))
        else:
            arpegio_eventos.append(("0", str(tiempo_restante_final)))
    return arpegio_eventos, ultimo_pitch_arpegio

def generar_contorno_arco(nota_inicio_obj, duracion_total_contorno, num_pasos_contorno, escala_obj, octava_min, octava_max, max_salto_semitonos_contorno=4, melodia_grid_unit_ql=0.25):
    eventos_contorno = []
    if not nota_inicio_obj or num_pasos_contorno < 2:
        if duracion_total_contorno > 0: eventos_contorno.append(("0", str(duracion_total_contorno)))
        return eventos_contorno, nota_inicio_obj
    total_grid_units_en_contorno = int(duracion_total_contorno / melodia_grid_unit_ql) if melodia_grid_unit_ql > 0 else 0
    if total_grid_units_en_contorno < num_pasos_contorno:
        if duracion_total_contorno > 0: eventos_contorno.append(("0", str(duracion_total_contorno)))
        return eventos_contorno, nota_inicio_obj
    grid_units_por_paso = total_grid_units_en_contorno // num_pasos_contorno if num_pasos_contorno > 0 else 0
    grid_units_restantes_contorno = total_grid_units_en_contorno % num_pasos_contorno if num_pasos_contorno > 0 else 0
    if grid_units_por_paso == 0:
        if duracion_total_contorno > 0: eventos_contorno.append(("0", str(duracion_total_contorno)))
        return eventos_contorno, nota_inicio_obj
    punto_medio_pasos = num_pasos_contorno // 2
    nota_actual_obj = nota_inicio_obj
    if nota_actual_obj.octave < octava_min: nota_actual_obj.octave = octava_min
    if nota_actual_obj.octave > octava_max: nota_actual_obj.octave = octava_max
    tiempo_asignado_contorno = 0.0
    notas_generadas_contorno = [nota_actual_obj]
    ultimo_pitch_contorno = nota_inicio_obj
    for _ in range(1, punto_medio_pasos + (num_pasos_contorno % 2)):
        notas_candidatas_mov = []
        nota_temporal_para_busqueda = nota_actual_obj
        for step_sz in range(1, max_salto_semitonos_contorno + 2):
            try:
                nota_siguiente_obj = escala_obj.nextPitch(nota_temporal_para_busqueda, stepSize=1, direction=scale.Direction.ASCENDING)
                if octava_min <= nota_siguiente_obj.octave <= octava_max:
                    if abs(interval.Interval(nota_actual_obj, nota_siguiente_obj).semitones) <= max_salto_semitonos_contorno:
                        notas_candidatas_mov.append(nota_siguiente_obj)
                nota_temporal_para_busqueda = nota_siguiente_obj
                if notas_candidatas_mov: break
            except Exception: break
        if notas_candidatas_mov: nota_actual_obj = random.choice(notas_candidatas_mov)
        notas_generadas_contorno.append(nota_actual_obj)
    for _ in range(punto_medio_pasos + (num_pasos_contorno % 2), num_pasos_contorno):
        notas_candidatas_mov = []
        nota_temporal_para_busqueda = nota_actual_obj
        for step_sz in range(1, max_salto_semitonos_contorno + 2):
            try:
                nota_siguiente_obj = escala_obj.previousPitch(nota_temporal_para_busqueda, stepSize=1, direction=scale.Direction.DESCENDING)
                if octava_min <= nota_siguiente_obj.octave <= octava_max:
                     if abs(interval.Interval(nota_actual_obj, nota_siguiente_obj).semitones) <= max_salto_semitonos_contorno:
                        notas_candidatas_mov.append(nota_siguiente_obj)
                nota_temporal_para_busqueda = nota_siguiente_obj
                if notas_candidatas_mov: break
            except Exception: break
        if notas_candidatas_mov: nota_actual_obj = random.choice(notas_candidatas_mov)
        notas_generadas_contorno.append(nota_actual_obj)
    if len(notas_generadas_contorno) != num_pasos_contorno:
        notas_generadas_contorno = notas_generadas_contorno[:num_pasos_contorno]
        while len(notas_generadas_contorno) < num_pasos_contorno:
            notas_generadas_contorno.append(notas_generadas_contorno[-1] if notas_generadas_contorno else nota_inicio_obj)
    for i_cont, p_obj_cont in enumerate(notas_generadas_contorno):
        dur_actual_nota_units = grid_units_por_paso
        if grid_units_restantes_contorno > 0:
            dur_actual_nota_units += 1
            grid_units_restantes_contorno -=1
        dur_actual_nota_ql = round(dur_actual_nota_units * melodia_grid_unit_ql, 3)
        if dur_actual_nota_ql <=0: continue
        eventos_contorno.append((p_obj_cont.nameWithOctave, str(dur_actual_nota_ql)))
        tiempo_asignado_contorno += dur_actual_nota_ql
        ultimo_pitch_contorno = p_obj_cont
    tiempo_restante_final_contorno = round(duracion_total_contorno - tiempo_asignado_contorno, 3)
    if tiempo_restante_final_contorno > 0.01:
        if eventos_contorno and eventos_contorno[-1][0] == "0":
            prev_dur = float(eventos_contorno[-1][1])
            eventos_contorno[-1] = ("0", str(round(prev_dur + tiempo_restante_final_contorno, 3)))
        else:
            eventos_contorno.append(("0", str(tiempo_restante_final_contorno)))
    return eventos_contorno, ultimo_pitch_contorno

def _generar_melodia_default_segmento(
    segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj,
    params: ParametrosMelodicos,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento
):
    # ... (COPIA AQUÍ EL CUERPO COMPLETO DE TU FUNCIÓN _generar_segmento_melodia ORIGINAL)
    # Este es solo un placeholder para que el código sea ejecutable.
    # Debes reemplazar esto con tu lógica original.
    print(f"DEBUG (Melodia): Usando técnica 'default' (algorítmica general). BPM interno: {params.bpm}") # Verificación de BPM
    segmento_melodia_final = []
    _ultima_nota_interna_pitch_obj = ultima_nota_global_pitch_obj
    _consecutive_short_notes_count = 0
    _consecutive_same_duration_count = 0
    _last_generated_duration_ql = -1.0
    _consecutive_same_pitch_eighth_count = 0
    _last_pitch_of_eighth_note = None
    _ultima_nota_fue_tension = False
    _pitch_de_tension_anterior = None
    min_duracion_nota_permitida_ql = params.melodia_grid_unit_ql * params.melodia_min_note_multiples
    posibles_duraciones_ql = []
    for m in range(params.melodia_min_note_multiples, params.melodia_max_note_multiples + 1):
        posibles_duraciones_ql.append(round(m * params.melodia_grid_unit_ql, 3))
    posibles_duraciones_ql = sorted(list(set(d for d in posibles_duraciones_ql if d > 0)))
    if not posibles_duraciones_ql:
        posibles_duraciones_ql = [params.melodia_grid_unit_ql] if params.melodia_grid_unit_ql > 0 else [0.25]

    for i, acorde_actual_data in enumerate(segmento_acordes):
        duracion_acorde_actual = float(segmento_ritmos[i % len(segmento_ritmos)])
        notas_base_del_acorde_actual_obj = notas_del_acorde_music21(acorde_actual_data)
        notas_acorde_en_rango_obj = []
        nombres_notas_acorde_actual_set = set()
        if notas_base_del_acorde_actual_obj:
            for p_base in notas_base_del_acorde_actual_obj:
                nombres_notas_acorde_actual_set.add(p_base.name)
                for oct_cand in range(params.octava_melodia_min, params.octava_melodia_max + 1):
                    try:
                        p_temp = pitch.Pitch(p_base.name); p_temp.octave = oct_cand
                        if p_temp not in notas_acorde_en_rango_obj: notas_acorde_en_rango_obj.append(p_temp)
                    except: continue
            notas_acorde_en_rango_obj = sorted(list(set(notas_acorde_en_rango_obj)), key=lambda p:p.ps)
        if duracion_acorde_actual <= 0: continue
        tecnica_elegida_sub = "paso_vecino_salto" # Nombre de la sub-técnica dentro de default
        rand_val = random.random()
        if isinstance(acorde_actual_data, list) and notas_acorde_en_rango_obj: # Solo si es un acorde y hay notas válidas
            if rand_val < params.probabilidad_arpegio: tecnica_elegida_sub = "arpegio"
            elif rand_val < params.probabilidad_arpegio + params.probabilidad_contorno: tecnica_elegida_sub = "contorno_arco"

        if tecnica_elegida_sub == "arpegio":
            arpegio_notas_durs, ultima_nota_tec = generar_arpegio_simple(acorde_actual_data, duracion_acorde_actual, params.octava_melodia_min, params.octava_melodia_max, params.melodia_grid_unit_ql)
            if arpegio_notas_durs and not (len(arpegio_notas_durs) == 1 and arpegio_notas_durs[0][0] == "0"):
                segmento_melodia_final.extend(arpegio_notas_durs)
                if ultima_nota_tec: _ultima_nota_interna_pitch_obj = ultima_nota_tec
                _ultima_nota_fue_tension = False; _consecutive_short_notes_count = 0; _consecutive_same_duration_count = 0; _last_generated_duration_ql = -1.0; _consecutive_same_pitch_eighth_count = 0; _last_pitch_of_eighth_note = None
                continue
            else: tecnica_elegida_sub = "paso_vecino_salto"
        if tecnica_elegida_sub == "contorno_arco":
            nota_inicio_contorno = None
            if notas_acorde_en_rango_obj: nota_inicio_contorno = random.choice(notas_acorde_en_rango_obj)
            elif _ultima_nota_interna_pitch_obj: nota_inicio_contorno = _ultima_nota_interna_pitch_obj
            elif notas_escala_disponibles_obj: nota_inicio_contorno = random.choice(notas_escala_disponibles_obj)
            if nota_inicio_contorno:
                num_pasos_contorno = random.randint(params.min_notas_contorno, params.max_notas_contorno)
                if num_pasos_contorno * params.melodia_grid_unit_ql > duracion_acorde_actual and duracion_acorde_actual > params.melodia_grid_unit_ql:
                    num_pasos_contorno = max(2, int(duracion_acorde_actual / params.melodia_grid_unit_ql))
                if num_pasos_contorno >=2 :
                    contorno_eventos, ultima_nota_tec = generar_contorno_arco(nota_inicio_contorno, duracion_acorde_actual, num_pasos_contorno, escala_actual, params.octava_melodia_min, params.octava_melodia_max, max_salto_semitonos_contorno=params.max_semitonos_salto, melodia_grid_unit_ql=params.melodia_grid_unit_ql)
                    if contorno_eventos and not (len(contorno_eventos) == 1 and contorno_eventos[0][0] == "0"):
                        segmento_melodia_final.extend(contorno_eventos)
                        if ultima_nota_tec: _ultima_nota_interna_pitch_obj = ultima_nota_tec
                        _ultima_nota_fue_tension = False; _consecutive_short_notes_count = 0; _consecutive_same_duration_count = 0; _last_generated_duration_ql = -1.0; _consecutive_same_pitch_eighth_count = 0; _last_pitch_of_eighth_note = None
                        continue
                    else: tecnica_elegida_sub = "paso_vecino_salto"
            else: tecnica_elegida_sub = "paso_vecino_salto"
        
        tiempo_restante_en_acorde = duracion_acorde_actual
        tiempo_transcurrido_en_acorde_actual = 0.0
        while tiempo_restante_en_acorde >= params.melodia_grid_unit_ql - 0.001 :
            opciones_dur_grid_que_caben = [d for d in posibles_duraciones_ql if d <= tiempo_restante_en_acorde + 0.001]
            if not opciones_dur_grid_que_caben: break
            dur_evento_actual = random.choice(opciones_dur_grid_que_caben)
            nota_elegida_obj_ph = random.choice(notas_escala_disponibles_obj) if notas_escala_disponibles_obj else pitch.Pitch("C4")
            if random.random() < params.densidad_notas:
                segmento_melodia_final.append((nota_elegida_obj_ph.nameWithOctave, str(dur_evento_actual)))
                _ultima_nota_interna_pitch_obj = nota_elegida_obj_ph
            else:
                segmento_melodia_final.append(("0", str(dur_evento_actual)))
                _ultima_nota_interna_pitch_obj = None
            tiempo_transcurrido_en_acorde_actual += dur_evento_actual
            tiempo_restante_en_acorde -= dur_evento_actual
            tiempo_restante_en_acorde = round(tiempo_restante_en_acorde, 3)
        if tiempo_restante_en_acorde > 0.01:
            if segmento_melodia_final and segmento_melodia_final[-1][0] == "0":
                prev_dur = float(segmento_melodia_final[-1][1])
                segmento_melodia_final[-1] = ("0", str(round(prev_dur + tiempo_restante_en_acorde, 3)))
            else:
                segmento_melodia_final.append(("0", str(round(tiempo_restante_en_acorde, 3))))
    return segmento_melodia_final, _ultima_nota_interna_pitch_obj


def _generar_melodia_esqueleto_pasos(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj,
                                     params: ParametrosMelodicos, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Usando técnica 'esqueleto_pasos_vecinos'. BPM interno: {params.bpm}")
    melodia_final_tec1 = []
    _ultima_nota_tec1_obj = ultima_nota_global_pitch_obj
    tiempo_total_acumulado_global = 0.0

    for i, acorde_actual_data in enumerate(segmento_acordes):
        duracion_acorde_actual_ql = float(segmento_ritmos[i % len(segmento_ritmos)])
        notas_del_acorde_actual_obj_base = notas_del_acorde_music21(acorde_actual_data)

        notas_acorde_en_rango_actual = []
        if notas_del_acorde_actual_obj_base:
            for p_base in notas_del_acorde_actual_obj_base:
                for oct_cand in range(params.octava_melodia_min, params.octava_melodia_max + 1):
                    try:
                        p_temp = pitch.Pitch(p_base.name); p_temp.octave = oct_cand
                        if p_temp not in notas_acorde_en_rango_actual: notas_acorde_en_rango_actual.append(p_temp)
                    except: continue
            notas_acorde_en_rango_actual = sorted(list(set(notas_acorde_en_rango_actual)), key=lambda p:p.ps)
        
        if not notas_acorde_en_rango_actual:
            if notas_escala_disponibles_obj:
                notas_acorde_en_rango_actual = [p for p in notas_escala_disponibles_obj if escala_actual.getScaleDegreeFromPitch(p) == 1]
                if not notas_acorde_en_rango_actual: notas_acorde_en_rango_actual = [random.choice(notas_escala_disponibles_obj)]
            else:
                notas_acorde_en_rango_actual = [pitch.Pitch(f"{raiz_tonalidad_segmento}{params.octava_melodia_min}")]

        tiempo_restante_en_acorde_ql = duracion_acorde_actual_ql
        tiempo_transcurrido_en_acorde_ql = 0.0
        
        while tiempo_restante_en_acorde_ql >= params.melodia_grid_unit_ql - 0.001:
            offset_absoluto_beat_actual = tiempo_total_acumulado_global + tiempo_transcurrido_en_acorde_ql
            offset_relativo_compas_actual = offset_absoluto_beat_actual % params.pulsos_por_compas
            
            es_beat_fuerte_actual = False
            beats_fuertes_definidos = [0.0]
            if params.pulsos_por_compas == 4: beats_fuertes_definidos.append(2.0)
            elif params.pulsos_por_compas == 3: beats_fuertes_definidos.extend([1.0, 2.0])
            
            for bf_compas in beats_fuertes_definidos:
                if abs(offset_relativo_compas_actual - bf_compas) < params.melodia_grid_unit_ql / 2.0:
                    es_beat_fuerte_actual = True
                    break
            
            nota_a_colocar_obj = None
            dur_nota_actual_ql = params.melodia_grid_unit_ql

            if es_beat_fuerte_actual and notas_acorde_en_rango_actual:
                if isinstance(acorde_actual_data, str) and acorde_actual_data not in ["0", "N/A"]:
                    try:
                        cs = harmony.ChordSymbol(acorde_actual_data)
                        grados_deseados = [cs.getChordStep(1), cs.getChordStep(3), cs.getChordStep(5), cs.getChordStep(7)]
                        grados_validos_en_rango = [p for p in grados_deseados if p and params.octava_melodia_min <= p.octave <= params.octava_melodia_max]
                        if grados_validos_en_rango: nota_a_colocar_obj = random.choice(grados_validos_en_rango)
                    except: pass
                if not nota_a_colocar_obj:
                    nota_a_colocar_obj = random.choice(notas_acorde_en_rango_actual)
                
                if random.random() < 0.6 and tiempo_restante_en_acorde_ql >= params.melodia_grid_unit_ql * 2:
                    dur_nota_actual_ql = params.melodia_grid_unit_ql * 2
                elif tiempo_restante_en_acorde_ql >= params.melodia_grid_unit_ql * 4:
                     if random.random() < 0.3: dur_nota_actual_ql = params.melodia_grid_unit_ql * 4
            else:
                if _ultima_nota_tec1_obj and notas_escala_disponibles_obj:
                    candidatas_paso_vecino = []
                    for p_escala in notas_escala_disponibles_obj:
                        try:
                            semitonos_dist = abs(interval.Interval(_ultima_nota_tec1_obj, p_escala).semitones)
                            if 0 < semitonos_dist <= 2:
                                candidatas_paso_vecino.append(p_escala)
                        except: continue
                    
                    if candidatas_paso_vecino:
                        nota_a_colocar_obj = random.choice(candidatas_paso_vecino)
                    elif notas_acorde_en_rango_actual:
                        nota_a_colocar_obj = random.choice(notas_acorde_en_rango_actual)
                    else:
                        nota_a_colocar_obj = _ultima_nota_tec1_obj
                elif notas_acorde_en_rango_actual:
                     nota_a_colocar_obj = random.choice(notas_acorde_en_rango_actual)
                elif notas_escala_disponibles_obj:
                     nota_a_colocar_obj = random.choice(notas_escala_disponibles_obj)

            if nota_a_colocar_obj and random.random() < params.densidad_notas:
                dur_nota_actual_ql = min(dur_nota_actual_ql, tiempo_restante_en_acorde_ql)
                dur_nota_actual_ql = round(int(dur_nota_actual_ql / params.melodia_grid_unit_ql) * params.melodia_grid_unit_ql, 3)
                if dur_nota_actual_ql < params.melodia_grid_unit_ql - 0.001: break

                melodia_final_tec1.append((nota_a_colocar_obj.nameWithOctave, str(dur_nota_actual_ql)))
                _ultima_nota_tec1_obj = nota_a_colocar_obj
                tiempo_transcurrido_en_acorde_ql += dur_nota_actual_ql
                tiempo_restante_en_acorde_ql -= dur_nota_actual_ql
            else:
                dur_silencio_ql = params.melodia_grid_unit_ql
                dur_silencio_ql = min(dur_silencio_ql, tiempo_restante_en_acorde_ql)
                dur_silencio_ql = round(int(dur_silencio_ql / params.melodia_grid_unit_ql) * params.melodia_grid_unit_ql, 3)
                if dur_silencio_ql < params.melodia_grid_unit_ql - 0.001: break

                melodia_final_tec1.append(("0", str(dur_silencio_ql)))
                tiempo_transcurrido_en_acorde_ql += dur_silencio_ql
                tiempo_restante_en_acorde_ql -= dur_silencio_ql
            
            tiempo_restante_en_acorde_ql = round(tiempo_restante_en_acorde_ql, 3)
        tiempo_total_acumulado_global += duracion_acorde_actual_ql

    if not melodia_final_tec1:
        total_dur_prog = sum(float(r) for r in segmento_ritmos)
        if total_dur_prog > 0: melodia_final_tec1.append(("0", str(total_dur_prog)))
    return melodia_final_tec1, _ultima_nota_tec1_obj

# --- Stubs para las demás técnicas ---
def _generar_melodia_guia_tonos(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'guia_terceras_septimas' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_contornos_clasicos(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'contornos_clasicos_variados' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

# ... (resto de los stubs de técnicas, añadiendo el print del BPM) ...
def _generar_melodia_pregunta_respuesta(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'pregunta_respuesta' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_secuencias_motivo(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'secuencias_motivo' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_arpegio_hibrido(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'arpegio_hibrido_mejorado' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_intervalos_3_1(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'intervalos_3_1_relleno' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_envoltura_ritmica_fija(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'envoltura_ritmica_fija' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_envoltura_melodica_fija(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'envoltura_melodica_fija_ritmo_libre' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_tension_relajacion(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'tension_relajacion_target' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)

def _generar_melodia_transformaciones_motivicas(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento):
    print(f"DEBUG (Melodia): Técnica 'transformaciones_motivicas' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}")
    return _generar_melodia_default_segmento(segmento_acordes, segmento_ritmos, escala_actual, notas_escala_disponibles_obj, params, ultima_nota_global_pitch_obj, raiz_tonalidad_segmento)


# --- Función Principal de Generación de Melodía ---
def generar_melodia_sobre_acordes(acordes_progresion, ritmo_acordes,
                                 raiz_tonalidad, modo_tonalidad,
                                 tecnica_seleccionada_externa=None,
                                 bpm=120, densidad_notas=0.65,
                                 octava_melodia_min=4, octava_melodia_max=5,
                                 prob_preferir_paso_conjunto=0.75,
                                 max_semitonos_salto=7,
                                 # ... (otros parámetros de ParametrosMelodicos que quieras exponer)
                                 ):
    melodia_final = []
    if not acordes_progresion or not ritmo_acordes: return melodia_final

    params_mel = ParametrosMelodicos(
        bpm=bpm, densidad_notas=densidad_notas,
        octava_melodia_min=octava_melodia_min, octava_melodia_max=octava_melodia_max,
        prob_preferir_paso_conjunto=prob_preferir_paso_conjunto,
        max_semitonos_salto=max_semitonos_salto
        # Asegúrate de pasar/inicializar todos los parámetros que usan tus técnicas
    )
    # Imprimir el BPM que se está usando para la generación de esta melodía
    print(f"INFO (Generador Melodia): Iniciando generación de melodía con BPM: {params_mel.bpm}")

    escala_actual = obtener_escala_actual(raiz_tonalidad, modo_tonalidad)
    notas_escala_disponibles_obj = []
    for p_escala_base in escala_actual.pitches:
        if isinstance(p_escala_base, pitch.Pitch):
            for oct_num in range(params_mel.octava_melodia_min, params_mel.octava_melodia_max + 1):
                try:
                    p_temp = pitch.Pitch(p_escala_base.name); p_temp.octave = oct_num
                    if p_temp not in notas_escala_disponibles_obj: notas_escala_disponibles_obj.append(p_temp)
                except: continue
    notas_escala_disponibles_obj = sorted(list(set(notas_escala_disponibles_obj)), key=lambda p:p.ps)

    if not notas_escala_disponibles_obj:
        print("ADVERTENCIA (generador_melodia): No hay notas de escala disponibles.");
        total_dur_silencio = sum(float(d) for d in ritmo_acordes) if ritmo_acordes else 0
        if total_dur_silencio > 0: melodia_final.append(("0", str(total_dur_silencio)))
        return melodia_final

    tecnica_a_usar = tecnica_seleccionada_externa
    if tecnica_a_usar is None or tecnica_a_usar not in LISTA_TECNICAS_MELODICAS:
        pesos = [5 if t == "default" else 3 if t == "esqueleto_pasos_vecinos" else 1 for t in LISTA_TECNICAS_MELODICAS]
        tecnica_a_usar = random.choices(LISTA_TECNICAS_MELODICAS, weights=pesos, k=1)[0]
    
    print(f"INFO (Melodia): Técnica seleccionada: {tecnica_a_usar}")

    args_comunes = (acordes_progresion, ritmo_acordes, escala_actual, notas_escala_disponibles_obj, params_mel, None, raiz_tonalidad)
    
    if tecnica_a_usar == "default":
        if params_mel.aplicar_repeticion_estructural and len(acordes_progresion) >= 2 and len(acordes_progresion) % 2 == 0:
            punto_medio = len(acordes_progresion) // 2
            melodia_seg1, ult_nota1 = _generar_melodia_default_segmento(acordes_progresion[:punto_medio], ritmo_acordes[:punto_medio], *args_comunes[2:])
            melodia_final.extend(melodia_seg1)
            if acordes_progresion[punto_medio:] == acordes_progresion[:punto_medio] and ritmo_acordes[punto_medio:] == ritmo_acordes[:punto_medio]:
                melodia_final.extend(melodia_seg1)
            else:
                args_seg2 = (acordes_progresion[punto_medio:], ritmo_acordes[punto_medio:], escala_actual, notas_escala_disponibles_obj, params_mel, ult_nota1, raiz_tonalidad)
                melodia_seg2, _ = _generar_melodia_default_segmento(*args_seg2)
                melodia_final.extend(melodia_seg2)
        else:
            melodia_generada, _ = _generar_melodia_default_segmento(*args_comunes)
            melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "esqueleto_pasos_vecinos":
        melodia_generada, _ = _generar_melodia_esqueleto_pasos(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "guia_terceras_septimas":
        melodia_generada, _ = _generar_melodia_guia_tonos(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "contornos_clasicos_variados":
        melodia_generada, _ = _generar_melodia_contornos_clasicos(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "pregunta_respuesta":
         melodia_generada, _ = _generar_melodia_pregunta_respuesta(*args_comunes)
         melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "secuencias_motivo":
        melodia_generada, _ = _generar_melodia_secuencias_motivo(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "arpegio_hibrido_mejorado":
        melodia_generada, _ = _generar_melodia_arpegio_hibrido(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "intervalos_3_1_relleno":
        melodia_generada, _ = _generar_melodia_intervalos_3_1(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "envoltura_ritmica_fija":
        melodia_generada, _ = _generar_melodia_envoltura_ritmica_fija(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "envoltura_melodica_fija_ritmo_libre":
        melodia_generada, _ = _generar_melodia_envoltura_melodica_fija(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "tension_relajacion_target":
        melodia_generada, _ = _generar_melodia_tension_relajacion(*args_comunes)
        melodia_final.extend(melodia_generada)
    elif tecnica_a_usar == "transformaciones_motivicas":
        melodia_generada, _ = _generar_melodia_transformaciones_motivicas(*args_comunes)
        melodia_final.extend(melodia_generada)
    else:
        melodia_generada, _ = _generar_melodia_default_segmento(*args_comunes)
        melodia_final.extend(melodia_generada)
        
    return melodia_final


if __name__ == '__main__':
    acordes_test = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
    ritmo_test = [2.0, 2.0, 1.0, 3.0]
    raiz_test = "C"
    modo_test = "major"

    print(f"\n--- Prueba de generación de melodía (Técnica Aleatoria) ---")
    for i in range(5):
        print(f"\nIntento de Melodía #{i+1}")
        melodia_resultado = generar_melodia_sobre_acordes(
            acordes_test, ritmo_test, raiz_test, modo_test,
            bpm=random.randint(70,150), # BPM aleatorio para prueba
            octava_melodia_min=3, octava_melodia_max=5,
            densidad_notas=0.7
        )
        print(f"Melodía generada ({len(melodia_resultado)} eventos): {melodia_resultado}")

    print(f"\n--- Prueba de generación de melodía (Técnica Específica: esqueleto_pasos_vecinos) ---")
    melodia_esqueleto = generar_melodia_sobre_acordes(
        acordes_test, ritmo_test, raiz_test, modo_test,
        bpm=90,
        tecnica_seleccionada_externa="esqueleto_pasos_vecinos"
    )
    print(f"Melodía (Esqueleto): {melodia_esqueleto}")

    print(f"\n--- Prueba de generación de melodía (Técnica Específica: default) ---")
    melodia_default = generar_melodia_sobre_acordes(
        acordes_test, ritmo_test, raiz_test, modo_test,
        bpm=130,
        tecnica_seleccionada_externa="default"
    )
    print(f"Melodía (Default): {melodia_default}")

