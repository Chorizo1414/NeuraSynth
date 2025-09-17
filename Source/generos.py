# generos.py
# Importar la función de procesamiento del nuevo archivo
try:
    from procesador_prompt import procesar_prompt_para_genero
except ImportError:
    print("ADVERTENCIA (generos.py): No se pudo importar 'procesador_prompt'. La detección de género será básica.")
    # Fallback a una detección muy simple si el import falla
    # Esta función de fallback solo se usará si procesador_prompt.py no se encuentra.
    def procesar_prompt_para_genero(prompt_crudo):
        prompt_lower = prompt_crudo.lower() if isinstance(prompt_crudo, str) else ""
        if "reggaeton" in prompt_lower or "regueton" in prompt_lower or "regaeton" in prompt_lower:
            return "reggaeton"
        if "lofi" in prompt_lower or "lo-fi" in prompt_lower or "lo fi" in prompt_lower:
            return "lofi"
        if "jazz" in prompt_lower or "jass" in prompt_lower:
            return "jazz"
        if "r&b" in prompt_lower or "rnb" in prompt_lower or "r and b" in prompt_lower:
            return "r&b"
        if "vals" in prompt_lower or "waltz" in prompt_lower:
            return "vals"
        if "pop" in prompt_lower:
            return "pop"
        if "techno" in prompt_lower or "tecno" in prompt_lower:
            return "techno"
        return "normal"

def detectar_estilo(prompt_crudo):
    """
    Detecta el estilo musical basado en el prompt del usuario,
    utilizando el módulo de procesamiento de prompt.
    """
    # La función procesar_prompt_para_genero (importada o la de fallback)
    # ya maneja la normalización y devuelve el nombre canónico del género o "normal".
    genero_detectado = procesar_prompt_para_genero(prompt_crudo)
    return genero_detectado

if __name__ == '__main__':
    # Pruebas para generos.py (opcional, las pruebas más completas están en procesador_prompt.py)
    prompts_de_prueba_generos = [
        "Reggaeton lento",
        "lo-fi chill",
        "jazz suave",
        "rnb",
        "un vals por favor",
        "musica pop",
        "tecno",
        "algo de rock" # Debería devolver 'normal' si no está en el procesador_prompt
    ]

    print("--- Pruebas desde generos.py ---")
    for p_test in prompts_de_prueba_generos:
        estilo = detectar_estilo(p_test)
        print(f"Prompt: '{p_test}' -> Estilo Detectado en generos.py: '{estilo}'")

