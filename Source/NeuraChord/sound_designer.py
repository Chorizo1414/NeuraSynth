import random
from copy import deepcopy
from typing import Dict, List, Tuple, Union

# ==============================================================================
# ==                            HERRAMIENTAS BASE                            ==
# ==============================================================================

Number = Union[int, float]


def float_range(min_val: float, max_val: float, limits: Tuple[float, float] = None) -> Dict:
    """Helper para describir un parámetro flotante aleatorio."""
    limits = limits or (min_val, max_val)
    return {
        "type": "float",
        "range": (float(min_val), float(max_val)),
        "limits": (float(limits[0]), float(limits[1])),
    }


def int_range(min_val: int, max_val: int, limits: Tuple[int, int] = None) -> Dict:
    """Helper para describir un parámetro entero aleatorio."""
    limits = limits or (min_val, max_val)
    return {
        "type": "int",
        "range": (int(min_val), int(max_val)),
        "limits": (int(limits[0]), int(limits[1])),
    }


def choice(values: List, weights: List[float] = None) -> Dict:
    return {
        "type": "choice",
        "values": list(values),
        "weights": list(weights) if weights is not None else None,
    }


def constant(value) -> Dict:
    return {"type": "constant", "value": value}


def bool_prob(prob_true: float) -> Dict:
    prob_true = max(0.0, min(1.0, prob_true))
    return choice([False, True], weights=[1.0 - prob_true, prob_true])


def normalize_spec(spec) -> Dict:
    """Normaliza tuplas heredadas a la nueva estructura de especificaciones."""
    if isinstance(spec, dict) and "type" in spec:
        return deepcopy(spec)
    if isinstance(spec, tuple) and len(spec) == 2:
        # Asumimos rango flotante por compatibilidad
        return float_range(spec[0], spec[1])
    raise ValueError(f"Especificación de parámetro inválida: {spec}")


def scale_param(spec: Dict, multiplier: float) -> Dict:
    if spec["type"] not in {"float", "int"}:
        return spec

    min_val, max_val = spec["range"]
    limits = spec.get("limits", spec["range"])

    new_min = min_val * multiplier
    new_max = max_val * multiplier

    low_limit, high_limit = limits
    new_min = max(low_limit, min(new_min, high_limit))
    new_max = max(low_limit, min(new_max, high_limit))

    if new_min > new_max:
        new_min, new_max = new_max, new_min

    if spec["type"] == "int":
        new_min = int(round(new_min))
        new_max = int(round(new_max))
        if new_min == new_max:
            spec["range"] = (new_min, new_max)
            return spec
        new_min = max(low_limit, min(new_min, high_limit))
        new_max = max(low_limit, min(new_max, high_limit))
        if new_min > new_max:
            new_min, new_max = new_max, new_min
        spec["range"] = (int(new_min), int(new_max))
    else:
        spec["range"] = (float(new_min), float(new_max))

    return spec


# ==============================================================================
# ==                         TABLAS DE WAVETABLES                             ==
# ==============================================================================
AVAILABLE_WAVETABLES = [
    "saw.wav",
    "square.wav",
    "pulse.wav",
    "triangle.wav",
    "sen.wav",
    "senHarmonic.wav",
    "whitenoise.wav",
]

BASE_WAVETABLE_OPTIONS = {
    "osc1": AVAILABLE_WAVETABLES,
    "osc2": AVAILABLE_WAVETABLES,
    "osc3": AVAILABLE_WAVETABLES,
}


# ==============================================================================
# ==                        CONFIGURACIÓN GLOBAL BASE                         ==
# ==============================================================================

