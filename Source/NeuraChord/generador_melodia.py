# generador_melodia.py
import random
import re
from dataclasses import dataclass
from typing import List, Optional, Sequence
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
    "rnb": {
        "tecnicas_preferidas": [("motivo", 0.9), ("arpegio", 0.1)],
        "prob_variacion_A": 0.7,
        "estructura_frase": "pregunta_respuesta",
        "densidad_notas": 0.6,
        # Ritmo rnb: Sincopado, swing, notas largas + rápidas
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

ALLOWED_DURATION_UNITS = [8, 4, 2, 1]


@dataclass
class ChordRuleContext:
    sorted_pitches: List[pitch.Pitch]
    triad_indices: List[int]
    triad_pitch_classes: List[str]
    duration_units: int
    start_units: int
    original_duration: float
    chord_source: object


@dataclass
class MelodyEvent:
    pitch_name: str
    duration_units: int
    velocity: int
    segment_index: int
    index_in_chord: int
    beat_index: int


@dataclass
class MotifEntry:
    index_in_sorted: int
    duration_units: int
    is_strong: bool


@dataclass
class MelodyGenerationState:
    last_index: Optional[int] = None
    last_pitch_name: Optional[str] = None
    last_segment_index: Optional[int] = None
    consecutive_units_same_pitch: int = 0
    pending_resolution: Optional[int] = None
    global_min: Optional[float] = None
    global_max: Optional[float] = None


class _DurationDistribution:
    """Tracks rhythmic distribution to stay close to the recommended ratios."""

    def __init__(self):
        self.allowed = list(ALLOWED_DURATION_UNITS)
        self.targets = {8: 0.10, 4: 0.40, 2: 0.40, 1: 0.10}
        self.counts = {u: 0 for u in self.allowed}

    def choose_duration(self, remaining_units: int, units_to_bar_end: int) -> int:
        candidates = [u for u in self.allowed if u <= remaining_units and u <= units_to_bar_end]
        if not candidates:
            return max(1, min(self.allowed)) if remaining_units >= 1 else remaining_units

        total_counts = sum(self.counts.values())
        weights = []
        for value in candidates:
            target = self.targets.get(value, 0.1)
            actual_ratio = (self.counts[value] / total_counts) if total_counts > 0 else 0.0
            weight = max(0.05, target - actual_ratio + 0.05)
            if value == remaining_units:
                weight += 0.5
            if value == units_to_bar_end:
                weight += 0.3
            weights.append(weight)

        return random.choices(candidates, weights=weights, k=1)[0]

    def register(self, value: int) -> None:
        if value in self.counts:
            self.counts[value] += 1


def _velocity_for_beat(beat_index: int) -> int:
    base = 88
    if beat_index == 0:
        return min(127, base + 12)
    if beat_index == 2:
        return min(127, base + 6)
    return base


def _adjust_duration_to_allowed(units: int) -> int:
    if units <= 0:
        return 0
    for allowed in sorted(ALLOWED_DURATION_UNITS, reverse=True):
        if allowed <= units:
            return allowed
    return 1


def _find_index_by_name(
    pitches_list: Sequence[pitch.Pitch],
    target_name: str,
    *,
    reference_midi: Optional[float] = None,
    prefer_lowest: bool = True,
) -> Optional[int]:
    matching = [i for i, item in enumerate(pitches_list) if item.name == target_name]
    if not matching:
        return None
    if reference_midi is not None:
        return min(matching, key=lambda idx: abs(pitches_list[idx].midi - reference_midi))
    return matching[0] if prefer_lowest else matching[-1]


def _extract_triad_pitch_classes(acorde_data) -> List[str]:
    pitches_objs = notas_del_acorde_music21(acorde_data)
    if not pitches_objs:
        return []

    prepared_names = []
    for pitch_obj in pitches_objs:
        try:
            p = pitch.Pitch(pitch_obj.nameWithOctave)
        except Exception:
            p = pitch.Pitch(pitch_obj.name)
            p.octave = p.octave if p.octave is not None else 4
        prepared_names.append(p.nameWithOctave)

    try:
        chord_obj = m21_chord.Chord(prepared_names)
    except Exception:
        chord_obj = None

    triad_names: List[str] = []
    if chord_obj is not None:
        try:
            root_pitch = chord_obj.root()
            if root_pitch is not None:
                triad_names.append(root_pitch.name)
        except Exception:
            pass
        try:
            third_pitch = chord_obj.third
            if third_pitch is not None:
                triad_names.append(third_pitch.name)
        except Exception:
            pass
        try:
            fifth_pitch = chord_obj.fifth
            if fifth_pitch is not None:
                triad_names.append(fifth_pitch.name)
        except Exception:
            pass
        try:
            seventh_pitch = chord_obj.seventh
            if seventh_pitch is not None:
                triad_names.append(seventh_pitch.name)
        except Exception:
            pass

    if not triad_names:
        seen = set()
        for p in sorted(pitches_objs, key=lambda item: item.midi):
            base_name = p.name
            if base_name not in seen:
                triad_names.append(base_name)
                seen.add(base_name)
                if len(triad_names) >= 4:
                    break

    return triad_names


def _map_pitch_classes_to_indices(
    sorted_pitches: Sequence[pitch.Pitch],
    triad_pitch_classes: Sequence[str],
) -> List[int]:
    indices: List[int] = []
    used_names = set()
    for name in triad_pitch_classes:
        if name in used_names:
            continue
        idx = _find_index_by_name(sorted_pitches, name)
        if idx is not None:
            indices.append(idx)
            used_names.add(name)
    if not indices and sorted_pitches:
        indices = list(range(min(3, len(sorted_pitches))))
    return indices


def _build_rule_contexts(
    acordes: Sequence,
    ritmos: Sequence,
    params: ParametrosMelodicos,
) -> List[ChordRuleContext]:
    contexts: List[ChordRuleContext] = []
    grid = params.melodia_grid_unit_ql
    start_units = 0
    for idx, acorde in enumerate(acordes):
        try:
            duracion = float(ritmos[idx]) if idx < len(ritmos) else 1.0
        except (ValueError, TypeError):
            duracion = 1.0
        units = max(1, int(round(duracion / grid)))
        sorted_pitches = _expandir_notas_acorde_en_rango(acorde, params)
        if not sorted_pitches:
            return []
        triad_pitch_classes = _extract_triad_pitch_classes(acorde)
        triad_indices = _map_pitch_classes_to_indices(sorted_pitches, triad_pitch_classes)
        contexts.append(
            ChordRuleContext(
                sorted_pitches=sorted_pitches,
                triad_indices=triad_indices,
                triad_pitch_classes=list(triad_pitch_classes),
                duration_units=units,
                start_units=start_units,
                original_duration=duracion,
                chord_source=acorde,
            )
        )
        start_units += units
    return contexts


def _choose_note_index(
    base_indices: Sequence[int],
    full_indices: Sequence[int],
    state: MelodyGenerationState,
    motif_target: Optional[int],
) -> int:
    available_full = sorted(set(full_indices))
    available_base = sorted(set(base_indices)) if base_indices else available_full
    if not available_full:
        return 0

    last_idx = state.last_index
    pending = state.pending_resolution

    if last_idx is None:
        if motif_target is not None and motif_target in available_full:
            return motif_target
        if available_base:
            return available_base[len(available_base) // 2]
        return available_full[len(available_full) // 2]

    if pending is not None:
        direction = -pending
        candidates = [i for i in available_full if (i - last_idx) * direction > 0 and abs(i - last_idx) <= 2]
        if not candidates:
            candidates = [i for i in available_full if (i - last_idx) * direction > 0]
        if not candidates:
            candidates = available_full
        candidates = sorted(
            candidates,
            key=lambda i: (
                abs(i - (motif_target if motif_target is not None else last_idx + direction)),
                abs(i - last_idx),
            ),
        )
        return candidates[0]

    step_candidates = [i for i in available_base if abs(i - last_idx) <= 1]
    if not step_candidates:
        step_candidates = [i for i in available_full if abs(i - last_idx) <= 1]

    leap_candidates = [i for i in available_full if abs(i - last_idx) >= 2]

    use_leap = False
    if motif_target is not None:
        use_leap = abs(motif_target - last_idx) >= 2 and bool(leap_candidates)
    else:
        use_leap = bool(leap_candidates) and random.random() < 0.2

    candidates = leap_candidates if use_leap and leap_candidates else step_candidates
    if not candidates:
        candidates = available_full

    if motif_target is not None:
        candidates = sorted(candidates, key=lambda i: (abs(i - motif_target), abs(i - last_idx)))
    else:
        random.shuffle(candidates)
        candidates = sorted(candidates, key=lambda i: abs(i - last_idx))

    return candidates[0]


def _enforce_range_and_repetition(
    chosen_idx: int,
    available_indices: Sequence[int],
    duration_units: int,
    context: ChordRuleContext,
    state: MelodyGenerationState,
    limit_same_pitch_units: int,
) -> tuple[int, int, float, float, float]:
    ordered_candidates = [chosen_idx] + [i for i in available_indices if i != chosen_idx]
    previous_pitch = state.last_pitch_name

    for candidate in ordered_candidates:
        pitch_obj = context.sorted_pitches[candidate]
        midi_val = pitch_obj.midi
        new_min = midi_val if state.global_min is None else min(state.global_min, midi_val)
        new_max = midi_val if state.global_max is None else max(state.global_max, midi_val)
        if (new_max - new_min) > 14:
            continue

        actual_duration = duration_units
        same_note = previous_pitch == pitch_obj.nameWithOctave
        if same_note and state.consecutive_units_same_pitch + duration_units > limit_same_pitch_units:
            allowance = limit_same_pitch_units - state.consecutive_units_same_pitch
            adjusted = _adjust_duration_to_allowed(allowance)
            if adjusted <= 0:
                continue
            actual_duration = adjusted

        return candidate, actual_duration, midi_val, new_min, new_max

    fallback_pitch = context.sorted_pitches[chosen_idx]
    midi_val = fallback_pitch.midi
    new_min = midi_val if state.global_min is None else min(state.global_min, midi_val)
    new_max = midi_val if state.global_max is None else max(state.global_max, midi_val)
    actual_duration = _adjust_duration_to_allowed(duration_units)
    if actual_duration <= 0:
        actual_duration = 1
    return chosen_idx, actual_duration, midi_val, new_min, new_max


def _apply_final_resolution(events: List[MelodyEvent], contexts: Sequence[ChordRuleContext]) -> None:
    if not events or not contexts:
        return

    last_idx = None
    for idx in range(len(events) - 1, -1, -1):
        if events[idx].pitch_name != "0":
            last_idx = idx
            break
    if last_idx is None:
        return

    last_event = events[last_idx]
    context = contexts[last_event.segment_index]
    triad_names = context.triad_pitch_classes
    if not triad_names:
        return

    reference_midi = pitch.Pitch(last_event.pitch_name).midi
    base_probs = [0.6, 0.3, 0.1]
    candidates = []

    for pos, name in enumerate(triad_names[:3]):
        idx = _find_index_by_name(context.sorted_pitches, name, reference_midi=reference_midi)
        if idx is None:
            continue
        candidate_pitch = context.sorted_pitches[idx]
        weight = base_probs[pos] if pos < len(base_probs) else 0.05
        score = weight - (abs(candidate_pitch.midi - reference_midi) / 24.0)
        candidates.append((score, candidate_pitch, idx))

    if not candidates:
        return

    best_candidate = max(candidates, key=lambda item: item[0])
    last_event.pitch_name = best_candidate[1].nameWithOctave
    last_event.index_in_chord = best_candidate[2]


def _convert_events_to_output(events: List[MelodyEvent], grid: float) -> List[tuple[str, str]]:
    salida: List[tuple[str, str]] = []
    for event in events:
        dur_ql = event.duration_units * grid
        salida = _agregar_evento(salida, event.pitch_name, dur_ql)
    return salida


def _generar_melodia_con_reglas(
    contexts: Sequence[ChordRuleContext],
    params: ParametrosMelodicos,
) -> List[MelodyEvent]:
    if not contexts:
        return []

    grid = params.melodia_grid_unit_ql
    unidades_por_compas = max(1, int(round(4.0 / grid)))
    unidades_por_tiempo = max(1, int(round(1.0 / grid)))
    limite_repeticion = int(round(2.0 / grid))

    distribucion = _DurationDistribution()
    estado = MelodyGenerationState()
    eventos: List[MelodyEvent] = []
    motivo: List[MotifEntry] = []

    total_unidades = 0
    indice_compas = 0
    desplazamiento_motivo = 0
    indice_nota_en_compas = 0

    for seg_idx, contexto in enumerate(contexts):
        unidades_restantes = contexto.duration_units
        while unidades_restantes > 0:
            posicion_compas = total_unidades % unidades_por_compas
            if total_unidades > 0 and posicion_compas == 0:
                indice_compas += 1
                indice_nota_en_compas = 0
                desplazamiento_motivo = random.choice([-1, 0, 1]) if motivo else 0

            unidades_hasta_fin = unidades_por_compas - posicion_compas
            if unidades_hasta_fin <= 0:
                unidades_hasta_fin = unidades_por_compas

            duracion_units = distribucion.choose_duration(unidades_restantes, unidades_hasta_fin)
            if duracion_units <= 0:
                duracion_units = 1

            beat_index = (posicion_compas // unidades_por_tiempo) % 4
            es_fuerte = beat_index in (0, 2)

            indices_disponibles = list(range(len(contexto.sorted_pitches)))
            indices_base = contexto.triad_indices if es_fuerte and contexto.triad_indices else indices_disponibles

            motivo_activo = None
            if indice_compas > 0 and motivo and indices_disponibles:
                motivo_base = motivo[:6] if len(motivo) > 6 else motivo
                entrada = motivo_base[indice_nota_en_compas % len(motivo_base)]
                candidato = entrada.index_in_sorted + desplazamiento_motivo
                motivo_activo = max(0, min(len(indices_disponibles) - 1, candidato))

            indice_elegido = _choose_note_index(indices_base, indices_disponibles, estado, motivo_activo)
            indice_elegido, duracion_real, midi_val, nuevo_min, nuevo_max = _enforce_range_and_repetition(
                indice_elegido,
                indices_disponibles,
                duracion_units,
                contexto,
                estado,
                limite_repeticion,
            )

            duracion_units = duracion_real

            nota_nombre = contexto.sorted_pitches[indice_elegido].nameWithOctave
            velocidad = _velocity_for_beat(beat_index)

            eventos.append(
                MelodyEvent(
                    pitch_name=nota_nombre,
                    duration_units=duracion_units,
                    velocity=velocidad,
                    segment_index=seg_idx,
                    index_in_chord=indice_elegido,
                    beat_index=beat_index,
                )
            )

            distribucion.register(duracion_units)

            unidades_restantes -= duracion_units
            total_unidades += duracion_units

            anterior_indice = estado.last_index
            anterior_nombre = estado.last_pitch_name

            if motivo_activo is None and indice_compas == 0 and len(motivo) < 6:
                motivo.append(MotifEntry(index_in_sorted=indice_elegido, duration_units=duracion_units, is_strong=es_fuerte))

            if anterior_nombre == nota_nombre:
                consecutivo = estado.consecutive_units_same_pitch + duracion_units
            else:
                consecutivo = duracion_units

            estado.last_index = indice_elegido
            estado.last_pitch_name = nota_nombre
            estado.last_segment_index = seg_idx
            estado.consecutive_units_same_pitch = consecutivo
            estado.global_min = nuevo_min
            estado.global_max = nuevo_max

            if anterior_indice is not None:
                movimiento = indice_elegido - anterior_indice
                if estado.pending_resolution is not None:
                    if movimiento == 0:
                        pass
                    elif movimiento == -estado.pending_resolution:
                        estado.pending_resolution = None
                    else:
                        estado.pending_resolution = None
                else:
                    if abs(movimiento) >= 2:
                        estado.pending_resolution = 1 if movimiento > 0 else -1
                    else:
                        estado.pending_resolution = None
            else:
                estado.pending_resolution = None

            indice_nota_en_compas += 1

    _apply_final_resolution(eventos, contexts)
    return eventos

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
    if isinstance(acorde_data_o_lista_str, dict):
        posibles_claves = ("voicing", "notas", "notes")
        for clave in posibles_claves:
            if clave in acorde_data_o_lista_str and isinstance(acorde_data_o_lista_str[clave], (list, tuple)):
                lista_notas_str = list(acorde_data_o_lista_str[clave])
                break
    elif isinstance(acorde_data_o_lista_str, list):
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
    objetivo_min_octava = max(params.octava_melodia_min, highest_pitch.octave)
    objetivo_max_octava = min(params.octava_melodia_max, highest_pitch.octave + 1)

    if objetivo_min_octava > objetivo_max_octava:
        # Si la progresión está fuera del rango solicitado por el usuario,
        # forzamos ambos extremos al límite más cercano permitido.
        limite_clamp = min(
            params.octava_melodia_max,
            max(params.octava_melodia_min, highest_pitch.octave),
        )
        objetivo_min_octava = limite_clamp
        objetivo_max_octava = limite_clamp

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

def _snap_pitch_to_chord(p_obj, notas_acorde, referencia=None):
    """Ajusta una nota candidata al tono del acorde más cercano."""
    if p_obj is None or not notas_acorde:
        return p_obj

    candidato_midi = p_obj.midi
    ref_midi = referencia.midi if referencia is not None else candidato_midi
    direccion = 0
    if referencia is not None:
        if candidato_midi > ref_midi:
            direccion = 1
        elif candidato_midi < ref_midi:
            direccion = -1

    def _ranking(nota_acorde):
        distancia = abs(nota_acorde.midi - candidato_midi)
        if direccion == 0:
            penalizacion = 0
        else:
            misma_direccion = (nota_acorde.midi - ref_midi) * direccion >= 0
            penalizacion = 0 if misma_direccion else 1
        return (distancia, penalizacion, abs(nota_acorde.midi - ref_midi))

    mejor_opcion = min(notas_acorde, key=_ranking)
    return pitch.Pitch(mejor_opcion.nameWithOctave)

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
         nota_actual = pitch.Pitch(ultima_nota.nameWithOctave)
    else:
         nota_actual = pitch.Pitch(random.choice(notas_acorde).nameWithOctave) # Seguro porque ya comprobamos que notas_acorde no está vacía

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

            nota_candidata = _snap_pitch_to_chord(
                pitch.Pitch(nota_candidata.nameWithOctave),
                notas_acorde,
                nota_actual,
            )
            if nota_candidata is None:
                nota_candidata = pitch.Pitch(nota_actual.nameWithOctave)

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

def _construir_timeline_acordes(acordes, ritmos):
    timeline = []
    cursor = 0.0
    for acorde, duracion in zip(acordes, ritmos):
        try:
            duracion_ql = float(duracion)
        except (TypeError, ValueError):
            duracion_ql = 0.0
        inicio = cursor
        cursor += max(0.0, duracion_ql)
        timeline.append((inicio, cursor, acorde))
    return timeline

def _variar_melodia(eventos_melodia, segmento_acordes, segmento_ritmos, notas_escala, params):
    """Aplica variaciones manteniendo las notas dentro de los acordes correspondientes."""
    if not eventos_melodia:
        return []

    timeline = _construir_timeline_acordes(segmento_acordes, segmento_ritmos)
    if not timeline:
        return list(eventos_melodia)

    eventos_variados = []
    tiempo_actual = 0.0
    indice_timeline = 0

    for nota, duracion in eventos_melodia:
        try:
            duracion_ql = float(duracion)
        except (TypeError, ValueError):
            duracion_ql = 0.0

        while indice_timeline < len(timeline) and tiempo_actual >= timeline[indice_timeline][1] - 1e-6:
            indice_timeline += 1

        if indice_timeline >= len(timeline):
            acorde_actual = segmento_acordes[-1]
        else:
            acorde_actual = timeline[indice_timeline][2]

        notas_acorde = _expandir_notas_acorde_en_rango(acorde_actual, params)

        if nota != "0" and notas_acorde:
            nota_original = pitch.Pitch(nota)
            candidato = pitch.Pitch(nota_original.nameWithOctave)
            if random.random() < 0.3 and notas_escala:
                vecinos = [p for p in notas_escala if 0 < abs(p.midi - nota_original.midi) <= 2]
                if vecinos:
                    candidato = random.choice(vecinos)
            candidato = _snap_pitch_to_chord(candidato, notas_acorde, nota_original)
            candidato = _clamp_pitch_to_range(candidato, params) or nota_original
            eventos_variados.append((candidato.nameWithOctave, duracion))
        else:
            eventos_variados.append((nota, duracion))

        tiempo_actual += max(0.0, duracion_ql)

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
    motivo = _crear_motivo_musical(notas_primer_acorde, perfil_actual, escala_actual)
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
    
    acordes_originales = list(acordes_para_melodia)
    ritmo_originales = list(ritmo_para_melodia)

    leading_silence_events = []
    pares_acorde_ritmo = list(zip(acordes_para_melodia, ritmo_para_melodia))
    while pares_acorde_ritmo and not notas_del_acorde_music21(pares_acorde_ritmo[0][0]):
        acorde_inicial, duracion_inicial = pares_acorde_ritmo.pop(0)
        try:
            dur_float = float(duracion_inicial)
        except (TypeError, ValueError):
            dur_float = 0.0
        if dur_float > 0:
            leading_silence_events = _agregar_evento(leading_silence_events, "0", dur_float)

    if pares_acorde_ritmo:
        acordes_para_melodia = [par[0] for par in pares_acorde_ritmo]
        ritmo_para_melodia = [par[1] for par in pares_acorde_ritmo]
    else:
        acordes_para_melodia = []
        ritmo_para_melodia = []

    if not acordes_para_melodia:
        resultado_vacio = leading_silence_events
        if devolver_contexto:
            return resultado_vacio, acordes_originales, ritmo_originales
        return resultado_vacio

    perfil_actual = PERFILES_GENERO.get(str(genero).lower(), PERFILES_GENERO["default"])
    params_mel = ParametrosMelodicos(bpm=bpm, octava_melodia_min=octava_melodia_min, octava_melodia_max=octava_melodia_max)
    _ajustar_rango_melodia_a_progresion(params_mel, acordes_para_melodia)

    contexts_reglas = _build_rule_contexts(acordes_para_melodia, ritmo_para_melodia, params_mel)
    if contexts_reglas:
        eventos_reglas = _generar_melodia_con_reglas(contexts_reglas, params_mel)
        if eventos_reglas:
            melodia_reglas = _convert_events_to_output(eventos_reglas, params_mel.melodia_grid_unit_ql)
            if leading_silence_events:
                melodia_reglas = leading_silence_events + melodia_reglas
            if devolver_contexto:
                return melodia_reglas, acordes_originales, ritmo_originales
            return melodia_reglas

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
        if leading_silence_events:
            melodia_simple = leading_silence_events + melodia_simple
        if devolver_contexto:
            return melodia_simple, acordes_originales, ritmo_originales
        return melodia_simple

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
         if leading_silence_events:
             melodia_simple = leading_silence_events + melodia_simple
         if devolver_contexto:
             return melodia_simple, acordes_originales, ritmo_originales
         return melodia_simple

    notas_primer_acorde = _expandir_notas_acorde_en_rango(segmento_A_acordes[0], params_mel)
    if not notas_primer_acorde:
        total_dur = sum(float(r) for r in ritmo_para_melodia)
        melodia_silencio = [("0", str(total_dur))] if total_dur > 0 else []
        if leading_silence_events:
            melodia_silencio = leading_silence_events + melodia_silencio
        if devolver_contexto:
            return melodia_silencio, acordes_originales, ritmo_originales
        return melodia_silencio

    motivo_principal = _crear_motivo_musical(notas_primer_acorde, perfil_actual, escala_actual)
    melodia_A, ultima_nota_A = _generar_seccion_melodica(segmento_A_acordes, segmento_A_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)
    
    notas_acorde_B = _expandir_notas_acorde_en_rango(segmento_B_acordes[0], params_mel) if segmento_B_acordes else notas_primer_acorde
    motivo_B = _crear_motivo_musical(notas_acorde_B, perfil_actual, escala_actual) # Pasar escala_actual
    melodia_B, _ = _generar_seccion_melodica(segmento_B_acordes, segmento_B_ritmos, tecnica_elegida, motivo_B, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, ultima_nota_A)

    if random.random() < perfil_actual["prob_variacion_A"]:
        print("DEBUG (Melodia): Generando variación A'")
        melodia_A_base_para_variacion, _ = _generar_seccion_melodica(segmento_A2_acordes, segmento_A2_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)
        melodia_A2 = _variar_melodia(
            melodia_A_base_para_variacion,
            segmento_A2_acordes,
            segmento_A2_ritmos,
            notas_escala_disponibles_obj,
            params_mel,
        )
    else:
        print("DEBUG (Melodia): Repitiendo sección A")
        melodia_A2, _ = _generar_seccion_melodica(segmento_A2_acordes, segmento_A2_ritmos, tecnica_elegida, motivo_principal, perfil_actual, escala_actual, notas_escala_disponibles_obj, params_mel, None)

    melodia_final = leading_silence_events + melodia_A + melodia_B + melodia_A2
    if devolver_contexto:
        return melodia_final, acordes_originales, ritmo_originales
    return melodia_final


# --- Bloque de Pruebas ---
if __name__ == "__main__":
    acordes_test = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"], ["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
    ritmo_test = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0] # Progresión de 8 acordes
    raiz_test = "C"
    modo_test = "major"

    print("\n--- Prueba de generación por GÉNERO (Estructura A-B-A') ---")
    
    for genero_actual in ["pop", "lofi", "reggaeton", "rnb", "techno"]:
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