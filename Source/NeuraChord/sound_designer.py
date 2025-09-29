import random

# Lista de wavetables disponibles en tu carpeta Source/wavetables
# Elige los nombres de archivo exactos.
AVAILABLE_WAVETABLES = [
    "saw.wav",
    "square.wav",
    "pulse.wav",
    "triangle.wav",
    "sen.wav",
    "senHarmonic.wav",
    "whitenoise.wav"
]

# ==============================================================================
# ==                            ARQUETIPOS DE SONIDO                          ==
# ==============================================================================
# Aquí definimos las "recetas" base para cada tipo de sonido.
# Los valores son tuplas (min, max) para permitir la aleatorización.

ARCHETYPES = {
    "lead": {
        "params": {
            "attack": (0.0, 0.05),      # Rápido
            "decay": (0.1, 0.4),       # Corto
            "sustain": (0.8, 1.0),     # Alto
            "release": (0.1, 0.3),     # Corto/Medio
            "osc1_gain": (0.8, 1.0),
            "osc2_gain": (0.5, 0.8),
            "osc3_gain": (0.0, 0.0),   # Apagado por defecto
            "osc1_unison_voices": (3, 5),
            "osc1_unison_detune": (0.3, 0.6), # Moderado
            "filter_cutoff_hz": (2000, 15000), # Abierto
            "filter_q": (0.1, 0.3),          # Baja
            "filter_env_amt": (0.0, 0.1)     # Poca influencia
        },
        "wavetable_options": {
            "osc1": ["saw.wav", "square.wav"],
            "osc2": ["saw.wav", "square.wav"],
            "osc3": []
        }
    },
    "pad": {
        "params": {
            "attack": (0.8, 3.0),      # Lento
            "decay": (1.0, 3.0),
            "sustain": (0.6, 0.9),     # Medio-Alto
            "release": (1.5, 5.0),     # Largo
            "osc1_gain": (0.7, 1.0),
            "osc2_gain": (0.6, 0.9),
            "osc3_gain": (0.3, 0.6),
            "osc1_unison_voices": (5, 8),
            "osc1_unison_detune": (0.1, 0.3), # Ligero
            "osc1_unison_spread": (0.7, 1.0), # Estéreo
            "filter_cutoff_hz": (400, 3000),  # Medio-Bajo
            "filter_q": (0.2, 0.5),
            "filter_env_amt": (0.1, 0.4),     # Abre un poco
            "lfo_speed_hz": (0.1, 0.8),     # Lento
            "lfo_amount": (0.2, 0.6)        # Para mover el filtro
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "triangle.wav"],
            "osc2": ["sen.wav", "triangle.wav", "saw.wav"],
            "osc3": ["saw.wav", "senHarmonic.wav"]
        }
    },
    "bass": {
        "params": {
            "attack": (0.0, 0.03),
            "decay": (0.2, 0.6),
            "sustain": (0.4, 0.7),
            "release": (0.1, 0.3),
            "osc1_gain": (1.0, 1.0),  # Principal
            "osc2_gain": (0.6, 1.0),  # Textura
            "osc3_gain": (0.0, 0.0),
            "osc1_unison_voices": (1, 3), # Pocas voces
            "osc1_unison_detune": (0.0, 0.2),
            "filter_cutoff_hz": (80, 800), # Bajo
            "filter_q": (0.3, 0.7),
            "filter_env_amt": (0.2, 0.6)
        },
        "wavetable_options": {
            "osc1": ["sen.wav", "square.wav"], # Sub o principal
            "osc2": ["saw.wav", "square.wav"], # Textura
            "osc3": []
        }
    },
    "pluck": {
        "params": {
            "attack": (0.0, 0.01),
            "decay": (0.1, 0.4),       # Corto
            "sustain": (0.0, 0.1),     # Muy bajo
            "release": (0.2, 0.5),
            "osc1_gain": (1.0, 1.0),
            "osc2_gain": (0.5, 0.8),
            "osc3_gain": (0.0, 0.0),
            "osc1_unison_voices": (2, 4),
            "osc1_unison_detune": (0.1, 0.4),
            "filter_cutoff_hz": (1000, 8000), # Medio-Alto
            "filter_q": (0.2, 0.5),
            "filter_env_amt": (0.5, 1.0)     # Muy percusivo
        },
        "wavetable_options": {
            "osc1": ["saw.wav", "square.wav", "pulse.wav"],
            "osc2": ["saw.wav", "square.wav"],
            "osc3": []
        }
    },
    # Puedes seguir añadiendo el resto de arquetipos aquí...
}


# ==============================================================================
# ==                           MODIFICADORES SEMÁNTICOS                       ==
# ==============================================================================
# Modifican los rangos del arquetipo base.
# La clave es el nombre del parámetro y el valor es un multiplicador.

MODIFIERS = {
    "bright": {
        "filter_cutoff_hz": (1.5, 2.0), # Aumenta el cutoff
        "filter_q": (1.1, 1.3)
    },
    "dark": {
        "filter_cutoff_hz": (0.2, 0.5)  # Reduce el cutoff
    },
    "warm": {
        "osc1_unison_detune": (1.1, 1.3), # Un poco más de detune
        "lfo_amount": (0.5, 0.8)       # LFO sutil para vibrato
    },
    "soft": {
        "attack": (1.5, 3.0),           # Attack más lento
        "filter_cutoff_hz": (0.8, 1.0)
    },
    "aggressive": {
        "attack": (0.1, 0.5),           # Attack más rápido
        "osc1_unison_detune": (1.2, 1.5),
        "fm_amount": (0.2, 0.5)         # Añade FM
    }
}

# ==============================================================================
# ==                                  LÓGICA                                  ==
# ==============================================================================

def generate_synth_patch(tags: list) -> dict:
    """
    Genera un patch de sintetizador basado en una lista de etiquetas.
    """
    archetype_name = None
    modifier_names = []

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

    # 2. Aplicar los modificadores a los rangos
    for mod_name in modifier_names:
        modifier = MODIFIERS[mod_name]
        for param, multiplier_range in modifier.items():
            if param in final_params:
                multiplier = random.uniform(*multiplier_range)
                final_params[param][0] *= multiplier
                final_params[param][1] *= multiplier

    # 3. Generar valores aleatorios dentro de los rangos finales
    result = {}
    for param, value_range in final_params.items():
        min_val, max_val = min(value_range), max(value_range)
        
        # Si el parámetro espera un entero (como las voces de unison), lo generamos
        if "voices" in param:
            result[param] = random.randint(int(min_val), int(max_val))
        else:
            result[param] = random.uniform(min_val, max_val)

    # 4. Elegir las wavetables
    wavetable_choices = patch["wavetable_options"]
    for osc_name, options in wavetable_choices.items():
        if options:
            result[f"{osc_name}_wavetable"] = random.choice(options)
        else:
            result[f"{osc_name}_wavetable"] = "None" # O el nombre que uses para 'apagado'

    return result