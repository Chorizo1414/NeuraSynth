# procesador_prompt.py
import re

# Define los géneros conocidos y sus variaciones comunes o errores de escritura
# El valor asociado es el nombre "canónico" o "normalizado" del género.
MAPEO_ERRORES_GENERO = {
    # Reggaeton
    "reggaeton": "reggaeton",
    "regaeton": "reggaeton",
    "regueton": "reggaeton",
    "regeton": "reggaeton",
    "reggaetton": "reggaeton",
    "reggeton": "reggaeton",
    # Lofi
    "lofi": "lofi",
    "lo-fi": "lofi",
    "lo fi": "lofi",
    "lowfi": "lofi",
    "low-fi": "lofi",
    "low fi": "lofi",
    # Jazz
    "jazz": "jazz",
    "jass": "jazz",
    "jas": "jazz",
    "jaz": "jazz",
    # R&B
    "r&b": "r&b",
    "rnb": "r&b",
    "rhythm and blues": "r&b",
    "r and b": "r&b",
    # Vals
    "vals": "vals",
    "valz": "vals", 
    "waltz": "vals",
    "valses": "vals",
    "vals lento": "vals",
    "balada vals": "vals",
    "balada": "vals",
    "valada": "vals",
    # Pop
    "pop": "pop",
    "pop music": "pop", # Frase común
    "musica pop": "pop", # En español
    # Techno
    "techno": "techno",
    "tecno": "techno", # Error común en español
    "tekno": "techno", # Otra variación
}

# Lista de los nombres canónicos de los géneros que el sistema soporta
# Debes asegurarte de que existan los archivos base_<genero>.py para estos
# y que el autoentrenador los pueda procesar.
GENEROS_SOPORTADOS = ["reggaeton", "lofi", "jazz", "r&b", "vals", "pop", "techno"]

def normalizar_texto_simple(texto):
    """
    Realiza una limpieza básica del texto: minúsculas y elimina espacios extra.
    """
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = re.sub(r'\s+', ' ', texto).strip() # Reemplaza múltiples espacios con uno solo
    return texto

def corregir_genero_en_prompt(prompt_normalizado):
    """
    Intenta identificar y corregir el nombre de un género musical en el prompt
    basándose en el MAPEO_ERRORES_GENERO.
    Devuelve el nombre canónico del género si se encuentra una coincidencia,
    o None si no se encuentra un género conocido.
    """
    palabras_prompt = prompt_normalizado.split()

    max_longitud_frase_genero = 3 
    for longitud_frase in range(max_longitud_frase_genero, 0, -1):
        for i in range(len(palabras_prompt) - longitud_frase + 1):
            sub_frase = " ".join(palabras_prompt[i : i + longitud_frase])
            if sub_frase in MAPEO_ERRORES_GENERO:
                return MAPEO_ERRORES_GENERO[sub_frase]
            
    return None 

def procesar_prompt_para_genero(prompt_crudo):
    """
    Procesa el prompt crudo para extraer un nombre de género normalizado.
    """
    if not prompt_crudo or not isinstance(prompt_crudo, str):
        return "normal" 

    prompt_limpio = normalizar_texto_simple(prompt_crudo)
    
    genero_corregido = corregir_genero_en_prompt(prompt_limpio)

    if genero_corregido and genero_corregido in GENEROS_SOPORTADOS:
        print(f"INFO (Procesador Prompt): Género detectado y normalizado: '{genero_corregido}'")
        return genero_corregido
    else:
        for gen_soportado in GENEROS_SOPORTADOS:
            if re.search(r'\b' + re.escape(gen_soportado) + r'\b', prompt_limpio):
                print(f"INFO (Procesador Prompt): Género detectado por nombre canónico: '{gen_soportado}'")
                return gen_soportado
        
        print(f"INFO (Procesador Prompt): No se detectó un género conocido. Usando 'normal'. Prompt original: '{prompt_crudo}'")
        return "normal" 

if __name__ == '__main__':
    # Pruebas
    prompts_de_prueba = [
        "Reggaeton lento",
        "Quiero un regueton suave",
        "reggaetton en Do Mayor",
        "Un beat de lofi para estudiar",
        "lo-fi chill",
        "low fi beats",
        "jass",
        "jazz suave",
        "jaz",
        "rnb",
        "R&B tranquilo",
        "rhythm and blues clasico",
        "r and b",
        "un vals por favor",
        "valz para bailar",
        "waltz",
        "pop music",
        "musica pop",
        "algo de techno",
        "tecno fuerte",
        "tekno",
        "algo de trap", 
        "Rock and Roll", 
        "   REGGAETON   con   muchos   espacios   "
    ]

    for p in prompts_de_prueba:
        genero_detectado = procesar_prompt_para_genero(p)
        print(f"Prompt: '{p}' -> Género Detectado: '{genero_detectado}'")
        print("-" * 20)
