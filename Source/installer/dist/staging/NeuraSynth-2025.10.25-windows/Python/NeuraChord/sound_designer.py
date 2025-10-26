import random
import json
import os
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
    "slope.wav",
    "pwm.wav",
    "layered.wav",
    "pendulumphase.wav",
    "squeezy_keys.wav",
    "rmi_piano.wav",
    "zionoid_pad.wav",
    "marbles_bell.wav",
    "bells_and_crickets.wav",
    "bass_mix_destroyer.wav",
    "bass_sin_er.wav",
    "bass_sine_additive_fold.wav",
    "bass_yab.wav",
    "simple_bass.wav",
    "lead_voice.wav",
    "bell_picking_a_string.wav",
    "analog_substation_harmony_ak.wav",
    "analog_mix_destroyer_ak.wav",
    "analog_wave_bass.wav",
    "analog_stacked_saws_pad.wav",
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
    "master_gain": constant(0.70),
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
    "osc1_gain": float_range(0.6, 0.80, limits=(0.0, 0.80)),
    "osc2_gain": float_range(0.3, 0.7, limits=(0.0, 0.80)),
    "osc3_gain": float_range(0.1, 0.5, limits=(0.0, 0.80)),

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
            "master_drive": float_range(0.3, 0.6, limits=(0.0, 1.0)),
            "master_bright": float_range(0.6, 1.0, limits=(0.0, 1.0)),
            "master_dark": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.45),

            "attack": float_range(0.0, 0.05, limits=(0.0, 5.0)),
            "decay": float_range(0.12, 0.4, limits=(0.0, 5.0)),
            "sustain": float_range(0.75, 1.0, limits=(0.0, 1.0)),
            "release": float_range(0.1, 0.3, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.7, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.4, 0.7, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.0, 0.5, limits=(0.0, 0.80)),

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
            "osc1": ["saw.wav", "square.wav", "slope.wav", "squeezy_keys.wav", "lead_voice.wav"],
            "osc2": ["saw.wav", "square.wav", "pulse.wav", "slope.wav", "keys_saw.wav", "lead_voice.wav", "pwm.wav"],
            "osc3": ["senHarmonic.wav", "triangle.wav", "slope.wav"],
        },
    },
    "pad": {
        "params": {
            "master_drive": float_range(0.0, 0.25, limits=(0.0, 1.0)),
            "master_dark": float_range(0.1, 0.4, limits=(0.0, 1.0)),
            "master_bright": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.75),

            # Envolvente más controlada: sigue siendo suave, pero más musical.
            "attack": float_range(0.5, 2.0, limits=(0.0, 5.0)),
            "decay": float_range(1.0, 3.0, limits=(0.0, 5.0)),
            "sustain": float_range(0.6, 0.9, limits=(0.0, 1.0)),
            "release": float_range(1.5, 3.5, limits=(0.0, 5.0)),

            # Ganancias limitadas y equilibradas
            "osc1_gain": float_range(0.7, 0.85, limits=(0.0, 0.85)),
            "osc2_gain": float_range(0.6, 0.8, limits=(0.0, 0.85)),
            "osc3_gain": float_range(0.5, 0.75, limits=(0.0, 0.85)),

            # Unísono rico pero estable
            "osc1_unison_voices": int_range(4, 9, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.08, 0.2, limits=(0.0, 1.0)), # Detune reducido
            "osc1_unison_spread": float_range(1.0, 2.0, limits=(0.0, 2.5)),

            # Filtro más brillante y con menos resonancia para evitar sonidos "inquietantes"
            "filter_cutoff_hz": float_range(1500.0, 8000.0, limits=(20.0, 20000.0)),
            "filter_q": float_range(0.2, 0.45, limits=(0.1, 10.0)),
            "filter_env_amt": float_range(0.1, 0.35, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.7),

            # La modulación será controlada por la función _apply_modulation_scenario
            # para priorizar barridos lentos y sutiles.
            "fm_amount": float_range(-0.1, 0.1, limits=(-1.0, 1.0)),
            
            # Efectos generosos para un sonido espacioso
            "reverb_wet_level": float_range(0.25, 0.5, limits=(0.0, 1.0)),
            "reverb_room_size": float_range(0.7, 0.95, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.2, 0.4, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            # Ondas ricas en armónicos pero suaves
            "osc1": ["layered.wav", "saw.wav", "senHarmonic.wav", "zionoid_pad.wav", "pwm.wav", "analog_stacked_saws_pad.wav",],
            "osc2": ["pendulumphase.wav", "triangle.wav", "keys_organ.wav", "lead_voice.wav", "pwm.wav", "analog_stacked_saws_pad.wav",],
            "osc3": ["saw.wav", "sen.wav", "layered.wav", "pwm.wav"],
        },
    },
    "bass": {
        "params": {
            "master_drive": float_range(0.4, 0.8, limits=(0.0, 1.0)),
            "master_dark": float_range(0.4, 0.8, limits=(0.0, 1.0)),
            "master_bright": float_range(0.0, 0.3, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.15),

            "attack": float_range(0.0, 0.04, limits=(0.0, 5.0)),
            "decay": float_range(0.15, 0.5, limits=(0.0, 5.0)),
            "sustain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "release": float_range(0.1, 0.25, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.8, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.4, 0.75, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.0, 0.5, limits=(0.0, 0.80)),

            "osc1_unison_voices": int_range(1, 2, limits=(1, 16)),
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
            "osc1": ["sen.wav", "square.wav", "slope.wav", "bass_mix_destroyer.wav", 
                     "bass_sin_er.wav", "bass_sine_additive_fold.wav", "simple_bass.wav",
                     "bass_yab.wav", "pwm.wav", "analog_wave_bass.wav",],

            "osc2": ["saw.wav", "square.wav", "slope.wav", "bass_mix_destroyer.wav", 
                     "bass_sin_er.wav", "bass_sine_additive_fold.wav", "simple_bass.wav",
                     "bass_yab.wav", "pwm.wav", "analog_wave_bass.wav",],

            "osc3": ["saw.wav", "square.wav", "slope.wav" "pwm.wav"],
        },
    },
    "pluck": {
        "params": {
            "master_drive": float_range(0.1, 0.4, limits=(0.0, 1.0)),
            "master_bright": float_range(0.5, 0.8, limits=(0.0, 1.0)),
            "master_dark": float_range(0.0, 0.3, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.5),

            "attack": float_range(0.0, 0.015, limits=(0.0, 5.0)),
            "decay": float_range(0.08, 0.3, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.15, limits=(0.0, 1.0)),
            "release": float_range(0.15, 0.45, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.7, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.4, 0.7, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.0, 0.3, limits=(0.0, 0.80)),

            "osc1_unison_voices": int_range(1, 3, limits=(1, 16)),
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
           "osc1": ["sen.wav", "square.wav", "rmi_piano.wav", "marbles_bell.wav", 
                    "bells_and_crickets.wav", "bell_picking_a_string.wav"],
            "osc2": ["saw.wav", "square.wav", "triangle.wav", "keys_saw.wav", "bell_picking_a_string.wav", "pwm.wav"],
            "osc3": ["triangle.wav", "senHarmonic.wav", "pwm.wav"],
        },
    },
    "keys": {
        "params": {
            "master_drive": float_range(0.05, 0.35, limits=(0.0, 1.0)),
            "master_bright": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.55),

            # Envolvente tipo "pluck": ataque rápido, sustain bajo.
            "attack": float_range(0.0, 0.04, limits=(0.0, 5.0)),
            "decay": float_range(0.3, 0.8, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.4, limits=(0.0, 1.0)), # Sustain bajo es clave
            "release": float_range(0.2, 0.6, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.7, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.4, 0.75, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.0, 0.5, limits=(0.0, 0.80)),

            "osc1_unison_voices": int_range(1, 3, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.08, 0.2, limits=(0.0, 1.0)),

            "filter_cutoff_hz": float_range(800.0, 7000.0, limits=(20.0, 20000.0)),
            
            # ¡CLAVE! Mucha modulación de envolvente en el filtro para el "pluck"
            "filter_env_amt": float_range(0.4, 0.85, limits=(-1.0, 1.0)),
            "filter_keytrack": bool_prob(0.6),

            "fm_amount": float_range(-0.1, 0.2, limits=(-1.0, 1.0)),

            "reverb_wet_level": float_range(0.15, 0.3, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.15, 0.35, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            # Ondas clásicas para sonidos de teclado de sinte
            "osc1": ["rmi_piano.wav", "squeezy_keys.wav", "keys_saw.wav"],
            "osc2": ["squeezy_keys.wav", "sen.wav", "saw.wav", "rmi_piano.wav", "pwm.wav"],
            "osc3": ["triangle.wav", "sen.wav", "pwm.wav"],
        },
    },
    "poly_synth": {
        "params": {
            "master_drive": float_range(0.05, 0.3, limits=(0.0, 1.0)),
            "master_dark": float_range(0.2, 0.5, limits=(0.0, 1.0)),
            "master_bright": float_range(0.35, 0.65, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.55),

            "attack": float_range(0.1, 0.45, limits=(0.0, 5.0)),
            "decay": float_range(0.35, 1.1, limits=(0.0, 5.0)),
            "sustain": float_range(0.4, 0.7, limits=(0.0, 1.0)),
            "release": float_range(0.45, 1.2, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.7, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.5, 0.7, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.35, 0.65, limits=(0.0, 0.80)),

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
            "osc1": ["saw.wav", "square.wav", "triangle.wav", "pwm.wav", "analog_substation_harmony_ak.wav",
                     "analog_mix_destroyer_ak.wav", "analog_wave_bass.wav", "analog_stacked_saws_pad.wav"],
            "osc2": ["saw.wav", "triangle.wav", "pulse.wav", "lead_voice.wav", "pwm.wav", "analog_substation_harmony_ak.wav",
                     "analog_mix_destroyer_ak.wav", "analog_wave_bass.wav", "analog_stacked_saws_pad.wav"],
            "osc3": ["triangle.wav", "sen.wav", "senHarmonic.wav", "pwm.wav"],
        },
    },
    "string_brass": {
        "params": {
            "master_drive": float_range(0.1, 0.35, limits=(0.0, 1.0)),
            "master_dark": float_range(0.25, 0.55, limits=(0.0, 1.0)),
            "master_bright": float_range(0.35, 0.7, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.65),

            "attack": float_range(0.25, 1.1, limits=(0.0, 5.0)),
            "decay": float_range(0.6, 1.6, limits=(0.0, 5.0)),
            "sustain": float_range(0.55, 0.85, limits=(0.0, 1.0)),
            "release": float_range(0.8, 1.8, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.75, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.55, 0.70, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.25, 0.55, limits=(0.0, 0.80)),

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
    "fx": {
        "params": {
            "master_drive": float_range(0.1, 0.5, limits=(0.0, 1.0)),
            "master_dark": float_range(0.1, 0.5, limits=(0.0, 1.0)),
            "master_bright": float_range(0.3, 0.7, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.55),

            "attack": float_range(0.15, 4.0, limits=(0.0, 5.0)),
            "decay": float_range(0.4, 3.0, limits=(0.0, 5.0)),
            "sustain": float_range(0.1, 0.7, limits=(0.0, 1.0)),
            "release": float_range(0.3, 4.5, limits=(0.0, 5.0)),

            "osc1_gain": float_range(0.5, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.3, 0.7, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.2, 0.6, limits=(0.0, 0.80)),

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
            "master_drive": float_range(0.0, 0.2, limits=(0.0, 1.0)),
            "master_bright": float_range(0.45, 0.75, limits=(0.0, 1.0)),
            "master_chorus_on": bool_prob(0.35),

            # Envolvente de campana: ataque instantáneo, sin sustain, caída media.
            "attack": float_range(0.0, 0.01, limits=(0.0, 5.0)),
            "decay": float_range(0.8, 1.5, limits=(0.0, 5.0)),
            "sustain": float_range(0.0, 0.0, limits=(0.0, 1.0)), # Sustain CERO es clave
            "release": float_range(0.8, 2.0, limits=(0.0, 5.0)),

            # Ganancias limitadas
            "osc1_gain": float_range(0.7, 0.80, limits=(0.0, 0.80)),
            "osc2_gain": float_range(0.5, 0.7, limits=(0.0, 0.80)),
            "osc3_gain": float_range(0.3, 0.5, limits=(0.0, 0.80)),

            "osc1_unison_voices": int_range(1, 2, limits=(1, 16)),
            "osc1_unison_detune": float_range(0.05, 0.15, limits=(0.0, 1.0)),

            "filter_cutoff_hz": float_range(2000.0, 14000.0, limits=(20.0, 20000.0)),

            # FM muy sutil para brillo, no para el tono metálico
            "fm_amount": float_range(-0.15, 0.25, limits=(-1.0, 1.0)),

            "reverb_wet_level": float_range(0.2, 0.45, limits=(0.0, 1.0)),
            "delay_wet_level": float_range(0.2, 0.4, limits=(0.0, 1.0)),
        },
        "wavetable_options": {
            # Base sinusoidal para un sonido limpio de campana
            "osc1": ["sen.wav", "marbles_bell.wav",
                     "bells_and_crickets.wav", "bell_picking_a_string.wav"],
            "osc2": ["senHarmonic.wav", "triangle.wav", "bell_picking_a_string.wav"],
            "osc3": ["sen.wav"],
        },
    },
}

# Define la probabilidad de usar 1, 2 o 3 osciladores para cada arquetipo.
# Formato: [prob_1_osc, prob_2_osc, prob_3_osc]
OSCILLATOR_COUNT_PROFILES: Dict[str, List[float]] = {
    # Bajos y Kicks: simples y potentes
    "bass": [0.4, 0.5, 0.1],
    "kick": [0.6, 0.3, 0.1],

    # Sonidos percusivos y definidos
    "pluck": [0.1, 0.7, 0.2],
    "keys":  [0.0, 0.6, 0.4],
    "bell":  [0.0, 0.5, 0.5],
    "mallet": [0.1, 0.7, 0.2],
    "snare": [0.0, 0.8, 0.2], # Generalmente 2 (tono + ruido)
    "hihat": [0.0, 0.7, 0.3], # Tono + ruido

    # Sonidos melódicos y principales
    "lead": [0.1, 0.5, 0.4],

    # Sonidos complejos y densos
    "pad": [0.0, 0.3, 0.7],
    "poly_synth": [0.0, 0.4, 0.6],
    "string_brass": [0.0, 0.2, 0.8],
    "string_synth": [0.0, 0.2, 0.8],
    "brass_synth": [0.0, 0.3, 0.7],

    # FX: puede ser cualquier cosa
    "fx": [0.2, 0.4, 0.4],
    
    # Perfil por defecto si no se encuentra uno específico
    "default": [0.1, 0.5, 0.4],
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
    "vintage": {
        # Sonido más oscuro y cálido
        "master_bright": (0.6, 0.8),
        "master_dark": (1.1, 1.4),
        "master_drive": (1.2, 1.6),
        # Simula la inestabilidad de tono de los circuitos analógicos
        "lfo_speed_hz": float_range(4.5, 6.5, limits=(0.0, 30.0)),
        "lfo_amount": float_range(0.01, 0.05, limits=(0.0, 1.0)),
    },
    "modern": {
        # Sonido nítido y brillante
        "master_bright": (1.2, 1.5),
        "master_dark": (0.7, 0.9),
        # Promueve el uso de armónicos complejos y digitales
        "fm_amount": (1.5, 2.5),
        # Envolvente más rápida y "punchy"
        "attack": (0.5, 0.8),
    },
    "lofi": {
        # Recorta drásticamente los agudos y graves
        "filter_cutoff_hz": (0.2, 0.5),
        "master_bright": float_range(0.0, 0.2, limits=(0.0, 1.0)),
        "master_dark": float_range(0.7, 1.0, limits=(0.0, 1.0)),
        # Simula el "wow & flutter" de una cinta gastada
        "lfo_speed_hz": float_range(0.1, 0.8, limits=(0.0, 30.0)),
        "lfo_amount": float_range(0.03, 0.09, limits=(0.0, 1.0)),
        # Un toque de ruido de fondo
        "osc3_wavetable": choice(["whitenoise.wav"]),
        "osc3_gain": float_range(0.01, 0.08, limits=(0.0, 0.85)),
    }
}

# ==============================================================================
# ==                                  LÓGICA                                  ==
# ==============================================================================

# --- NUEVAS CONSTANTES Y FUNCIONES DE APRENDIZAJE ---
LEARNED_SOUNDS_PATH = os.path.join(os.path.dirname(__file__), 'learned_sounds.json')
PROB_USE_LEARNED = 0.5 # 50% de probabilidad de usar un sonido aprendido como base

def load_learned_sounds():
    """Carga los ejemplares guardados desde el archivo JSON."""
    if not os.path.exists(LEARNED_SOUNDS_PATH):
        return []
    try:
        with open(LEARNED_SOUNDS_PATH, 'r') as f:
            # Añadimos una comprobación para evitar errores con archivos vacíos
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, IOError):
        return []

