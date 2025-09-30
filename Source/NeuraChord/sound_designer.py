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
    "lfo_speed_hz": float_range(0.3, 3.0, limits=(0.1, 30.0)),
    "lfo_amount": float_range(0.05, 0.4, limits=(0.0, 1.0)),

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
            "osc1_unison_detune": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "osc1_unison_spread": float_range(0.6, 1.3, limits=(0.0, 2.5)),

            "filter_cutoff_hz": float_range(2000.0, 16000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.15, 0.35, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.0, 0.2, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.3),

            "fm_amount": float_range(0.05, 0.35, limits=(-1.0, 1.0)),
            "lfo_speed_hz": float_range(1.5, 5.0, limits=(0.1, 30.0)),
            "lfo_amount": float_range(0.05, 0.2, limits=(0.0, 1.0)),

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
            "release": float_range(2.0, 6.0, limits=(0.0, 5.0)),

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
            "lfo_speed_hz": float_range(0.1, 1.0, limits=(0.1, 30.0)),
            "lfo_amount": float_range(0.2, 0.6, limits=(0.0, 1.0)),

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
            "lfo_speed_hz": float_range(0.5, 2.5, limits=(0.1, 30.0)),
            "lfo_amount": float_range(0.05, 0.3, limits=(0.0, 1.0)),

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
            "lfo_speed_hz": float_range(1.0, 4.0, limits=(0.1, 30.0)),
            "lfo_amount": float_range(0.05, 0.25, limits=(0.0, 1.0)),

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
}


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

    # 1. Cargar la receta base del arquetipo
    patch = ARCHETYPES[archetype_name]
    final_params = {k: list(v) for k, v in patch["params"].items()} # Copiamos los rangos
    archetype = ARCHETYPES[archetype_name]
    specs = _merge_param_specs(DEFAULT_PARAM_SPECS, archetype.get("params", {}))

    # 2. Aplicar los modificadores a los rangos
    for mod_name in modifier_names:
        _apply_modifier(specs, MODIFIERS[mod_name])

    result: Dict[str, Union[float, int, bool, str]] = {}
    for param, spec in specs.items():
        result[param] = _generate_value(param, spec)

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