DEFAULT_PARAM_SPECS: Dict[str, Dict] = {
    # --- Master ---
    "master_gain": float_range(0.55, 0.85, limits=(0.0, 1.0)),
    "master_glide": float_range(0.0, 0.25, limits=(0.0, 2.0)),
    "master_drive": float_range(0.0, 0.35, limits=(0.0, 1.0)),
    "master_dark": float_range(0.0, 0.5, limits=(0.0, 1.0)),
    "master_bright": float_range(0.0, 0.5, limits=(0.0, 1.0)),
    "master_chorus_on": bool_prob(0.35),

    # --- Envelope ---
    "attack": float_range(0.01, 0.4, limits=(0.0, 5.0)),
    "decay": float_range(0.2, 1.0, limits=(0.0, 5.0)),
    "sustain": float_range(0.4, 0.85, limits=(0.0, 1.0)),
    "release": float_range(0.3, 1.2, limits=(0.0, 5.0)),

    # --- Oscillator Levels ---
    "osc1_gain": float_range(0.6, 0.95, limits=(0.0, 1.0)),
    "osc2_gain": float_range(0.3, 0.7, limits=(0.0, 1.0)),
    "osc3_gain": float_range(0.1, 0.5, limits=(0.0, 1.0)),

    # --- Oscillator tuning & panorama ---
    "osc1_octave": int_range(-1, 1, limits=(-2, 2)),
    "osc1_pitch": int_range(-7, 7, limits=(-12, 12)),
    "osc1_fine": float_range(-20.0, 20.0, limits=(-50.0, 50.0)),
    "osc1_pan": float_range(0.4, 0.6, limits=(0.0, 1.0)),

    "osc2_octave": int_range(-2, 0, limits=(-2, 2)),
    "osc2_pitch": int_range(-9, 9, limits=(-12, 12)),
    "osc2_fine": float_range(-25.0, 25.0, limits=(-50.0, 50.0)),
    "osc2_pan": float_range(0.2, 0.8, limits=(0.0, 1.0)),

    "osc3_octave": int_range(-2, 2, limits=(-2, 2)),
    "osc3_pitch": int_range(-12, 12, limits=(-12, 12)),
    "osc3_fine": float_range(-30.0, 30.0, limits=(-50.0, 50.0)),
    "osc3_pan": float_range(0.1, 0.9, limits=(0.0, 1.0)),

    # --- Unison (Osc1 siempre disponible, 2 y 3 opcionales) ---
    "osc1_unison_voices": int_range(2, 5, limits=(1, 16)),
    "osc1_unison_detune": float_range(0.08, 0.35, limits=(0.0, 1.0)),
    "osc1_unison_balance": float_range(-0.3, 0.3, limits=(-1.0, 1.0)),
    "osc1_unison_spread": float_range(0.3, 1.2, limits=(0.0, 2.5)),

    "osc2_unison_voices": int_range(1, 4, limits=(1, 16)),
    "osc2_unison_detune": float_range(0.05, 0.25, limits=(0.0, 1.0)),
    "osc2_unison_balance": float_range(-0.2, 0.2, limits=(-1.0, 1.0)),

    "osc3_unison_voices": int_range(1, 3, limits=(1, 16)),
    "osc3_unison_detune": float_range(0.05, 0.2, limits=(0.0, 1.0)),
    "osc3_unison_balance": float_range(-0.2, 0.2, limits=(-1.0, 1.0)),

    # --- Filter ---
    "filter_cutoff_hz": float_range(300.0, 14000.0, limits=(20.0, 20000.0)),
    "filter_q": float_range(0.2, 0.7, limits=(0.1, 10.0)),
    "filter_env_amt": float_range(-0.2, 0.5, limits=(-1.0, 1.0)),
    "filter_keytrack": bool_prob(0.45),

    # --- Modulación ---
    "fm_amount": float_range(-0.25, 0.25, limits=(-1.0, 1.0)),
    "lfo_speed_hz": float_range(0.1, 1.6, limits=(0.0, 30.0)),
    "lfo_amount": float_range(0.02, 0.2, limits=(0.0, 1.0)),

    # --- Reverb ---
    "reverb_dry_level": float_range(0.6, 0.85, limits=(0.0, 1.0)),
    "reverb_wet_level": float_range(0.1, 0.3, limits=(0.0, 1.0)),
    "reverb_room_size": float_range(0.5, 0.8, limits=(0.0, 1.0)),
    "reverb_damping": float_range(0.3, 0.7, limits=(0.0, 1.0)),
    "reverb_pre_delay": float_range(0.05, 0.25, limits=(0.0, 1.0)),
    "reverb_diffusion": float_range(0.5, 0.85, limits=(0.0, 1.0)),
    "reverb_decay": float_range(0.4, 0.8, limits=(0.0, 1.0)),

    # --- Delay ---
    "delay_dry_level": float_range(0.65, 0.95, limits=(0.0, 1.0)),
    "delay_wet_level": float_range(0.15, 0.35, limits=(0.0, 1.0)),
    "delay_side_level": float_range(0.1, 0.3, limits=(0.0, 1.0)),
    "delay_hp_freq": float_range(0.05, 0.35, limits=(0.0, 1.0)),
    "delay_lp_freq": float_range(0.6, 1.0, limits=(0.0, 1.0)),
    "delay_time_left": float_range(0.18, 0.55, limits=(0.0, 1.0)),
    "delay_time_center": float_range(0.22, 0.6, limits=(0.0, 1.0)),
    "delay_time_right": float_range(0.28, 0.65, limits=(0.0, 1.0)),
    "delay_feedback": float_range(0.25, 0.55, limits=(0.0, 0.98)),
    "delay_wow_depth": float_range(0.15, 0.45, limits=(0.0, 1.0)),
}


# ==============================================================================
# ==                            ARQUETIPOS DE SONIDO                          ==
# ==============================================================================