def find_matching_exemplar(tags: list, learned_sounds: list):
    """
    Encuentra el mejor "ejemplar" (sonido guardado) que coincida con los tags del prompt.
    """
    best_match = None
    highest_score = -1  # Empezamos en -1 para que cualquier coincidencia sea mejor
    
    if not tags:
        return None
        
    archetype = tags[0]
    modifiers = set(tags[1:])

    for exemplar in learned_sounds:
        # El arquetipo (lead, pad, etc.) debe coincidir perfectamente
        if not exemplar['tags'] or exemplar['tags'][0] != archetype:
            continue

        exemplar_modifiers = set(exemplar['tags'][1:])
        
        # Puntuación: Damos 2 puntos por cada modificador que coincide
        # y restamos 1 por cada modificador que no coincide.
        # Esto prefiere ejemplares que son más específicos.
        score = len(modifiers.intersection(exemplar_modifiers)) * 2
        score -= len(modifiers.symmetric_difference(exemplar_modifiers))
        
        if score > highest_score:
            highest_score = score
            best_match = exemplar
            
    return best_match

def mutate_patch(patch: dict):
    """
    Toma un patch existente y aplica pequeñas variaciones aleatorias a sus valores
    para crear un sonido similar pero no idéntico.
    """
    mutated = patch.copy()
    for param, value in mutated.items():
        if isinstance(value, float):
            # Aplica una variación de hasta +/- 15% al valor actual
            mutation_factor = 1.0 + random.uniform(-0.15, 0.15)
            mutated[param] = value * mutation_factor
        elif isinstance(value, int) and param != "osc1_unison_voices": # No mutamos las voces
             # Para enteros, la variación es más pequeña
             mutation_factor = 1.0 + random.uniform(-0.10, 0.10)
             mutated[param] = int(round(value * mutation_factor))

    return mutated

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
        (2, 0.05),
        (6, 0.04),
    ],
}


