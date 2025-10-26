# Source/NeuraChord/sound_prompt_processor.py

from fuzzywuzzy import process, fuzz
from sound_designer import ARCHETYPES, MODIFIERS

# Pre-calculamos las listas de arquetipos y modificadores una sola vez para eficiencia.
# Estos son los "tags" válidos que nuestro sistema conoce.
VALID_ARCHETYPES = list(ARCHETYPES.keys())
VALID_MODIFIERS = list(MODIFIERS.keys())

# Umbrales de confianza para la coincidencia de texto. 
# Puedes ajustarlos si ves que es demasiado estricto o demasiado permisivo.
ARCHETYPE_THRESHOLD = 80  # Debe haber una coincidencia bastante clara para el sonido base.
MODIFIER_THRESHOLD = 75   # Un poco más permisivo para las cualidades del sonido.


def normalize_text(text: str) -> str:
    """
    Limpia el texto de entrada para un mejor procesamiento.
    """
    return text.lower().strip()


def parse_sound_prompt(prompt: str):
    """
    Analiza el prompt del usuario para extraer el arquetipo de sonido principal
    y los modificadores aplicables utilizando lógica difusa (fuzzy logic).

    Returns:
        Una lista de 'tags' (strings) que incluye el arquetipo y los modificadores detectados,
        lista para ser usada por `generate_synth_patch`.
    """
    clean_prompt = normalize_text(prompt)
    if not clean_prompt:
        return {"tags": ["lead"], "error": "Prompt vacío, usando 'lead' por defecto."}

    # 1. BÚSQUEDA DEL ARQUETIPO (El tipo de sonido principal)
    # Usamos `process.extractOne` para encontrar la MEJOR coincidencia para el arquetipo.
    # Es importante que cada sonido tenga solo UN arquetipo base.
    best_archetype_match = process.extractOne(
        clean_prompt,
        VALID_ARCHETYPES,
        scorer=fuzz.token_set_ratio # Este scorer es bueno para encontrar palabras clave en frases.
    )

    detected_archetype = None
    if best_archetype_match and best_archetype_match[1] >= ARCHETYPE_THRESHOLD:
        detected_archetype = best_archetype_match[0]
        print(f"INFO (Sound Prompt): Arquetipo detectado -> '{detected_archetype}' (Confianza: {best_archetype_match[1]}%)")
    else:
        # Si no estamos seguros del arquetipo, es mejor usar uno por defecto que adivinar mal.
        print(f"WARN (Sound Prompt): No se detectó un arquetipo claro. Usando 'poly_synth' por defecto.")
        detected_archetype = "poly_synth"

    # 2. BÚSQUEDA DE MODIFICADORES (Las cualidades del sonido)
    # Usamos `process.extract` para encontrar TODAS las coincidencias que superen el umbral.
    # Un sonido puede tener varios modificadores (ej: 'bright' y 'soft').
    best_modifier_matches = process.extract(
        clean_prompt,
        VALID_MODIFIERS,
        scorer=fuzz.token_set_ratio,
        limit=5 # Limitamos a un máximo de 5 modificadores por si acaso.
    )

    detected_modifiers = []
    if best_modifier_matches:
        for mod, score in best_modifier_matches:
            if score >= MODIFIER_THRESHOLD:
                detected_modifiers.append(mod)
                print(f"INFO (Sound Prompt): Modificador detectado -> '{mod}' (Confianza: {score}%)")

    # 3. CONSTRUIR EL RESULTADO FINAL
    # La lista final de tags que se enviará al sound designer.
    # Nos aseguramos de que no haya duplicados.
    final_tags = [detected_archetype] + list(set(detected_modifiers))

    print(f"INFO (Sound Prompt): Tags finales para Sound Designer -> {final_tags}")
    
    return {"tags": final_tags, "error": None}

# --- Bloque para pruebas directas del script ---
if __name__ == '__main__':
    test_prompts = [
        "a bright and soft lead sound",
        "dark ambient pad",
        "give me an aggressive bass",
        "llave suave y brillante", # Prueba en español para "keys"
        "pluck vintage",
        "modern lofi arp", # Debería detectar 'lofi' y 'modern'
        "sonido calido y brillante",
        "Un bajo agresivo y oscuro"
    ]

    for p in test_prompts:
        result = parse_sound_prompt(p)
        print(f"Prompt: '{p}' -> Resultado: {result['tags']}")
        print("-" * 30)