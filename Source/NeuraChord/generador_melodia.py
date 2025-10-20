# generador_melodia.py
import random
from music21 import note, pitch, scale, harmony, stream, interval, key, chord as m21_chord


class ParametrosMelodicos:
    def __init__(
        self,
        bpm=120,
        densidad_notas=0.65,  # Probabilidad de que una subdivisión de la cuadrícula tenga una nota vs silencio
        octava_melodia_min=4,  # Octava MIDI más grave para la melodía (ej. C4 = 4)
        octava_melodia_max=5,  # Octava MIDI más aguda
        aplicar_repeticion_estructural=True,  # Para técnicas como pregunta-respuesta o si la progresión se repite
        probabilidad_arpegio=0.15,  # Usado por técnica default/híbrida
        probabilidad_contorno=0.25,  # Usado por técnica default/híbrida
        melodia_grid_unit_ql=0.25,  # Cuadrícula rítmica base (0.25 = semicorchea)
        melodia_min_note_multiples=1,  # Mínima duración = grid * min_multiples (ej. 1*0.25 = semicorchea)
        melodia_max_note_multiples=8,  # Máxima duración = grid * max_multiples (ej. 8*0.25 = negra)
        max_notas_cortas_consecutivas=2,  # Máx. notas de duración mínima seguidas
        priorizar_acentos_en_beats=True,  # Intentar poner notas del acorde en tiempos fuertes
        pulsos_por_compas=4,  # Para la lógica de acentos (ej. 4 para 4/4)
        prob_preferir_paso_conjunto=0.75,  # Probabilidad de moverse por grado conjunto vs salto
        max_semitonos_salto=7,  # Límite de salto en semitonos (una 5ta justa)
        max_consecutive_same_duration_notes=3,  # Máx. notas seguidas con la misma duración
        max_consecutive_same_pitch_eighth_notes=2,  # Máx. corcheas seguidas con la misma altura
        eighth_note_ql_ref=0.5,  # Duración de referencia para una corchea
        resolver_tensiones_diatonicas=True,  # Intentar resolver notas fuera del acorde
        min_notas_contorno=3,  # Para la técnica de contorno
        max_notas_contorno=5,  # Para la técnica de contorno
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


LISTA_TECNICAS_MELODICAS = [
    "default",
    "esqueleto_pasos_vecinos",
    "guia_terceras_septimas",
    "contornos_clasicos_variados",
    "pregunta_respuesta",
    "secuencias_motivo",
    "arpegio_hibrido_mejorado",
    "intervalos_3_1_relleno",
    "envoltura_ritmica_fija",
    "envoltura_melodica_fija_ritmo_libre",
    "tension_relajacion_target",
    "transformaciones_motivicas",
]


def _pitch_from_midi(midi_val):
    p = pitch.Pitch()
    p.midi = int(round(midi_val))
    return p


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


def _ajustar_a_escala_mas_cercana(p_obj, notas_escala_disponibles_obj):
    if not p_obj or not notas_escala_disponibles_obj:
        return p_obj
    objetivo = p_obj.midi
    candidato = min(notas_escala_disponibles_obj, key=lambda cand: abs(cand.midi - objetivo))
    return pitch.Pitch(candidato.nameWithOctave)


def _forzar_a_nota_de_acorde(p_obj, notas_acorde_en_rango):
    if not p_obj or not notas_acorde_en_rango:
        return p_obj
    objetivo = p_obj.midi
    candidato = min(notas_acorde_en_rango, key=lambda cand: abs(cand.midi - objetivo))
    return pitch.Pitch(candidato.nameWithOctave)


def _es_tiempo_fuerte(offset_units, params: ParametrosMelodicos):
    if params.melodia_grid_unit_ql <= 0:
        return False
    posicion_en_compas = (offset_units * params.melodia_grid_unit_ql) % params.pulsos_por_compas
    beats_fuertes = {0.0}
    if params.pulsos_por_compas == 4:
        beats_fuertes.add(2.0)
    elif params.pulsos_por_compas == 3:
        beats_fuertes.update({1.0, 2.0})
    tolerancia = params.melodia_grid_unit_ql * 0.5
    return any(abs(posicion_en_compas - beat) <= tolerancia for beat in beats_fuertes)


def _crear_patron_melodico(params: ParametrosMelodicos):
    largo_motivo = random.randint(3, 5)
    posibles_intervalos = [-7, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 7]
    pesos_intervalos = [1, 1, 2, 3, 4, 5, 5, 4, 3, 2, 1, 1]
    motivo_intervalos = random.choices(posibles_intervalos, weights=pesos_intervalos, k=largo_motivo)
    min_mult = max(1, params.melodia_min_note_multiples)
    max_mult = max(min_mult, params.melodia_max_note_multiples)
    opciones_duracion = list(range(min_mult, max_mult + 1))
    motivo_duraciones = [random.choice(opciones_duracion) for _ in range(largo_motivo)]
    if all(duracion == min_mult for duracion in motivo_duraciones) and max_mult > min_mult:
        idx = random.randrange(len(motivo_duraciones))
        motivo_duraciones[idx] = min(max_mult, min_mult * 2)
    return motivo_intervalos, motivo_duraciones


def _elegir_duracion_unidades(
    remaining_units,
    params: ParametrosMelodicos,
    ultima_duracion_units,
    consecutivas_misma_duracion,
    consecutivas_cortas,
    preferencia=None,
):
    min_mult = max(1, params.melodia_min_note_multiples)
    max_mult = max(min_mult, params.melodia_max_note_multiples)
    candidatas = []
    for unidades in range(min_mult, max_mult + 1):
        if unidades > remaining_units:
            continue
        if unidades == min_mult and consecutivas_cortas >= params.max_notas_cortas_consecutivas:
            continue
        if (
            ultima_duracion_units is not None
            and unidades == ultima_duracion_units
            and consecutivas_misma_duracion >= params.max_consecutive_same_duration_notes
        ):
            continue
        candidatas.append(unidades)
    if not candidatas:
        candidatas = [remaining_units]
    if preferencia in candidatas:
        pesos = []
        for unidades in candidatas:
            if unidades == preferencia:
                pesos.append(4)
            elif abs(unidades - preferencia) == 1:
                pesos.append(2)
            else:
                pesos.append(1)
        return random.choices(candidatas, weights=pesos, k=1)[0]
    return random.choice(candidatas)


def _buscar_vecino_suave(ultima_nota, notas_escala, notas_acorde, params: ParametrosMelodicos, preferir_acorde=False):
    if not notas_escala:
        return None
    if ultima_nota is None:
        if preferir_acorde and notas_acorde:
            return pitch.Pitch(random.choice(notas_acorde).nameWithOctave)
        return pitch.Pitch(random.choice(notas_escala).nameWithOctave)
    vecinos = []
    for cand in notas_escala:
        distancia = abs(cand.midi - ultima_nota.midi)
        if 0 < distancia <= 2:
            vecinos.append(cand)
    if preferir_acorde and notas_acorde:
        vecinos_acorde = [cand for cand in vecinos if any(abs(cand.midi - nota_acorde.midi) < 0.5 for nota_acorde in notas_acorde)]
        if vecinos_acorde:
            vecinos = vecinos_acorde
    if vecinos:
        return pitch.Pitch(random.choice(vecinos).nameWithOctave)
    return None


def _seleccionar_pitch_para_evento(
    ultima_nota,
    notas_acorde,
    notas_escala,
    params: ParametrosMelodicos,
    intervalo_hint,
    es_tiempo_fuerte,
):
    candidato = None
    if ultima_nota and random.random() < params.prob_preferir_paso_conjunto:
        candidato = _buscar_vecino_suave(ultima_nota, notas_escala, notas_acorde, params, preferir_acorde=es_tiempo_fuerte)
    if candidato is None and ultima_nota:
        objetivo_midi = ultima_nota.midi + intervalo_hint
        max_salto = params.max_semitonos_salto
        if abs(intervalo_hint) > max_salto:
            objetivo_midi = ultima_nota.midi + max_salto * (1 if intervalo_hint > 0 else -1)
        candidato = _pitch_from_midi(objetivo_midi)
    if candidato is None:
        if notas_acorde:
            candidato = pitch.Pitch(random.choice(notas_acorde).nameWithOctave)
        elif notas_escala:
            candidato = pitch.Pitch(random.choice(notas_escala).nameWithOctave)
    candidato = _clamp_pitch_to_range(candidato, params)
    candidato = _ajustar_a_escala_mas_cercana(candidato, notas_escala)
    if es_tiempo_fuerte:
        candidato = _forzar_a_nota_de_acorde(candidato, notas_acorde)
    return candidato


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


def generar_arpegio_simple(acorde_data, duracion_total_acorde, octava_min, octava_max, melodia_grid_unit_ql):
    arpegio_eventos = []
    ultimo_pitch_arpegio = None
    notas_del_acorde_obj_sin_octava = notas_del_acorde_music21(acorde_data)
    max_notas_para_arpegio_simple = 3
    notas_arpegio_en_rango = []
    if notas_del_acorde_obj_sin_octava:
        pitches_base_ordenados = sorted({p.name for p in notas_del_acorde_obj_sin_octava})
        for nota_nombre_base in pitches_base_ordenados:
            for octava_candidata in range(octava_min, octava_max + 1):
                try:
                    pitch_temporal = pitch.Pitch(f"{nota_nombre_base}{octava_candidata}")
                    if pitch_temporal not in notas_arpegio_en_rango:
                        notas_arpegio_en_rango.append(pitch_temporal)
                    break
                except Exception:  # noqa: BLE001
                    continue
        notas_arpegio_en_rango = sorted(set(notas_arpegio_en_rango), key=lambda p: p.ps)
        if len(notas_arpegio_en_rango) > max_notas_para_arpegio_simple:
            notas_arpegio_en_rango = notas_arpegio_en_rango[:max_notas_para_arpegio_simple]
    if not notas_arpegio_en_rango:
        if duracion_total_acorde > 0:
            arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
        return arpegio_eventos, None
    num_notas_arpegio = len(notas_arpegio_en_rango)
    total_grid_units_en_acorde = int(duracion_total_acorde / melodia_grid_unit_ql) if melodia_grid_unit_ql > 0 else 0
    if total_grid_units_en_acorde < num_notas_arpegio:
        if duracion_total_acorde > 0:
            arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
        return arpegio_eventos, None
    grid_units_por_nota = total_grid_units_en_acorde // num_notas_arpegio if num_notas_arpegio > 0 else 0
    grid_units_restantes = total_grid_units_en_acorde % num_notas_arpegio if num_notas_arpegio > 0 else 0
    if grid_units_por_nota == 0:
        if duracion_total_acorde > 0:
            arpegio_eventos.append(("0", str(round(duracion_total_acorde, 3))))
        return arpegio_eventos, None
    dur_asignada_total = 0.0
    for p_obj in notas_arpegio_en_rango:
        dur_actual_nota_units = grid_units_por_nota
        if grid_units_restantes > 0:
            dur_actual_nota_units += 1
            grid_units_restantes -= 1
        dur_actual_nota_ql = round(dur_actual_nota_units * melodia_grid_unit_ql, 3)
        if dur_actual_nota_ql <= 0:
            continue
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


def generar_contorno_arco(
    nota_inicio_obj,
    duracion_total_contorno,
    num_pasos_contorno,
    escala_obj,
    octava_min,
    octava_max,
    max_salto_semitonos_contorno=4,
    melodia_grid_unit_ql=0.25,
):
    eventos_contorno = []
    if not nota_inicio_obj or num_pasos_contorno < 2:
        if duracion_total_contorno > 0:
            eventos_contorno.append(("0", str(duracion_total_contorno)))
        return eventos_contorno, nota_inicio_obj
    total_grid_units_en_contorno = int(duracion_total_contorno / melodia_grid_unit_ql) if melodia_grid_unit_ql > 0 else 0
    if total_grid_units_en_contorno < num_pasos_contorno:
        if duracion_total_contorno > 0:
            eventos_contorno.append(("0", str(duracion_total_contorno)))
        return eventos_contorno, nota_inicio_obj
    grid_units_por_paso = total_grid_units_en_contorno // num_pasos_contorno if num_pasos_contorno > 0 else 0
    grid_units_restantes_contorno = total_grid_units_en_contorno % num_pasos_contorno if num_pasos_contorno > 0 else 0
    if grid_units_por_paso == 0:
        if duracion_total_contorno > 0:
            eventos_contorno.append(("0", str(duracion_total_contorno)))
        return eventos_contorno, nota_inicio_obj
    punto_medio_pasos = num_pasos_contorno // 2
    nota_actual_obj = nota_inicio_obj
    if nota_actual_obj.octave < octava_min:
        nota_actual_obj.octave = octava_min
    if nota_actual_obj.octave > octava_max:
        nota_actual_obj.octave = octava_max
    tiempo_asignado_contorno = 0.0
    notas_generadas_contorno = [nota_actual_obj]
    ultimo_pitch_contorno = nota_inicio_obj
    for _ in range(1, punto_medio_pasos + (num_pasos_contorno % 2)):
        notas_candidatas_mov = []
        nota_temporal_para_busqueda = nota_actual_obj
        for step_sz in range(1, max_salto_semitonos_contorno + 2):
            try:
                nota_siguiente_obj = escala_obj.nextPitch(
                    nota_temporal_para_busqueda,
                    stepSize=1,
                    direction=scale.Direction.ASCENDING,
                )
                if octava_min <= nota_siguiente_obj.octave <= octava_max:
                    if abs(interval.Interval(nota_actual_obj, nota_siguiente_obj).semitones) <= max_salto_semitonos_contorno:
                        notas_candidatas_mov.append(nota_siguiente_obj)
                nota_temporal_para_busqueda = nota_siguiente_obj
                if notas_candidatas_mov:
                    break
            except Exception:  # noqa: BLE001
                break
        if notas_candidatas_mov:
            nota_actual_obj = random.choice(notas_candidatas_mov)
        notas_generadas_contorno.append(nota_actual_obj)
    for _ in range(punto_medio_pasos + (num_pasos_contorno % 2), num_pasos_contorno):
        notas_candidatas_mov = []
        nota_temporal_para_busqueda = nota_actual_obj
        for step_sz in range(1, max_salto_semitonos_contorno + 2):
            try:
                nota_siguiente_obj = escala_obj.previousPitch(
                    nota_temporal_para_busqueda,
                    stepSize=1,
                    direction=scale.Direction.DESCENDING,
                )
                if octava_min <= nota_siguiente_obj.octave <= octava_max:
                    if abs(interval.Interval(nota_actual_obj, nota_siguiente_obj).semitones) <= max_salto_semitonos_contorno:
                        notas_candidatas_mov.append(nota_siguiente_obj)
                nota_temporal_para_busqueda = nota_siguiente_obj
                if notas_candidatas_mov:
                    break
            except Exception:  # noqa: BLE001
                break
        if notas_candidatas_mov:
            nota_actual_obj = random.choice(notas_candidatas_mov)
        notas_generadas_contorno.append(nota_actual_obj)
    if len(notas_generadas_contorno) != num_pasos_contorno:
        notas_generadas_contorno = notas_generadas_contorno[:num_pasos_contorno]
        while len(notas_generadas_contorno) < num_pasos_contorno:
            notas_generadas_contorno.append(notas_generadas_contorno[-1] if notas_generadas_contorno else nota_inicio_obj)
    for p_obj_cont in notas_generadas_contorno:
        dur_actual_nota_units = grid_units_por_paso
        if grid_units_restantes_contorno > 0:
            dur_actual_nota_units += 1
            grid_units_restantes_contorno -= 1
        dur_actual_nota_ql = round(dur_actual_nota_units * melodia_grid_unit_ql, 3)
        if dur_actual_nota_ql <= 0:
            continue
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
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params: ParametrosMelodicos,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(f"DEBUG (Melodia): Usando técnica 'default' (algorítmica general). BPM interno: {params.bpm}")
    if not segmento_acordes or not segmento_ritmos:
        return [], ultima_nota_global_pitch_obj

    motivo_intervalos, motivo_duraciones = _crear_patron_melodico(params)
    posicion_motivo = 0
    melodia_generada = []
    ultima_nota = ultima_nota_global_pitch_obj

    consecutivas_cortas = 0
    consecutivas_misma_duracion = 0
    ultima_duracion_units = None
    consecutivas_misma_altura_corchea = 0

    grid = params.melodia_grid_unit_ql
    tol_corchea = grid * 0.25
    min_mult = max(1, params.melodia_min_note_multiples)

    for idx, acorde_data in enumerate(segmento_acordes):
        duracion_acorde = float(segmento_ritmos[idx % len(segmento_ritmos)])
        if duracion_acorde <= 0:
            continue

        notas_acorde = _expandir_notas_acorde_en_rango(acorde_data, params)
        total_unidades = max(1, int(round(duracion_acorde / grid))) if grid > 0 else 1
        unidades_usadas = 0
        eventos_acorde = []
        se_coloco_nota = False

        while unidades_usadas < total_unidades:
            remaining_units = total_unidades - unidades_usadas
            preferencia_duracion = motivo_duraciones[posicion_motivo % len(motivo_duraciones)]
            dur_units = _elegir_duracion_unidades(
                remaining_units,
                params,
                ultima_duracion_units,
                consecutivas_misma_duracion,
                consecutivas_cortas,
                preferencia=preferencia_duracion,
            )
            if dur_units <= 0:
                dur_units = min_mult
            if dur_units > remaining_units:
                dur_units = remaining_units

            dur_ql = round(dur_units * grid, 3)
            es_fuerte = _es_tiempo_fuerte(unidades_usadas, params)
            intervalo_hint = motivo_intervalos[posicion_motivo % len(motivo_intervalos)]
            if random.random() < 0.2:
                intervalo_hint = random.choice(motivo_intervalos)

            colocar_nota = (random.random() < params.densidad_notas) or es_fuerte or not se_coloco_nota
            evento_agregado = False

            if colocar_nota and notas_escala_disponibles_obj:
                candidato_pitch = _seleccionar_pitch_para_evento(
                    ultima_nota,
                    notas_acorde,
                    notas_escala_disponibles_obj,
                    params,
                    intervalo_hint,
                    es_fuerte,
                )

                if candidato_pitch and ultima_nota:
                    salto = candidato_pitch.midi - ultima_nota.midi
                    if abs(salto) > params.max_semitonos_salto:
                        direccion = 1 if salto > 0 else -1
                        candidato_pitch = _pitch_from_midi(ultima_nota.midi + direccion * params.max_semitonos_salto)
                        candidato_pitch = _ajustar_a_escala_mas_cercana(candidato_pitch, notas_escala_disponibles_obj)
                        if es_fuerte:
                            candidato_pitch = _forzar_a_nota_de_acorde(candidato_pitch, notas_acorde)

                if candidato_pitch and ultima_nota and candidato_pitch.midi == ultima_nota.midi:
                    es_corchea = abs(dur_ql - params.eighth_note_ql_ref) <= tol_corchea
                    if es_corchea:
                        consecutivas_misma_altura_corchea += 1
                    else:
                        consecutivas_misma_altura_corchea = 0
                    if es_corchea and consecutivas_misma_altura_corchea > params.max_consecutive_same_pitch_eighth_notes:
                        ajuste_vecino = _buscar_vecino_suave(
                            ultima_nota,
                            notas_escala_disponibles_obj,
                            notas_acorde,
                            params,
                            preferir_acorde=es_fuerte,
                        )
                        if ajuste_vecino:
                            candidato_pitch = ajuste_vecino
                            consecutivas_misma_altura_corchea = 0
                else:
                    consecutivas_misma_altura_corchea = 0

                if candidato_pitch:
                    eventos_acorde = _agregar_evento(eventos_acorde, candidato_pitch.nameWithOctave, dur_ql)
                    ultima_nota = pitch.Pitch(candidato_pitch.nameWithOctave)
                    evento_agregado = True
                    se_coloco_nota = True
                else:
                    colocar_nota = False

            if not evento_agregado:
                eventos_acorde = _agregar_evento(eventos_acorde, "0", dur_ql)
                if ultima_nota is not None and colocar_nota:
                    ultima_nota = None
                consecutivas_misma_altura_corchea = 0

            if dur_units == min_mult:
                consecutivas_cortas += 1
            else:
                consecutivas_cortas = 0

            if ultima_duracion_units is not None and dur_units == ultima_duracion_units:
                consecutivas_misma_duracion += 1
            else:
                consecutivas_misma_duracion = 0
            ultima_duracion_units = dur_units

            unidades_usadas += dur_units
            posicion_motivo += 1

        dur_generada = sum(float(ev[1]) for ev in eventos_acorde)
        diferencia = round(duracion_acorde - dur_generada, 3)
        if abs(diferencia) > 0.001 and eventos_acorde:
            ult_pitch, ult_dur = eventos_acorde[-1]
            nueva_dur = max(0.0, float(ult_dur) + diferencia)
            if nueva_dur <= 0 and len(eventos_acorde) > 1:
                eventos_acorde.pop()
            else:
                eventos_acorde[-1] = (ult_pitch, str(round(nueva_dur, 3)))

        melodia_generada.extend(eventos_acorde)

    return melodia_generada, ultima_nota


def _generar_melodia_esqueleto_pasos(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params: ParametrosMelodicos,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(f"DEBUG (Melodia): Usando técnica 'esqueleto_pasos_vecinos'. BPM interno: {params.bpm}")
    melodia_final_tec1 = []
    ultima_nota_tecnica = ultima_nota_global_pitch_obj
    tiempo_total_acumulado_global = 0.0

    for i, acorde_actual_data in enumerate(segmento_acordes):
        duracion_acorde_actual_ql = float(segmento_ritmos[i % len(segmento_ritmos)])
        notas_del_acorde_actual_obj_base = notas_del_acorde_music21(acorde_actual_data)

        notas_acorde_en_rango_actual = []
        if notas_del_acorde_actual_obj_base:
            for p_base in notas_del_acorde_actual_obj_base:
                for oct_cand in range(params.octava_melodia_min, params.octava_melodia_max + 1):
                    try:
                        p_temp = pitch.Pitch(p_base.name)
                        p_temp.octave = oct_cand
                        if p_temp not in notas_acorde_en_rango_actual:
                            notas_acorde_en_rango_actual.append(p_temp)
                    except Exception:  # noqa: BLE001
                        continue
            notas_acorde_en_rango_actual = sorted(set(notas_acorde_en_rango_actual), key=lambda p: p.ps)

        if not notas_acorde_en_rango_actual:
            if notas_escala_disponibles_obj:
                notas_acorde_en_rango_actual = [
                    p for p in notas_escala_disponibles_obj if escala_actual.getScaleDegreeFromPitch(p) == 1
                ]
                if not notas_acorde_en_rango_actual:
                    notas_acorde_en_rango_actual = [random.choice(notas_escala_disponibles_obj)]
            else:
                notas_acorde_en_rango_actual = [pitch.Pitch(f"{raiz_tonalidad_segmento}{params.octava_melodia_min}")]

        tiempo_restante_en_acorde_ql = duracion_acorde_actual_ql
        tiempo_transcurrido_en_acorde_ql = 0.0

        while tiempo_restante_en_acorde_ql >= params.melodia_grid_unit_ql - 0.001:
            offset_absoluto_beat_actual = tiempo_total_acumulado_global + tiempo_transcurrido_en_acorde_ql
            offset_relativo_compas_actual = offset_absoluto_beat_actual % params.pulsos_por_compas

            es_beat_fuerte_actual = False
            beats_fuertes_definidos = [0.0]
            if params.pulsos_por_compas == 4:
                beats_fuertes_definidos.append(2.0)
            elif params.pulsos_por_compas == 3:
                beats_fuertes_definidos.extend([1.0, 2.0])

            for beat_fuerte in beats_fuertes_definidos:
                if abs(offset_relativo_compas_actual - beat_fuerte) < params.melodia_grid_unit_ql / 2.0:
                    es_beat_fuerte_actual = True
                    break

            nota_a_colocar_obj = None
            dur_nota_actual_ql = params.melodia_grid_unit_ql

            if es_beat_fuerte_actual and notas_acorde_en_rango_actual:
                if isinstance(acorde_actual_data, str) and acorde_actual_data not in ["0", "N/A"]:
                    try:
                        cs = harmony.ChordSymbol(acorde_actual_data)
                        grados_deseados = [
                            cs.getChordStep(1),
                            cs.getChordStep(3),
                            cs.getChordStep(5),
                            cs.getChordStep(7),
                        ]
                        grados_validos_en_rango = [
                            nota
                            for nota in grados_deseados
                            if nota and params.octava_melodia_min <= nota.octave <= params.octava_melodia_max
                        ]
                        if grados_validos_en_rango:
                            nota_a_colocar_obj = random.choice(grados_validos_en_rango)
                    except Exception:  # noqa: BLE001
                        pass
                if not nota_a_colocar_obj:
                    nota_a_colocar_obj = random.choice(notas_acorde_en_rango_actual)

                if random.random() < 0.6 and tiempo_restante_en_acorde_ql >= params.melodia_grid_unit_ql * 2:
                    dur_nota_actual_ql = params.melodia_grid_unit_ql * 2
                elif tiempo_restante_en_acorde_ql >= params.melodia_grid_unit_ql * 4 and random.random() < 0.3:
                    dur_nota_actual_ql = params.melodia_grid_unit_ql * 4
            else:
                if ultima_nota_tecnica and notas_escala_disponibles_obj:
                    candidatas_paso_vecino = []
                    for p_escala in notas_escala_disponibles_obj:
                        try:
                            semitonos_dist = abs(interval.Interval(ultima_nota_tecnica, p_escala).semitones)
                            if 0 < semitonos_dist <= 2:
                                candidatas_paso_vecino.append(p_escala)
                        except Exception:  # noqa: BLE001
                            continue

                    if candidatas_paso_vecino:
                        nota_a_colocar_obj = random.choice(candidatas_paso_vecino)
                    elif notas_acorde_en_rango_actual:
                        nota_a_colocar_obj = random.choice(notas_acorde_en_rango_actual)
                    else:
                        nota_a_colocar_obj = ultima_nota_tecnica
                elif notas_acorde_en_rango_actual:
                    nota_a_colocar_obj = random.choice(notas_acorde_en_rango_actual)
                elif notas_escala_disponibles_obj:
                    nota_a_colocar_obj = random.choice(notas_escala_disponibles_obj)

            if nota_a_colocar_obj and random.random() < params.densidad_notas:
                dur_nota_actual_ql = min(dur_nota_actual_ql, tiempo_restante_en_acorde_ql)
                dur_nota_actual_ql = round(
                    int(dur_nota_actual_ql / params.melodia_grid_unit_ql) * params.melodia_grid_unit_ql,
                    3,
                )
                if dur_nota_actual_ql < params.melodia_grid_unit_ql - 0.001:
                    break

                melodia_final_tec1.append((nota_a_colocar_obj.nameWithOctave, str(dur_nota_actual_ql)))
                ultima_nota_tecnica = nota_a_colocar_obj
                tiempo_transcurrido_en_acorde_ql += dur_nota_actual_ql
                tiempo_restante_en_acorde_ql -= dur_nota_actual_ql
            else:
                dur_silencio_ql = params.melodia_grid_unit_ql
                dur_silencio_ql = min(dur_silencio_ql, tiempo_restante_en_acorde_ql)
                dur_silencio_ql = round(
                    int(dur_silencio_ql / params.melodia_grid_unit_ql) * params.melodia_grid_unit_ql,
                    3,
                )
                if dur_silencio_ql < params.melodia_grid_unit_ql - 0.001:
                    break

                melodia_final_tec1.append(("0", str(dur_silencio_ql)))
                tiempo_transcurrido_en_acorde_ql += dur_silencio_ql
                tiempo_restante_en_acorde_ql -= dur_silencio_ql

            tiempo_restante_en_acorde_ql = round(tiempo_restante_en_acorde_ql, 3)
        tiempo_total_acumulado_global += duracion_acorde_actual_ql

    if not melodia_final_tec1:
        total_dur_prog = sum(float(r) for r in segmento_ritmos)
        if total_dur_prog > 0:
            melodia_final_tec1.append(("0", str(total_dur_prog)))
    return melodia_final_tec1, ultima_nota_tecnica


# --- Stubs para las demás técnicas ---
def _generar_melodia_guia_tonos(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'guia_terceras_septimas' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_contornos_clasicos(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'contornos_clasicos_variados' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_pregunta_respuesta(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'pregunta_respuesta' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_secuencias_motivo(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'secuencias_motivo' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_arpegio_hibrido(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'arpegio_hibrido_mejorado' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_intervalos_3_1(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'intervalos_3_1_relleno' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_envoltura_ritmica_fija(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'envoltura_ritmica_fija' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_envoltura_melodica_fija(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'envoltura_melodica_fija_ritmo_libre' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_tension_relajacion(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'tension_relajacion_target' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


def _generar_melodia_transformaciones_motivicas(
    segmento_acordes,
    segmento_ritmos,
    escala_actual,
    notas_escala_disponibles_obj,
    params,
    ultima_nota_global_pitch_obj,
    raiz_tonalidad_segmento,
):
    print(
        f"DEBUG (Melodia): Técnica 'transformaciones_motivicas' NO IMPLEMENTADA. Usando default. BPM interno: {params.bpm}"
    )
    return _generar_melodia_default_segmento(
        segmento_acordes,
        segmento_ritmos,
        escala_actual,
        notas_escala_disponibles_obj,
        params,
        ultima_nota_global_pitch_obj,
        raiz_tonalidad_segmento,
    )


# --- Función Principal de Generación de Melodía ---
def generar_melodia_sobre_acordes(
    acordes_progresion,
    ritmo_acordes,
    raiz_tonalidad,
    modo_tonalidad,
    tecnica_seleccionada_externa=None,
    bpm=120,
    densidad_notas=0.65,
    octava_melodia_min=4,
    octava_melodia_max=5,
    prob_preferir_paso_conjunto=0.75,
    max_semitonos_salto=7,
):
    melodia_final = []
    if not acordes_progresion or not ritmo_acordes:
        return melodia_final

    params_mel = ParametrosMelodicos(
        bpm=bpm,
        densidad_notas=densidad_notas,
        octava_melodia_min=octava_melodia_min,
        octava_melodia_max=octava_melodia_max,
        prob_preferir_paso_conjunto=prob_preferir_paso_conjunto,
        max_semitonos_salto=max_semitonos_salto,
    )
    print(f"INFO (Generador Melodia): Iniciando generación de melodía con BPM: {params_mel.bpm}")

    escala_actual = obtener_escala_actual(raiz_tonalidad, modo_tonalidad)
    notas_escala_disponibles_obj = []
    for p_escala_base in escala_actual.pitches:
        if isinstance(p_escala_base, pitch.Pitch):
            for oct_num in range(params_mel.octava_melodia_min, params_mel.octava_melodia_max + 1):
                try:
                    p_temp = pitch.Pitch(p_escala_base.name)
                    p_temp.octave = oct_num
                    if p_temp not in notas_escala_disponibles_obj:
                        notas_escala_disponibles_obj.append(p_temp)
                except Exception:  # noqa: BLE001
                    continue
    notas_escala_disponibles_obj = sorted(set(notas_escala_disponibles_obj), key=lambda p: p.ps)

    if not notas_escala_disponibles_obj:
        print("ADVERTENCIA (generador_melodia): No hay notas de escala disponibles.")
        total_dur_silencio = sum(float(duracion) for duracion in ritmo_acordes) if ritmo_acordes else 0
        if total_dur_silencio > 0:
            melodia_final.append(("0", str(total_dur_silencio)))
        return melodia_final

    tecnica_a_usar = tecnica_seleccionada_externa
    if tecnica_a_usar is None or tecnica_a_usar not in LISTA_TECNICAS_MELODICAS:
        pesos = [5 if tecnica == "default" else 3 if tecnica == "esqueleto_pasos_vecinos" else 1 for tecnica in LISTA_TECNICAS_MELODICAS]
        tecnica_a_usar = random.choices(LISTA_TECNICAS_MELODICAS, weights=pesos, k=1)[0]

    print(f"INFO (Melodia): Técnica seleccionada: {tecnica_a_usar}")

    args_comunes = (
        acordes_progresion,
        ritmo_acordes,
        escala_actual,
        notas_escala_disponibles_obj,
        params_mel,
        None,
        raiz_tonalidad,
    )

    if tecnica_a_usar == "default":
        if (
            params_mel.aplicar_repeticion_estructural
            and len(acordes_progresion) >= 2
            and len(acordes_progresion) % 2 == 0
        ):
            punto_medio = len(acordes_progresion) // 2
            melodia_seg1, ult_nota1 = _generar_melodia_default_segmento(
                acordes_progresion[:punto_medio],
                ritmo_acordes[:punto_medio],
                *args_comunes[2:],
            )
            melodia_final.extend(melodia_seg1)
            if (
                acordes_progresion[punto_medio:] == acordes_progresion[:punto_medio]
                and ritmo_acordes[punto_medio:] == ritmo_acordes[:punto_medio]
            ):
                melodia_final.extend(melodia_seg1)
            else:
                args_seg2 = (
                    acordes_progresion[punto_medio:],
                    ritmo_acordes[punto_medio:],
                    escala_actual,
                    notas_escala_disponibles_obj,
                    params_mel,
                    ult_nota1,
                    raiz_tonalidad,
                )
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


if __name__ == "__main__":
    acordes_test = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
    ritmo_test = [2.0, 2.0, 1.0, 3.0]
    raiz_test = "C"
    modo_test = "major"

    print("\n--- Prueba de generación de melodía (Técnica Aleatoria) ---")
    for i in range(5):
        print(f"\nIntento de Melodía #{i + 1}")
        melodia_resultado = generar_melodia_sobre_acordes(
            acordes_test,
            ritmo_test,
            raiz_test,
            modo_test,
            bpm=random.randint(70, 150),
            octava_melodia_min=3,
            octava_melodia_max=5,
            densidad_notas=0.7,
        )
        print(f"Melodía generada ({len(melodia_resultado)} eventos): {melodia_resultado}")

    print("\n--- Prueba de generación de melodía (Técnica Específica: esqueleto_pasos_vecinos) ---")
    melodia_esqueleto = generar_melodia_sobre_acordes(
        acordes_test,
        ritmo_test,
        raiz_test,
        modo_test,
        bpm=90,
        tecnica_seleccionada_externa="esqueleto_pasos_vecinos",
    )
    print(f"Melodía (Esqueleto): {melodia_esqueleto}")

    print("\n--- Prueba de generación de melodía (Técnica Específica: default) ---")
    melodia_default = generar_melodia_sobre_acordes(
        acordes_test,
        ritmo_test,
        raiz_test,
        modo_test,
        bpm=130,
        tecnica_seleccionada_externa="default",
    )
    print(f"Melodía (Default): {melodia_default}")