FINE_SPAN_BY_ARCHETYPE: Dict[str, float] = {
    "bass": 1.8,
    "kick": 1.0,
    "snare": 1.5,
    "hihat": 1.5,
    "lead": 3.0,
    "pad": 4.0,
    "poly_synth": 3.8,
    "string_synth": 4.2,
    "string_brass": 4.0,
    "brass_synth": 3.5,
    "poly": 3.5,
    "keys": 2.8,
    "pluck": 2.5,
    "bell": 4.5,
    "mallet": 3.0,
    "fx": 8.0,
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


def _choose_interval(archetype: str, osc_index: int, specs: Dict[str, Dict], used: List[int], context_interval: int = None) -> int:
    profile = INTERVAL_PROFILES.get(archetype, DEFAULT_INTERVAL_PROFILE)
    candidates: List[int] = []
    weights: List[float] = []

    # Diccionario de intervalos "sugeridos" para formar acordes
    chord_tones = {
        7: [3, 4],      # Si el contexto es una 5a, sugiere una 3a
        5: [3, 4],      # Si el contexto es una 4a, sugiere una 3a
        3: [7, -5],     # Si el contexto es una 3a menor, sugiere 5a o 4a
        4: [7, -5],     # Si el contexto es una 3a Mayor, sugiere 5a o 4a
    }

    for interval, weight in profile:
        if not _interval_allowed_for_osc(interval, osc_index, specs):
            continue

        # Penalización si el intervalo ya se usó
        penalty = 0.4 if any(abs(interval - other) < 0.1 for other in used) else 1.0
        
        # Aumento de probabilidad si el intervalo forma un acorde con el contexto
        boost = 1.0
        if context_interval in chord_tones and interval in chord_tones[context_interval]:
            boost = 2.5 # Hacemos que sea mucho más probable

        candidates.append(interval)
        weights.append(weight * penalty * boost)

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


def _shape_fine_offsets(
    result: Dict,
    specs: Dict[str, Dict],
    active_oscillators: List[int],
    archetype: str,
):
    """
    Modela la desafinación (fine) de forma inteligente, respetando el intervalo armónico
    de cada oscilador para mantener la consonancia.
    """
    if not active_oscillators:
        return

    # 1. Obtenemos el "carácter" base de desafinación y el factor de unison
    base_span = FINE_SPAN_BY_ARCHETYPE.get(archetype, 4.0)
    unison_voices = result.get("osc1_unison_voices", 1)
    unison_factor = 1.0 + ((unison_voices - 1) / 15.0) * 0.5
    final_span = base_span * unison_factor

    # 2. El oscilador raíz se mantiene relativamente estable
    root_index = active_oscillators[0]
    root_spec = specs.get(f"osc{root_index}_fine")
    if root_spec:
        center_variation = random.uniform(-final_span * 0.1, final_span * 0.1)
        _set_numeric_param(result, specs, f"osc{root_index}_fine", center_variation)

    if len(active_oscillators) == 1:
        return

    # 3. Para los demás osciladores, ajustamos la desafinación según su intervalo
    for osc_index in active_oscillators[1:]:
        spec = specs.get(f"osc{osc_index}_fine")
        if not spec:
            continue

        intervalo_total = result.get(f"osc{osc_index}_octave", 0) * 12 + result.get(f"osc{osc_index}_pitch", 0)
        
        # Modificador basado en la consonancia del intervalo
        consonance_factor = 1.0
        abs_interval = abs(intervalo_total) % 12
        
        if abs_interval == 0: # Octava/Unísono
            consonance_factor = 0.25 # Muy poca desafinación
        elif abs_interval in [7, 5]: # Quinta/Cuarta
            consonance_factor = 0.5  # Poca desafinación
        # Para terceras, sextas, etc., se usa el factor completo (1.0)

        # Calculamos el rango de desafinación permitido para ESTE oscilador
        allowed_span = final_span * consonance_factor
        
        # Asignamos un valor dentro de ese rango musicalmente seguro
        fine_value = random.uniform(-allowed_span, allowed_span)
        _set_numeric_param(result, specs, f"osc{osc_index}_fine", fine_value)


def _ensure_layered_gains(result: Dict, specs: Dict[str, Dict], active_oscillators: List[int], archetype: str):
    """
    Modela la relación de ganancia entre los osciladores de forma inteligente,
    basándose en su rol armónico y el arquetipo del sonido.
    """
    if len(active_oscillators) <= 1:
        return

    osc_data = {}
    for i in active_oscillators:
        osc_data[i] = {
            "gain": result.get(f"osc{i}_gain", 0.0),
            "semitones": result.get(f"osc{i}_octave", 0) * 12 + result.get(f"osc{i}_pitch", 0),
            "wavetable": result.get(f"osc{i}_wavetable", "None"),
        }
    
    # 1. Asegurar que el OSC1 (el principal) tenga una ganancia sólida.
    primary_osc_index = active_oscillators[0]
    primary_gain_spec = specs.get(f"osc{primary_osc_index}_gain")
    if primary_gain_spec:
        min_gain = primary_gain_spec["range"][0] + (primary_gain_spec["range"][1] - primary_gain_spec["range"][0]) * 0.6
        if osc_data[primary_osc_index]["gain"] < min_gain:
             osc_data[primary_osc_index]["gain"] = random.uniform(min_gain, primary_gain_spec["range"][1])
    
    primary_gain = osc_data[primary_osc_index]["gain"]
    primary_semitones = osc_data[primary_osc_index].get("semitones", 0)

    # 2. Ajustar los osciladores secundarios en base a su rol
    for i in active_oscillators[1:]:
        secondary_spec = specs.get(f"osc{i}_gain")
        if not secondary_spec:
            continue

        target_ratio = 0.65  # Ratio de volumen por defecto para un oscilador de acompañamiento

        # Lógica para SUB-BAJOS
        if osc_data[i]["semitones"] <= primary_semitones - 12:
            target_ratio = random.uniform(0.55, 0.75) # Los subs son potentes pero no deben opacar
            if archetype == "bass":
                target_ratio *= 1.1 # En un bajo, el sub es más importante

        # Lógica para ARMÓNICOS SUPERIORES
        elif osc_data[i]["semitones"] > primary_semitones + 7:
            target_ratio = random.uniform(0.45, 0.6) # Los armónicos altos son más sutiles

        # Lógica para TEXTURA / RUIDO
        if osc_data[i]["wavetable"] == "whitenoise.wav":
            target_ratio = random.uniform(0.05, 0.25) # El ruido es solo para añadir textura

        # Para PADS, los osciladores pueden tener volúmenes más parecidos
        if archetype in ["pad", "string_synth"]:
            target_ratio *= 1.2

        # Calculamos la ganancia final y la aplicamos
        max_gain = primary_gain * target_ratio
        
        # Le damos un poco de aleatoriedad para que no suene siempre igual
        final_gain = random.uniform(max_gain * 0.8, max_gain)
        
        # Nos aseguramos de no salirnos de los límites definidos en el arquetipo
        osc_data[i]["gain"] = max(secondary_spec["range"][0], min(final_gain, secondary_spec["range"][1]))

    # 3. Finalmente, actualizamos el diccionario 'result' con las nuevas ganancias calculadas
    for i in active_oscillators:
        result[f"osc{i}_gain"] = osc_data[i]["gain"]


def _tame_master_drive(result: Dict, specs: Dict[str, Dict]):
    key = "master_drive"
    if key not in result or key not in specs:
        return

    spec = specs[key]
    drive = result.get(key, 0.0)
    low, _ = _effective_bounds(spec)
    subtle_drive = low + (drive - low) * 0.45
    _set_numeric_param(result, specs, key, subtle_drive)

def _apply_modulation_scenario(result: Dict, specs: Dict[str, Dict], archetype: str):
    """
    Elige y aplica un "escenario de modulación" para dar vida y movimiento al sonido.
    """
    # Escenarios posibles y sus probabilidades
    scenarios = ["static", "slow_sweep", "classic_vibrato", "rhythmic_pulse"]
    weights = [0.40, 0.32, 0.18, 0.10]  # Un poco menos de probabilidad de modulaciones intensas

    is_pad_like = archetype in ["pad", "string_synth"]
    if is_pad_like:
        # Los pads deben mantenerse más estables, con menor probabilidad de modulaciones fuertes
        weights = [0.48, 0.34, 0.14, 0.04]

    # Los bajos y sonidos percusivos a menudo no necesitan LFOs complejos
    if archetype in ["bass", "kick", "pluck", "keys", "snare"]:
        weights = [0.6, 0.1, 0.2, 0.1] # Más chance de ser estático

    chosen_scenario = random.choices(scenarios, weights=weights, k=1)[0]

    # --- Aplicamos la receta del escenario elegido ---

    if chosen_scenario == "static":
        result["lfo_amount"] = 0.0
        result["lfo_speed_hz"] = 0.0
        # También podemos reducir la modulación de la envolvente del filtro para un sonido más plano
        if "filter_env_amt" in result and random.random() < 0.5:
            result["filter_env_amt"] *= 0.3

    elif chosen_scenario == "slow_sweep":
        # LFO lento para pads y atmósferas, pero con un amount más contenido
        _set_numeric_param(result, specs, "lfo_speed_hz", random.uniform(0.05, 0.25))

        amount_min, amount_max = (0.06, 0.22)
        if is_pad_like:
            amount_min, amount_max = (0.04, 0.14)
        _set_numeric_param(result, specs, "lfo_amount", random.uniform(amount_min, amount_max))
        # Aseguramos que el filtro no esté completamente abierto para que el LFO tenga espacio para actuar
        if "filter_cutoff_hz" in result and result["filter_cutoff_hz"] > 10000:
             _set_numeric_param(result, specs, "filter_cutoff_hz", random.uniform(4000, 9000))

    elif chosen_scenario == "classic_vibrato":
        # LFO rápido y sutil para un vibrato musical
        _set_numeric_param(result, specs, "lfo_speed_hz", random.uniform(4.5, 7.0))
        vibrato_min, vibrato_max = (0.015, 0.06)
        if is_pad_like:
            vibrato_min, vibrato_max = (0.01, 0.045)
        _set_numeric_param(result, specs, "lfo_amount", random.uniform(vibrato_min, vibrato_max))

    elif chosen_scenario == "rhythmic_pulse":
        # LFO a velocidad media para crear wobbles o pulsos
       # LFO a velocidad media para crear wobbles o pulsos, manteniendo un amount más moderado
        _set_numeric_param(result, specs, "lfo_speed_hz", random.uniform(0.5, 3.5))

        pulse_min, pulse_max = (0.28, 0.65)
        if is_pad_like:
            pulse_min, pulse_max = (0.18, 0.42)
        _set_numeric_param(result, specs, "lfo_amount", random.uniform(pulse_min, pulse_max))
        _set_numeric_param(result, specs, "lfo_amount", random.uniform(0.4, 0.85))
        # Este efecto necesita que la envolvente del filtro no sea demasiado agresiva
        if "filter_env_amt" in result:
            result["filter_env_amt"] *= 0.5

def _shape_unison(result: Dict, specs: Dict[str, Dict], archetype: str):
    """
    Ajusta inteligentemente el detune del unísono basándose en el número de voces
    para mantener la estabilidad y el carácter musical del sonido.
    """
    if "osc1_unison_voices" not in result or "osc1_unison_detune" not in specs:
        return

    num_voices = result["osc1_unison_voices"]
    spec = specs["osc1_unison_detune"]

    if num_voices <= 1:
        # Si no hay unísono, no hay detune.
        result["osc1_unison_detune"] = 0.0
        return

    # A mayor número de voces, menor debe ser el detune para evitar disonancia.
    # Esta fórmula reduce progresivamente el detune máximo permitido.
    max_detune_factor = 1.0 / (1.0 + (num_voices - 2) * 0.25)
    
    # El rango original del arquetipo
    low, high = spec.get("range", (0.0, 1.0))
    
    # Calculamos el nuevo rango "inteligente"
    new_high = low + (high - low) * max_detune_factor
    new_low = low * max_detune_factor # También reducimos el mínimo

    # Generamos un valor final dentro de este rango seguro y musical
    final_detune = random.uniform(new_low, new_high)
    _set_numeric_param(result, specs, "osc1_unison_detune", final_detune)

def _shape_effects(result: Dict, specs: Dict[str, Dict], archetype: str):
    """
    Ajusta los efectos (Reverb y Delay) de forma inteligente basándose en el
    arquetipo del sonido para darle el espacio y la dimensión correctos.
    """
    # Perfil de efectos por defecto
    delay_wet = random.uniform(0.15, 0.35)
    reverb_wet = random.uniform(0.1, 0.3)
    reverb_decay = random.uniform(0.4, 0.8)
    reverb_size = random.uniform(0.5, 0.8)
    delay_hp = random.uniform(0.05, 0.35)

    # --- Recetas de Efectos por Arquetipo ---

    if archetype in ["pluck", "keys", "bell", "mallet"]:
        # Sonidos percusivos: Delay protagonista, Reverb corta para dar espacio.
        delay_wet = random.uniform(0.25, 0.45)
        reverb_wet = random.uniform(0.15, 0.30)
        reverb_decay = random.uniform(0.2, 0.5)
        reverb_size = random.uniform(0.3, 0.6)
        # Filtramos los graves del delay para no enturbiar la mezcla
        delay_hp = random.uniform(0.2, 0.5)

    elif archetype in ["pad", "string_synth", "string_brass"]:
        # Sonidos atmosféricos: Reverb enorme, Delay como una sombra sutil.
        reverb_wet = random.uniform(0.3, 0.55)
        reverb_decay = random.uniform(0.7, 0.95)
        reverb_size = random.uniform(0.75, 1.0)
        delay_wet = random.uniform(0.1, 0.25)
        # Filtramos los agudos del delay para que no distraiga
        _set_numeric_param(result, specs, "delay_lp_freq", random.uniform(0.4, 0.7))

    elif archetype in ["bass", "kick"]:
        # Sonidos graves: Prácticamente sin efectos para mantener la pegada y claridad.
        delay_wet = random.uniform(0.0, 0.05)
        reverb_wet = random.uniform(0.0, 0.1)

    # Aplicamos los valores calculados a los parámetros del resultado
    _set_numeric_param(result, specs, "delay_wet_level", delay_wet)
    _set_numeric_param(result, specs, "reverb_wet_level", reverb_wet)
    _set_numeric_param(result, specs, "reverb_decay", reverb_decay)
    _set_numeric_param(result, specs, "reverb_room_size", reverb_size)
    _set_numeric_param(result, specs, "delay_hp_freq", delay_hp)

def _apply_expert_correlations(result: Dict, specs: Dict[str, Dict], archetype: str):
    """
    Aplica reglas de experto finales para asegurar la coherencia entre parámetros,
    imitando las decisiones de un diseñador de sonido humano.
    """
    # --- 1. Correlación Envolvente-Filtro (Sonidos Plucky) ---
    filter_env = result.get("filter_env_amt", 0.0)
    if filter_env > 0.6 and "release" in result: # Si el filtro es muy percusivo...
        # ...acortamos la cola del sonido para que sea más definido.
        current_release = result["release"]
        result["release"] = max(0.05, min(current_release, random.uniform(0.1, 0.5)))

    # --- 2. Correlación Filtro-Resonancia (Evitar Picos Agresivos) ---
    filter_q = result.get("filter_q", 0.1)
    if filter_q > 0.7: # Si la resonancia es alta...
        # ...reducimos el drive y la ganancia para no distorsionar.
        if "master_drive" in result:
            result["master_drive"] *= 0.5
        if "osc1_gain" in result:
            result["osc1_gain"] *= 0.85

    # --- 3. Correlación Complejidad-Unísono (Evitar Sonidos "Fangosos") ---
    active_oscillators = [
        i for i in (1, 2, 3) if result.get(f"osc{i}_gain", 0.0) > 0.0 and result.get(f"osc{i}_wavetable") != "None"
    ]
    if len(active_oscillators) == 3 and "osc1_unison_voices" in result: # Si los 3 osciladores están activos...
        # ...reducimos un poco las voces del unísono para mantener la claridad.
        current_voices = result["osc1_unison_voices"]
        result["osc1_unison_voices"] = max(1, int(current_voices * 0.7))

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
        preferred = [0, 0, 0, 0, 0, 0, 0, 0, 12, -12, 7]
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
        STABILITY_CHANCE = 0.25  # 25% de probabilidad de elegir un intervalo perfectamente estable

        # --- Lógica para OSC2 ---
        osc2_index = active_oscillators[1]
        if random.random() < STABILITY_CHANCE and archetype not in ["fx", "bell"]:
            # FORZAMOS ESTABILIDAD: Octava o unísono, sin desafinación.
            stable_interval = random.choice([0, 12, -12])
            _assign_interval_to_osc(result, specs, osc2_index, stable_interval)
            _set_numeric_param(result, specs, f"osc{osc2_index}_fine", 0.0)
            interval_osc2 = stable_interval
        else:
            # Comportamiento normal: buscar armonía.
            interval_osc2 = _choose_interval(archetype, osc2_index, specs, used_intervals)
            _assign_interval_to_osc(result, specs, osc2_index, interval_osc2)
        used_intervals.append(interval_osc2)

        # --- Lógica para OSC3 (y siguientes, si los hubiera) ---
        if len(active_oscillators) >= 3:
            context_interval = interval_osc2
            for osc_index in active_oscillators[2:]:
                if random.random() < STABILITY_CHANCE and archetype not in ["fx"]:
                    stable_interval = random.choice([-12, -24, 0, 12]) # Priorizamos subs estables
                    _assign_interval_to_osc(result, specs, osc_index, stable_interval)
                    _set_numeric_param(result, specs, f"osc{osc_index}_fine", 0.0)
                else:
                    interval = _choose_interval(archetype, osc_index, specs, used_intervals, context_interval=context_interval)
                    used_intervals.append(interval)
                    _assign_interval_to_osc(result, specs, osc_index, interval)

    _shape_fine_offsets(result, specs, active_oscillators, archetype)
    _ensure_layered_gains(result, specs, active_oscillators, archetype)
    _shape_panorama(result, specs, active_oscillators, archetype)

def generate_synth_patch(tags: List[str]) -> Dict:
    # --- 1. LÓGICA DE APRENDIZAJE ---
    # Con una probabilidad definida, intentamos usar un sonido aprendido
    if random.random() < PROB_USE_LEARNED:
        learned_sounds = load_learned_sounds()
        if learned_sounds:
            exemplar = find_matching_exemplar(tags, learned_sounds)
            if exemplar:
                print("INFO (Sound Designer): Usando ejemplar aprendido como base para generar un nuevo sonido.")
                # Creamos una 'mutación' del ejemplar para generar variedad
                mutated_patch = mutate_patch(exemplar['patch'])
                
                # Nos aseguramos de que el patch mutado siga respetando los límites
                # definidos en los arquetipos para no generar valores inválidos.
                archetype_name_from_tags = tags[0]
                base_archetype = ARCHETYPES.get(archetype_name_from_tags, {})
                specs_for_clamping = _merge_param_specs(DEFAULT_PARAM_SPECS, base_archetype.get('params', {}))
                
                final_patch = {}
                for param, value in mutated_patch.items():
                    if param in specs_for_clamping and isinstance(value, (int, float)):
                        spec = specs_for_clamping[param]
                        final_patch[param] = _clamp_to_spec(value, spec)
                    else:
                        # Si no es numérico (ej. wavetable), lo pasamos tal cual
                        final_patch[param] = value
                
                return final_patch

    # --- 2. GENERACIÓN NORMAL (si no se usó un ejemplar) ---
    print("INFO (Sound Designer): Generando nuevo sonido desde cero usando las reglas base.")
    
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

    # --- Decisión de complejidad: ¿Cuántos osciladores usar? ---
    profile = OSCILLATOR_COUNT_PROFILES.get(archetype_name, OSCILLATOR_COUNT_PROFILES["default"])
    num_oscillators = random.choices([1, 2, 3], weights=profile, k=1)[0]

    # Apagamos los osciladores no deseados poniendo su ganancia a 0 Y su wavetable a "None".
    if num_oscillators == 1:
        result["osc2_gain"] = 0.0
        result["osc3_gain"] = 0.0
        result["osc2_wavetable"] = "None"
        result["osc3_wavetable"] = "None"
    elif num_oscillators == 2:
        result["osc3_gain"] = 0.0
        result["osc3_wavetable"] = "None"
    # Si son 3, no hacemos nada y dejamos que la IA los use todos.

    wavetable_choices = archetype.get("wavetable_options", BASE_WAVETABLE_OPTIONS)
    for osc_name in ("osc1", "osc2", "osc3"):
        options = wavetable_choices.get(osc_name, BASE_WAVETABLE_OPTIONS.get(osc_name, []))
        if options:
            result[f"{osc_name}_wavetable"] = random.choice(options)
        else:
            result[f"{osc_name}_wavetable"] = "None"
        
        # Armonizar los osciladores para que suenen bien juntos
        _harmonize_oscillators(result, specs, archetype_name)
        _shape_unison(result, specs, archetype_name)
        _tame_master_drive(result, specs)
        _apply_modulation_scenario(result, specs, archetype_name)
        _shape_effects(result, specs, archetype_name)
        _apply_expert_correlations(result, specs, archetype_name)

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