ARCHETYPES = {
    "lead": {
        "params": {
            "master_gain": float_range(0.7, 0.9, limits=(0.0, 1.0)),
            "master_drive": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "master_bright": float_range(0.6, 1.0, limits=(0.0, 1.0)),
            "master_dark": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.45),

            "attack": float_range(0.0, 0.05, limits=(0.0, 5.0)),
            "decay": float_range(0.12, 0.4, limits=(0.0, 5.0)),
            "sustain": float_range(0.75, 1.0, limits=(0.0, 1.0)),
            "release": float_range(0.1, 0.3, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.8, 1.0, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.0, 0.2, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(3, 6, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.15, 0.35, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.6, 1.3, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(2000.0, 16000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.15, 0.35, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.0, 0.2, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.3),

            "fm_amount": float_range(0.05, 0.35, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.2, 1.4, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.03, 0.15, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.65, 0.85, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.08, 0.2, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.5, 0.75, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.2, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.7, 0.95, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.1, 0.25, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.05, 0.2, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.1, 0.4, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.18, 0.45, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.22, 0.55, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.3, 0.65, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.25, 0.55, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.2, 0.5, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["saw.wav", "square.wav"],
            "osc2": ["saw.wav", "square.wav", "pulse.wav"],
            "osc3": ["senHarmonic.wav", "triangle.wav"],
        },
    },
    "pad": {
        "params": {
            "master_gain": float_range(0.5, 0.75, limits=(0.0, 1.0)),
            "master_drive": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "master_dark": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "master_bright": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.75),

            "attack": float_range(0.8, 3.0, limits=(0.0, 5.0)),
            "decay": float_range(1.5, 3.5, limits=(0.0, 5.0)),
            "sustain": float_range(0.7, 0.9, limits=(0.0, 1.0)),
            "release": float_range(2.0, 5.0, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.4, 0.7, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(5, 8, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.12, 0.3, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(1.0, 2.0, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(300.0, 4000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.2, 0.5, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.1, 0.4, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.7),

            "fm_amount": float_range(-0.1, 0.1, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.0, 0.8, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.0, 0.15, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.5, 0.7, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.2, 0.4, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.6, 0.9, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.6, 0.95, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.1, 0.3, limits=(0.0, 1.0)),
            "reverb_diffusion": float_range(0.6, 0.9, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.2, 0.4, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.15, 0.35, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.7, 1.0, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.35, 0.75, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.4, 0.8, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.35, 0.65, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.2, 0.5, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "triangle.wav"],
            "osc2": ["sen.wav", "triangle.wav", "saw.wav"],
            "osc3": ["saw.wav", "senHarmonic.wav", "triangle.wav"],
        },
    },
    "bass": {
        "params": {
            "master_gain": float_range(0.7, 0.95, limits=(0.0, 1.0)),
            "master_drive": float_range(0.4, 0.8, limits=(0.0, 1.0)),
            "master_dark": float_range(0.4, 0.8, limits=(0.0, 1.0)),
            "master_bright": float_range(0.0, 0.3, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.15),

            "attack": float_range(0.0, 0.04, limits=(0.0, 5.0)),
            "decay": float_range(0.15, 0.5, limits=(0.0, 5.0)),
            "sustain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "release": float_range(0.1, 0.25, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.9, 1.0, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.4, 0.8, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.0, 0.2, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(1, 3, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.05, 0.18, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.1, 0.6, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(80.0, 600.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.3, 0.8, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.3, 0.7, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.2),

            "fm_amount": float_range(0.0, 0.4, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.1, 1.2, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.02, 0.12, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.85, 1.0, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.0, 0.12, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.0, 0.15, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.8, 1.0, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.0, 0.15, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.0, 0.1, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.6, 0.95, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.1, 0.3, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.15, 0.35, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.2, 0.4, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.1, 0.3, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.0, 0.2, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "square.wav"],
            "osc2": ["saw.wav", "square.wav"],
            "osc3": [],
        },
    },
    "pluck": {
        "params": {
            "master_gain": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "master_drive": float_range(0.1, 0.4, limits=(0.0, 1.0)),
            "master_bright": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "master_dark": float_range(0.0, 0.3, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.5),

            "attack": float_range(0.0, 0.015, limits=(0.0, 5.0)),
            "decay": float_range(0.08, 0.3, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.15, limits=(0.0, 1.0)),
            "release": float_range(0.15, 0.45, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.7, 0.95, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.0, 0.3, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(2, 4, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.1, 0.3, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.5, 1.4, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(1000.0, 9000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.15, 0.45, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.4, 0.9, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.4),

            "fm_amount": float_range(0.0, 0.3, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.1, 1.2, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.02, 0.15, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.1, 0.25, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.2, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.25, 0.45, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.15, 0.35, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.1, 0.4, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.5, 0.9, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.25, 0.55, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.35, 0.65, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.35, 0.6, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.2, 0.5, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "square.wav"],
            "osc2": ["saw.wav", "square.wav", "triangle.wav"],
            "osc3": ["triangle.wav", "senHarmonic.wav"],
        },
    },
    "keys": {
        "params": {
            "master_gain": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "master_drive": float_range(0.05, 0.25, limits=(0.0, 1.0)),
            "master_dark": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "master_bright": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.45),

            "attack": float_range(0.03, 0.15, limits=(0.0, 5.0)),
            "decay": float_range(0.4, 1.0, limits=(0.0, 5.0)),
            "sustain": float_range(0.25, 0.55, limits=(0.0, 1.0)),
            "release": float_range(0.35, 0.9, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.65, 0.9, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.2, 0.45, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(2, 3, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.08, 0.2, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.4, 1.0, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(900.0, 6000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.2, 0.5, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.1, 0.35, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.5),

            "fm_amount": float_range(0.0, 0.25, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.1, 1.1, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.02, 0.12, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.15, 0.3, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.2, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.15, 0.3, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.1, 0.25, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.05, 0.3, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.6, 0.9, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.22, 0.55, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.28, 0.6, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.32, 0.65, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.25, 0.45, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.1, 0.3, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "triangle.wav", "saw.wav"],
            "osc2": ["sen.wav", "triangle.wav", "square.wav"],
            "osc3": ["saw.wav", "senHarmonic.wav", "triangle.wav"],
        },
    },
    "poly_synth": {
        "params": {
            "master_gain": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "master_drive": float_range(0.05, 0.3, limits=(0.0, 1.0)),
            "master_dark": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "master_bright": float_range(0.35, 0.65, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.55),

            "attack": float_range(0.1, 0.45, limits=(0.0, 5.0)),
            "decay": float_range(0.35, 1.1, limits=(0.0, 5.0)),
            "sustain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "release": float_range(0.45, 1.2, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.7, 0.95, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.35, 0.65, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(4, 6, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.12, 0.28, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.7, 1.6, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(600.0, 8000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.2, 0.55, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.15, 0.45, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.55),

            "fm_amount": float_range(-0.15, 0.3, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.1, 1.0, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.05, 0.2, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.18, 0.35, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.5, 0.85, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.25, limits=(0.0, 1.0)),
            "reverb_diffusion": float_range(0.55, 0.85, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.2, 0.35, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.15, 0.3, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.05, 0.3, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.6, 0.95, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.25, 0.6, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.3, 0.65, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.35, 0.7, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.3, 0.55, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.15, 0.4, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["saw.wav", "square.wav", "triangle.wav"],
            "osc2": ["saw.wav", "triangle.wav", "pulse.wav"],
            "osc3": ["triangle.wav", "sen.wav", "senHarmonic.wav"],
        },
    },
    "string_brass": {
        "params": {
            "master_gain": float_range(0.55, 0.78, limits=(0.0, 1.0)),
            "master_drive": float_range(0.1, 0.35, limits=(0.0, 1.0)),
            "master_dark": float_range(0.25, 0.55, limits=(0.0, 1.0)),
            "master_bright": float_range(0.35, 0.7, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.65),

            "attack": float_range(0.25, 1.1, limits=(0.0, 5.0)),
            "decay": float_range(0.6, 1.6, limits=(0.0, 5.0)),
            "sustain": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "release": float_range(0.8, 1.8, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.75, 0.95, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.25, 0.55, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(5, 7, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.12, 0.26, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.9, 1.8, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(800.0, 5000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.25, 0.55, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.2, 0.5, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.6),

            "fm_amount": float_range(-0.1, 0.25, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.1, 0.9, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.05, 0.2, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.25, 0.45, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.6, 0.9, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.25, limits=(0.0, 1.0)),
            "reverb_diffusion": float_range(0.6, 0.9, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.2, 0.35, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.15, 0.3, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.05, 0.25, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.65, 0.95, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.3, 0.65, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.35, 0.7, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.4, 0.75, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.35, 0.6, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.15, 0.35, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["saw.wav", "senHarmonic.wav"],
            "osc2": ["saw.wav", "square.wav", "triangle.wav"],
            "osc3": ["triangle.wav", "sen.wav"],
        },
    },
    "kick": {
        "params": {
            "master_gain": float_range(0.75, 0.95, limits=(0.0, 1.0)),
            "master_drive": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "master_dark": float_range(0.4, 0.75, limits=(0.0, 1.0)),
            "master_bright": float_range(0.1, 0.35, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.05),

            "attack": float_range(0.0, 0.01, limits=(0.0, 5.0)),
            "decay": float_range(0.08, 0.2, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.05, limits=(0.0, 1.0)),
            "release": float_range(0.15, 0.35, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.85, 1.0, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.0, 0.2, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(1, 2, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.02, 0.08, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.1, 0.35, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(1000.0, 12000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.1, 0.35, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.1, 0.35, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.2),

            "fm_amount": float_range(0.1, 0.45, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.0, 1.0, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.0, 0.1, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.9, 1.0, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.0, 0.1, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.2, 0.45, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.9, 1.0, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.0, 0.1, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.0, 0.1, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.0, 0.1, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.6, 0.95, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.08, 0.2, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.1, 0.25, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.12, 0.3, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.05, 0.2, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.0, 0.1, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "saw.wav"],
            "osc2": ["square.wav", "pulse.wav"],
            "osc3": ["whitenoise.wav"],
        },
    },
    "snare": {
        "params": {
            "master_gain": float_range(0.7, 0.9, limits=(0.0, 1.0)),
            "master_drive": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "master_dark": float_range(0.15, 0.4, limits=(0.0, 1.0)),
            "master_bright": float_range(0.45, 0.8, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.2),

            "attack": float_range(0.0, 0.01, limits=(0.0, 5.0)),
            "decay": float_range(0.18, 0.45, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.15, limits=(0.0, 1.0)),
            "release": float_range(0.25, 0.6, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.5, 0.9, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(1, 2, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.05, 0.15, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.2, 0.6, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(1500.0, 8000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.35, 0.8, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.2, 0.6, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.35),

            "fm_amount": float_range(0.0, 0.35, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.2, 1.5, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.02, 0.15, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.75, 0.95, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.1, 0.28, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.35, 0.6, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.8, 1.0, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.05, 0.2, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.05, 0.2, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.5, 0.85, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.12, 0.3, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.15, 0.35, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.18, 0.4, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.1, 0.3, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.05, 0.2, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["square.wav", "saw.wav"],
            "osc2": ["saw.wav", "triangle.wav"],
            "osc3": ["whitenoise.wav"],
        },
    },
    "hihat": {
        "params": {
            "master_gain": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "master_drive": float_range(0.25, 0.6, limits=(0.0, 1.0)),
            "master_dark": float_range(0.0, 0.25, limits=(0.0, 1.0)),
            "master_bright": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.25),

            "attack": float_range(0.0, 0.005, limits=(0.0, 5.0)),
            "decay": float_range(0.03, 0.12, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.05, limits=(0.0, 1.0)),
            "release": float_range(0.05, 0.2, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.8, 1.0, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(1, 2, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.05, 0.15, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.2, 0.6, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(6000.0, 18000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.25, 0.55, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.0, 0.25, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.25),

            "fm_amount": float_range(0.0, 0.25, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.5, 2.5, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.02, 0.15, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.85, 1.0, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.05, 0.18, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.2, 0.45, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.85, 1.0, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.0, 0.12, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.0, 0.12, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.2, 0.6, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.6, 1.0, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.05, 0.18, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.08, 0.2, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.1, 0.25, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.05, 0.18, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.05, 0.2, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["square.wav", "pulse.wav"],
            "osc2": ["triangle.wav", "square.wav"],
            "osc3": ["whitenoise.wav"],
        },
    },
    "fx": {
        "params": {
            "master_gain": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "master_drive": float_range(0.1, 0.5, limits=(0.0, 1.0)),
            "master_dark": float_range(0.1, 0.5, limits=(0.0, 1.0)),
            "master_bright": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.55),

            "attack": float_range(0.15, 4.0, limits=(0.0, 5.0)),
            "decay": float_range(0.4, 3.0, limits=(0.0, 5.0)),
            "sustain": float_range(0.1, 0.7, limits=(0.0, 1.0)),
            "release": float_range(0.3, 4.5, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.5, 0.85, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.2, 0.6, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(3, 6, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.15, 0.45, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.8, 2.0, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(200.0, 18000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.2, 0.9, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(-0.6, 0.8, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.4),

            "fm_amount": float_range(-0.5, 0.6, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.2, 4.5, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.1, 0.45, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.55, 0.95, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.55, 0.95, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.35, limits=(0.0, 1.0)),
            "reverb_diffusion": float_range(0.55, 0.95, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.25, 0.55, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.0, 0.4, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.4, 1.0, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.2, 0.75, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.25, 0.8, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.3, 0.85, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.35, 0.7, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.25, 0.6, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["saw.wav", "square.wav", "senHarmonic.wav"],
            "osc2": ["pulse.wav", "triangle.wav", "whitenoise.wav"],
            "osc3": ["whitenoise.wav", "sen.wav", "saw.wav"],
        },
    },
    "bell": {
        "params": {
            "master_gain": float_range(0.55, 0.8, limits=(0.0, 1.0)),
            "master_drive": float_range(0.0, 0.25, limits=(0.0, 1.0)),
            "master_dark": float_range(0.1, 0.35, limits=(0.0, 1.0)),
            "master_bright": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.35),

            "attack": float_range(0.0, 0.02, limits=(0.0, 5.0)),
            "decay": float_range(0.35, 0.9, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "release": float_range(0.6, 1.4, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.6, 0.85, limits=(0.0, 1.0)),
            "osc2_gain": float_range(0.45, 0.7, limits=(0.0, 1.0)),
            "osc3_gain": float_range(0.25, 0.55, limits=(0.0, 1.0)),

            "osc1_unison_voices": int_range(1, 2, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.05, 0.15, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.3, 0.8, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(2000.0, 12000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.25, 0.55, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.0, 0.25, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.45),

            "fm_amount": float_range(0.25, 0.6, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(0.1, 1.5, limits=(0.0, 30.0)),
            "lfo_amount": float_range(0.02, 0.15, limits=(0.0, 1.0)),

            "reverb_dry_level": float_range(0.5, 0.75, limits=(0.0, 1.0)),
            "reverb_wet_level": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "reverb_decay": float_range(0.5, 0.85, limits=(0.0, 1.0)),
            "reverb_pre_delay": float_range(0.05, 0.25, limits=(0.0, 1.0)),

            "delay_dry_level": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.2, 0.4, limits=(0.0, 1.0)),
            "delay_side_level": float_range(0.15, 0.35, limits=(0.0, 1.0)),
            "delay_hp_freq": float_range(0.1, 0.35, limits=(0.0, 1.0)),
            "delay_lp_freq": float_range(0.6, 0.95, limits=(0.0, 1.0)),
            "delay_time_left": float_range(0.25, 0.6, limits=(0.0, 1.0)),
            "delay_time_center": float_range(0.3, 0.65, limits=(0.0, 1.0)),
            "delay_time_right": float_range(0.35, 0.7, limits=(0.0, 1.0)),
            "delay_feedback": float_range(0.3, 0.55, limits=(0.0, 0.98)),
            "delay_wow_depth": float_range(0.1, 0.3, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "triangle.wav"],
            "osc2": ["senHarmonic.wav", "triangle.wav"],
            "osc3": ["sen.wav", "saw.wav"],
        },
    },
}


ARCHETYPES.update(
    {
        "string_synth": deepcopy(ARCHETYPES["string_brass"]),
        "brass_synth": deepcopy(ARCHETYPES["string_brass"]),
        "poly": deepcopy(ARCHETYPES["poly_synth"]),
        "mallet": deepcopy(ARCHETYPES["bell"]),
    }
)

# ==============================================================================
# ==                           MODIFICADORES SEMÁNTICOS                       ==
# ==============================================================================

MODIFIERS = {
    "bright": {
        "filter_cutoff_hz": (1.4, 1.9),
        "filter_q": (0.8, 1.1),
        "master_bright": float_range(0.7, 1.0, limits=(0.0, 1.0)),
        "master_dark": float_range(0.0, 0.2, limits=(0.0, 1.0)),
    },
    "dark": {
        "filter_cutoff_hz": (0.25, 0.6),
        "master_dark": float_range(0.5, 1.0, limits=(0.0, 1.0)),
        "master_bright": float_range(0.0, 0.2, limits=(0.0, 1.0)),
        "reverb_wet_level": (0.8, 1.1),
    },
    "warm": {
        "osc1_unison_detune": (1.15, 1.35),
        "lfo_amount": (1.1, 1.4),
        "reverb_wet_level": (1.15, 1.35),
        "master_chorus_on": bool_prob(0.8),
        "fm_amount": float_range(-0.15, 0.15, limits=(-1.0, 1.0)),
    },
    "soft": {
        "attack": (1.6, 2.5),
        "release": (1.4, 2.2),
        "master_drive": (0.4, 0.7),
        "filter_cutoff_hz": (0.7, 0.9),
        "delay_wet_level": (0.6, 0.9),
    },
    "aggressive": {
        "attack": float_range(0.0, 0.03, limits=(0.0, 5.0)),
        "master_drive": (1.6, 2.2),
        "osc1_unison_voices": int_range(4, 7, limits=(1, 16)),
        "osc1_unison_detune": (1.3, 1.7),
        "fm_amount": float_range(0.2, 0.6, limits=(-1.0, 1.0)),
        "filter_q": (1.1, 1.6),
    },
}

# ==============================================================================
# ==                                  LÓGICA                                  ==
# ==============================================================================

ParameterSpec = Dict[str, Union[str, Tuple[Number, Number], List, Number]]


def _merge_param_specs(base: Dict[str, Dict], overrides: Dict[str, Dict]) -> Dict[str, Dict]:
    merged = deepcopy(base)
    for key, spec in overrides.items():
        merged[key] = normalize_spec(spec)
    return merged


def _apply_modifier(specs: Dict[str, Dict], modifier: Dict[str, Union[Tuple[Number, Number], Dict]]):
    for param, adjustment in modifier.items():
        if param not in specs:
            continue

        if isinstance(adjustment, dict) and "type" in adjustment:
            specs[param] = normalize_spec(adjustment)
            continue

        if isinstance(adjustment, tuple) and len(adjustment) == 2:
            min_mult, max_mult = adjustment
            multiplier = random.uniform(min_mult, max_mult)
            specs[param] = scale_param(specs[param], multiplier)
            continue

        specs[param] = normalize_spec(adjustment)


def _generate_value(param: str, spec: Dict):
    spec_type = spec.get("type")

    if spec_type == "float":
        low, high = spec["range"]
        return random.uniform(low, high)
    if spec_type == "int":
        low, high = spec["range"]
        return random.randint(low, high)
    if spec_type == "choice":
        weights = spec.get("weights")
        return random.choices(spec["values"], weights=weights, k=1)[0]
    if spec_type == "constant":
        return spec["value"]

    raise ValueError(f"Tipo de especificación desconocido para '{param}': {spec}")

def _effective_bounds(spec: Dict) -> Tuple[Number, Number]:
    range_low, range_high = spec.get("range", (None, None))
    limit_low, limit_high = spec.get("limits", (range_low, range_high))

    low = range_low if range_low is not None else limit_low
    high = range_high if range_high is not None else limit_high

    if limit_low is not None:
        low = max(low, limit_low)
    if limit_high is not None:
        high = min(high, limit_high)

    return low, high


def _clamp_to_spec(value: Number, spec: Dict) -> Number:
    low, high = _effective_bounds(spec)
    if spec.get("type") == "int":
        value = int(round(value))
        low = int(round(low))
        high = int(round(high))
    return max(low, min(value, high))


def _set_numeric_param(result: Dict, specs: Dict[str, Dict], param: str, value: Number):
    spec = specs.get(param)
    if spec is None:
        result[param] = value
        return

    clamped = _clamp_to_spec(value, spec)
    if spec.get("type") == "int":
        clamped = int(clamped)
    else:
        clamped = float(clamped)
    result[param] = clamped


DEFAULT_INTERVAL_PROFILE: List[Tuple[int, float]] = [
    (0, 0.45),
    (12, 0.18),
    (-12, 0.12),
    (7, 0.1),
    (-7, 0.05),
    (5, 0.04),
    (-5, 0.03),
    (3, 0.02),
    (9, 0.01),
]


INTERVAL_PROFILES: Dict[str, List[Tuple[int, float]]] = {
    "pad": [
        (0, 0.4),
        (12, 0.18),
        (-12, 0.14),
        (7, 0.12),
        (5, 0.08),
        (-7, 0.05),
        (3, 0.03),
    ],
    "poly_synth": [
        (0, 0.38),
        (7, 0.2),
        (12, 0.18),
        (-12, 0.12),
        (5, 0.07),
        (-5, 0.05),
    ],
    "poly": [
        (0, 0.4),
        (7, 0.2),
        (12, 0.16),
        (-5, 0.1),
        (5, 0.08),
        (-12, 0.06),
    ],
    "lead": [
        (0, 0.35),
        (7, 0.22),
        (12, 0.18),
        (-12, 0.12),
        (5, 0.08),
        (-5, 0.05),
    ],
    "keys": [
        (0, 0.38),
        (12, 0.2),
        (7, 0.16),
        (5, 0.1),
        (-12, 0.1),
        (3, 0.06),
    ],
    "pluck": [
        (0, 0.42),
        (7, 0.22),
        (12, 0.14),
        (-5, 0.1),
        (5, 0.08),
        (-12, 0.04),
    ],
    "string_synth": [
        (0, 0.38),
        (12, 0.18),
        (7, 0.16),
        (-12, 0.12),
        (5, 0.09),
        (-5, 0.07),
    ],
    "string_brass": [
        (0, 0.36),
        (7, 0.2),
        (12, 0.18),
        (-12, 0.12),
        (5, 0.08),
        (3, 0.06),
    ],
    "brass_synth": [
        (0, 0.35),
        (7, 0.22),
        (12, 0.18),
        (-5, 0.1),
        (-12, 0.1),
        (5, 0.05),
    ],
    "bell": [
        (0, 0.32),
        (12, 0.24),
        (7, 0.18),
        (-12, 0.12),
        (5, 0.08),
        (3, 0.06),
    ],
    "mallet": [
        (0, 0.34),
        (12, 0.24),
        (7, 0.18),
        (5, 0.12),
        (-12, 0.08),
        (3, 0.04),
    ],
    "bass": [
        (0, 0.48),
        (-12, 0.22),
        (12, 0.12),
        (7, 0.1),
        (-5, 0.08),
    ],
    "kick": [
        (0, 0.6),
        (-12, 0.25),
        (12, 0.15),
    ],
    "snare": [
        (0, 0.55),
        (12, 0.25),
        (-12, 0.2),
    ],
    "hihat": [
        (0, 0.6),
        (12, 0.25),
        (7, 0.15),
    ],
    "fx": [
        (0, 0.28),
        (12, 0.18),
        (-12, 0.16),
        (7, 0.12),
        (-7, 0.1),
        (5, 0.08),
        (-5, 0.05),
        (3, 0.03),
    ],
}


FINE_SPAN_BY_ARCHETYPE: Dict[str, float] = {
    "bass": 2.5,
    "kick": 1.5,
    "snare": 2.0,
    "hihat": 2.0,
    "lead": 4.0,
    "pad": 5.0,
    "poly_synth": 5.0,
    "string_synth": 5.0,
    "string_brass": 5.0,
    "brass_synth": 4.5,
    "poly": 4.5,
    "keys": 4.0,
    "pluck": 3.5,
    "bell": 6.0,
    "mallet": 4.5,
    "fx": 9.0,
}


CENTERED_ARCHETYPES = {"bass", "kick", "snare"}


def _interval_allowed_for_osc(interval: int, osc_index: int, specs: Dict[str, Dict]) -> bool:
    octave_spec = specs.get(f"osc{osc_index}_octave")
    pitch_spec = specs.get(f"osc{osc_index}_pitch")
    if not octave_spec or not pitch_spec:
        return True

    oct_low, oct_high = _effective_bounds(octave_spec)
    pitch_low, pitch_high = _effective_bounds(pitch_spec)

    oct_low = int(round(oct_low))
    oct_high = int(round(oct_high))
    pitch_low = int(round(pitch_low))
    pitch_high = int(round(pitch_high))

    for octave in range(oct_low, oct_high + 1):
        remainder = interval - octave * 12
        if pitch_low <= remainder <= pitch_high:
            return True
    return False


def _choose_interval(archetype: str, osc_index: int, specs: Dict[str, Dict], used: List[int]) -> int:
    profile = INTERVAL_PROFILES.get(archetype, DEFAULT_INTERVAL_PROFILE)
    candidates: List[int] = []
    weights: List[float] = []

    for interval, weight in profile:
        if not _interval_allowed_for_osc(interval, osc_index, specs):
            continue

        penalty = 0.4 if any(abs(interval - other) < 0.1 for other in used) else 1.0
        candidates.append(interval)
        weights.append(weight * penalty)

    if not candidates:
        return 0

    if sum(weights) == 0:
        weights = [1.0] * len(candidates)

    return random.choices(candidates, weights=weights, k=1)[0]


def _assign_interval_to_osc(result: Dict, specs: Dict[str, Dict], osc_index: int, interval: int):
    octave_spec = specs.get(f"osc{osc_index}_octave")
    pitch_spec = specs.get(f"osc{osc_index}_pitch")
    if not octave_spec or not pitch_spec:
        return

    oct_low, oct_high = _effective_bounds(octave_spec)
    pitch_low, pitch_high = _effective_bounds(pitch_spec)

    oct_low = int(round(oct_low))
    oct_high = int(round(oct_high))
    pitch_low = int(round(pitch_low))
    pitch_high = int(round(pitch_high))

    best_octave = None
    best_pitch = None
    best_error = None

    for octave in range(oct_low, oct_high + 1):
        candidate_pitch = interval - octave * 12
        if pitch_low <= candidate_pitch <= pitch_high:
            error = abs(interval - (octave * 12 + candidate_pitch))
            if best_error is None or error < best_error:
                best_error = error
                best_octave = octave
                best_pitch = candidate_pitch

    if best_octave is None or best_pitch is None:
        octave = _clamp_to_spec(round(interval / 12), octave_spec)
        candidate_pitch = interval - octave * 12
        best_octave = octave
        best_pitch = _clamp_to_spec(candidate_pitch, pitch_spec)

    _set_numeric_param(result, specs, f"osc{osc_index}_octave", best_octave)
    _set_numeric_param(result, specs, f"osc{osc_index}_pitch", best_pitch)


def _shape_fine_offsets(result: Dict, specs: Dict[str, Dict], active_oscillators: List[int], archetype: str):
    base_span = FINE_SPAN_BY_ARCHETYPE.get(archetype, 4.0)
    for osc_index in active_oscillators:
        if osc_index == 1:
            continue
        spec = specs.get(f"osc{osc_index}_fine")
        if not spec:
            continue

        span = base_span
        if osc_index == 3 and len(active_oscillators) >= 3:
            span *= 1.2

        fine_value = random.uniform(-span, span)
        _set_numeric_param(result, specs, f"osc{osc_index}_fine", fine_value)


def _ensure_layered_gains(result: Dict, specs: Dict[str, Dict], active_oscillators: List[int]):
    active_count = len(active_oscillators)
    if active_count <= 1:
        return

    for position, osc_index in enumerate(active_oscillators, start=1):
        gain_key = f"osc{osc_index}_gain"
        spec = specs.get(gain_key)
        if not spec:
            continue

        range_low, range_high = spec.get("range", (0.0, 1.0))
        floor_factor = 0.55 if position == 1 else 0.3
        if active_count >= 3 and position == 3:
            floor_factor = 0.25
        elif active_count == 2 and position == 2:
            floor_factor = 0.35

        minimum = range_low + (range_high - range_low) * floor_factor
        minimum = max(range_low, min(minimum, range_high))

        if result.get(gain_key, 0.0) < minimum:
            result[gain_key] = random.uniform(minimum, range_high)

    primary_gain_key = f"osc{active_oscillators[0]}_gain"
    primary_gain = result.get(primary_gain_key, 0.0)
    for osc_index in active_oscillators[1:]:
        gain_key = f"osc{osc_index}_gain"
        spec = specs.get(gain_key)
        if not spec:
            continue
        range_low, range_high = spec.get("range", (0.0, 1.0))
        if result[gain_key] >= primary_gain:
            result[gain_key] = max(range_low, min(primary_gain - 0.05, range_high))


def _shape_panorama(result: Dict, specs: Dict[str, Dict], active_oscillators: List[int], archetype: str):
    if not active_oscillators:
        return

    centered = archetype in CENTERED_ARCHETYPES

    if centered:
        for osc_index in active_oscillators:
            pan_key = f"osc{osc_index}_pan"
            variation = random.uniform(-0.03, 0.03)
            _set_numeric_param(result, specs, pan_key, 0.5 + variation)
        return

    active_count = len(active_oscillators)
    if active_count == 1:
        variation = random.uniform(-0.05, 0.05)
        _set_numeric_param(
            result,
            specs,
            f"osc{active_oscillators[0]}_pan",
            0.5 + variation,
        )
        return

    root_variation = random.uniform(-0.04, 0.04)
    _set_numeric_param(
        result,
        specs,
        f"osc{active_oscillators[0]}_pan",
        0.5 + root_variation,
    )

    if active_count == 2:
        offset = random.uniform(0.15, 0.22)
        orientation = 1 if random.random() < 0.5 else -1
        target = 0.5 + orientation * offset
        variation = random.uniform(-0.04, 0.04)
        _set_numeric_param(
            result,
            specs,
            f"osc{active_oscillators[1]}_pan",
            target + variation,
        )
        return

    # Tres osciladores: centro + izquierda/derecha
    offset = random.uniform(0.18, 0.26)
    orientations = [-1, 1]
    random.shuffle(orientations)

    for osc_index, orientation in zip(active_oscillators[1:], orientations):
        target = 0.5 + orientation * offset
        variation = random.uniform(-0.04, 0.04)
        _set_numeric_param(result, specs, f"osc{osc_index}_pan", target + variation)


def _harmonize_oscillators(result: Dict, specs: Dict[str, Dict], archetype: str):
    active_oscillators: List[int] = []
    for osc_index in (1, 2, 3):
        wavetable = result.get(f"osc{osc_index}_wavetable", "None")
        gain = result.get(f"osc{osc_index}_gain", 0.0)
        if wavetable == "None" or gain <= 0.0:
            continue
        active_oscillators.append(osc_index)

    if not active_oscillators:
        return

    # Root oscillator: mantenerlo estable y bien centrado
    root_pitch_spec = specs.get("osc1_pitch")
    if root_pitch_spec:
        preferred = [0, 0, 0, 2, -2, 1, -1]
        preferred = [
            val
            for val in preferred
            if _effective_bounds(root_pitch_spec)[0] <= val <= _effective_bounds(root_pitch_spec)[1]
        ] or [0]
        _set_numeric_param(result, specs, "osc1_pitch", random.choice(preferred))

    root_fine_spec = specs.get("osc1_fine")
    if root_fine_spec:
        fine_span = FINE_SPAN_BY_ARCHETYPE.get(archetype, 4.0) * 0.5
        _set_numeric_param(
            result,
            specs,
            "osc1_fine",
            random.uniform(-fine_span, fine_span),
        )

    if len(active_oscillators) >= 2:
        used_intervals = [0]
        for osc_index in active_oscillators[1:]:
            interval = _choose_interval(archetype, osc_index, specs, used_intervals)
            used_intervals.append(interval)
            _assign_interval_to_osc(result, specs, osc_index, interval)

    _shape_fine_offsets(result, specs, active_oscillators, archetype)
    _ensure_layered_gains(result, specs, active_oscillators)
    _shape_panorama(result, specs, active_oscillators, archetype)


def generate_synth_patch(tags: List[str]) -> Dict:
    archetype_name = None
    modifier_names: List[str] = []

    for tag in tags:
        if tag in ARCHETYPES:
            archetype_name = tag
        elif tag in MODIFIERS:
            modifier_names.append(tag)
    
    if not archetype_name:
        return {"error": "No se encontró un arquetipo de sonido base (ej: lead, pad, bass)."}

    archetype = ARCHETYPES[archetype_name]
    specs = _merge_param_specs(DEFAULT_PARAM_SPECS, archetype.get("params", {}))

    for mod_name in modifier_names:
        _apply_modifier(specs, MODIFIERS[mod_name])

    result: Dict[str, Union[float, int, bool, str]] = {}
    for param, spec in specs.items():
        result[param] = _generate_value(param, spec)

    wavetable_choices = archetype.get("wavetable_options", BASE_WAVETABLE_OPTIONS)
    for osc_name in ("osc1", "osc2", "osc3"):
        options = wavetable_choices.get(osc_name, BASE_WAVETABLE_OPTIONS.get(osc_name, []))
        if options:
            result[f"{osc_name}_wavetable"] = random.choice(options)
        else:
            result[f"{osc_name}_wavetable"] = "None"

    _harmonize_oscillators(result, specs, archetype_name)

    if (
        archetype_name != "fx"
        and "lfo_amount" in result
        and "lfo_speed_hz" in result
    ):
        if random.random() < 0.8:
            result["lfo_amount"] = 0.0
            result["lfo_speed_hz"] = 0.0
        else:
            subtle_amount_cap = random.uniform(0.02, 0.12)
            result["lfo_amount"] = max(0.0, min(result["lfo_amount"], subtle_amount_cap))
            if result["lfo_amount"] <= 0.0:
                result["lfo_speed_hz"] = 0.0
            else:
                subtle_speed_cap = random.uniform(0.2, 1.5)
                current_speed = result["lfo_speed_hz"]
                if current_speed <= 0.0 or current_speed > subtle_speed_cap:
                    result["lfo_speed_hz"] = subtle_speed_cap
                else:
                    result["lfo_speed_hz"] = current_speed

    # Alias para compatibilidad con el procesador en C++
    if "filter_cutoff_hz" in result:
        result["filter_cutoff"] = result["filter_cutoff_hz"]

    wavetable_choices = archetype.get("wavetable_options", BASE_WAVETABLE_OPTIONS)
    for osc_name in ("osc1", "osc2", "osc3"):
        options = wavetable_choices.get(osc_name, BASE_WAVETABLE_OPTIONS.get(osc_name, []))
        if options:
            result[f"{osc_name}_wavetable"] = random.choice(options)
        else:
            result[f"{osc_name}_wavetable"] = "None"

    return result