# procesador_sentimientos.py
import random
import re
# Importar nota_equivalente desde generador_acordes.py
from generador_acordes import nota_equivalente
# Mantener la importación de procesador_prompt si se usa para otras cosas,
# aunque para nota_equivalente ya no es necesario.
# Si no se usa para nada más, se podría quitar.
import procesador_prompt


# Palabras clave para identificar sentimientos y su forma canónica
PALABRAS_CLAVE_SENTIMIENTOS = {
    # Alegría / Positivo
    "alegre": "alegria", "alegría": "alegria", "feliz": "alegria", "contento": "alegria", "jovial": "alegria",
    "felicidad": "alegria",
    "divertido": "diversion", "diversión": "diversion", "festivo": "festividad", "celebracion": "celebracion", "celebración": "celebracion",
    "eufórico": "euforia", "euforia": "euforia", "energetico": "energia", "energético": "energia", "energia": "energia", "energía": "energia",
    "brillante": "brillantez", "luminoso": "brillantez",
    # Calma / Paz
    "calma": "calma", "sereno": "serenidad", "serenidad": "serenidad", "tranquilo": "calma", "relajado": "relajacion", "relajación": "relajacion",
    "paz": "calma",
    # Romance / Amor
    "romantico": "romance", "romántico": "romance", "romance": "romance", "amor": "amor", "amoroso": "amor",
    "pasion": "pasion", "pasión": "pasion", "apasionado": "pasion", "seductor": "seduccion", "sensual": "sensualidad",
    # Tristeza / Melancolía
    "triste": "tristeza", "tristeza": "tristeza", "melancolico": "melancolia", "melancólico": "melancolia", "melancolía": "melancolia",
    "nostalgia": "nostalgia", "nostalgico": "nostalgia", "nostálgico": "nostalgia",
    "afligido": "tristeza", "deprimido": "tristeza profunda", "lamento": "lamento", "dolor": "dolor emocional", "penas": "tristeza",
    # Tensión / Oscuro / Negativo
    "tenso": "tension", "tensión": "tension", "suspense": "suspense", "misterio": "misterio", "oscuro": "oscuridad", "siniestro": "oscuridad",
    "epico": "epico", "épico": "epico", "epica": "epico", "grandioso": "grandiosidad",
    "angustia": "angustia", "desesperacion": "desesperacion", "desesperación": "desesperacion",
    "terror": "terror", "caos": "caos", "inquietante": "inquietud",
    "rabia": "rabia", "ira": "ira", "furioso": "ira", "frustracion": "frustracion", "frustración": "frustracion", "callejera": "rabia callejera",
    # Otros
    "sofisticado": "sofisticacion", "elegante": "elegancia",
    "esperanza": "esperanza", "patriotico": "patriotismo", "patriótico": "patriotismo",
    "espiritual": "espiritualidad", "trascendental": "trascendencia",
    "soledad": "soledad", "aislamiento": "aislamiento", "reflexivo": "reflexion", "reflexión": "reflexion", "existencial": "reflexion existencial",
    "hipnotico": "hipnosis", "hipnótico": "hipnosis", "industrial": "industrial",
    "bittersweet": "melancolia bittersweet", "agridulce": "melancolia bittersweet",
    "funebre": "funebre", "fúnebre": "funebre",
}

MAPEO_SENTIMIENTO_A_PARAMETROS = {
    "alegria": {"modo": "major", "tonalidades": ["C", "D", "G", "B", "E", "F"], "generos": ["pop", "vals", "reggaeton", "jazz"]},
    "pureza": {"modo": "major", "tonalidades": ["C"], "generos": ["pop"]},
    "inocencia": {"modo": "major", "tonalidades": ["C"], "generos": ["pop"]},
    "brillantez": {"modo": "major", "tonalidades": ["C#", "B", "D#"], "generos": []},
    "festividad": {"modo": "major", "tonalidades": ["C#", "B", "D", "E"], "generos": ["reggaeton", "techno", "pop", "vals"]},
    "romance": {"modo": "major", "tonalidades": ["D", "F", "A", "Eb"], "generos": ["r&b", "pop", "vals", "jazz"]},
    "júbilo": {"modo": "major", "tonalidades": ["D", "G", "B"], "generos": ["pop", "vals"]},
    "energia": {"modo": "major", "tonalidades": ["D#", "E", "G#", "B"], "generos": ["techno", "reggaeton", "pop"]},
    "extasis": {"modo": "major", "tonalidades": ["D#", "E"], "generos": ["techno", "pop"]},
    "grandiosidad": {"modo": "major", "tonalidades": ["D#", "A#", "E"], "generos": []},
    "euforia": {"modo": "major", "tonalidades": ["E", "G#", "B"], "generos": ["techno", "pop", "reggaeton"]},
    "diversion": {"modo": "major", "tonalidades": ["E", "C", "G"], "generos": ["pop", "reggaeton", "jazz"]},
    "calma": {"modo": "major", "tonalidades": ["F", "C", "Bb"], "generos": ["lofi", "jazz"]},
    "serenidad": {"modo": "major", "tonalidades": ["F", "Bb"], "generos": ["lofi", "jazz"]},
    "glamour": {"modo": "major", "tonalidades": ["F#", "C#"], "generos": ["jazz"]},
    "elegancia": {"modo": "major", "tonalidades": ["F#", "D", "A"], "generos": ["jazz", "vals", "pop"]},
    "esperanza": {"modo": "major", "tonalidades": ["G", "C", "D"], "generos": ["pop"]},
    "patriotismo": {"modo": "major", "tonalidades": ["G", "C", "F"], "generos": []},
    "belleza": {"modo": "major", "tonalidades": ["A", "E", "F#"], "generos": []},
    "amor": {"modo": "major", "tonalidades": ["A", "D", "E", "F"], "generos": ["pop", "r&b", "vals"]},
    "majestuosidad": {"modo": "major", "tonalidades": ["A#", "D#", "F"], "generos": []},
    "asombro": {"modo": "major", "tonalidades": ["A#", "E"], "generos": []},
    "celebracion": {"modo": "major", "tonalidades": ["B", "C#", "D", "G"], "generos": ["reggaeton", "pop", "techno"]},
    "sensualidad": {"modo": "major", "tonalidades": ["D", "F#", "A", "C#"], "generos": ["r&b", "reggaeton", "jazz", "lofi"]},

    "tristeza": {"modo": "minor", "tonalidades": ["C", "D", "A", "E", "G"], "generos": ["lofi", "pop", "vals", "r&b", "jazz"]},
    "tristeza profunda": {"modo": "minor", "tonalidades": ["C", "D#", "Fm"], "generos": ["vals", "lofi"]},
    "lamento": {"modo": "minor", "tonalidades": ["C", "Fm"], "generos": []},
    "misterio": {"modo": "minor", "tonalidades": ["C#", "F#m"], "generos": []},
    "suspense": {"modo": "minor", "tonalidades": ["C#", "G#m"], "generos": []},
    "melancolia": {"modo": "minor", "tonalidades": ["D", "A", "E", "Gm"], "generos": ["jazz", "lofi", "pop", "vals"]},
    "nostalgia": {"modo": "minor", "tonalidades": ["D", "A", "Am"], "generos": ["jazz", "lofi", "vals", "pop"]},
    "angustia": {"modo": "minor", "tonalidades": ["D#", "G#m"], "generos": []},
    "desesperacion": {"modo": "minor", "tonalidades": ["D#", "Cm"], "generos": []},
    "dolor emocional": {"modo": "minor", "tonalidades": ["E", "Am", "Bm"], "generos": ["lofi", "pop", "r&b"]},
    "vulnerabilidad": {"modo": "minor", "tonalidades": ["E", "Am"], "generos": ["r&b", "lofi", "pop"]},
    "pasion": {"modo": "minor", "tonalidades": ["F", "Cm", "Dm"], "generos": ["r&b", "vals", "reggaeton"]},
    "trascendencia": {"modo": "minor", "tonalidades": ["F#", "Bm"], "generos": []},
    "espiritualidad": {"modo": "minor", "tonalidades": ["F#", "Am"], "generos": []},
    "rebeldia": {"modo": "minor", "tonalidades": ["G", "Em"], "generos": []},
    "tension": {"modo": "minor", "tonalidades": ["G", "C#", "Bm"], "generos": ["techno", "reggaeton"]},
    "terror": {"modo": "minor", "tonalidades": ["G#", "D#m"], "generos": []},
    "caos": {"modo": "minor", "tonalidades": ["G#"], "generos": []},
    "añoranza": {"modo": "minor", "tonalidades": ["A", "Dm", "Em"], "generos": ["vals", "lofi", "pop"]},
    "soledad": {"modo": "minor", "tonalidades": ["A#", "E", "Am"], "generos": ["lofi", "jazz"]},
    "aislamiento": {"modo": "minor", "tonalidades": ["A#", "Fm"], "generos": ["lofi"]},
    "ira": {"modo": "minor", "tonalidades": ["B", "G", "Gm"], "generos": ["reggaeton", "techno"]},
    "frustracion": {"modo": "minor", "tonalidades": ["B", "Gm"], "generos": ["reggaeton"]},
    "rabia callejera": {"modo": "minor", "tonalidades": ["G", "B", "Cm"], "generos": ["reggaeton"]},
    "sofisticacion": {"modo": "major", "tonalidades": ["F#", "C#"], "generos": ["jazz"]},
    "relajacion": {"modo": "major", "tonalidades": ["F", "C", "Bb"], "generos": ["lofi", "jazz"]},
    "reflexion": {"modo": "minor", "tonalidades": ["E", "A", "Am"], "generos": ["lofi"]},
    "reflexion existencial": {"modo": "minor", "tonalidades": ["E", "A#", "Dm"], "generos": ["lofi"]},
    "hipnosis": {"modo": "minor", "tonalidades": ["G", "Am"], "generos": ["techno"]},
    "industrial": {"modo": "minor", "tonalidades": ["G", "C#", "D#m"], "generos": ["techno"]},
    "seduccion": {"modo": "major", "tonalidades": ["D","A", "F#", "Eb"], "generos": ["r&b", "jazz"]},
    "desamor": {"modo": "minor", "tonalidades": ["E","D", "A", "Cm"], "generos": ["r&b", "pop", "vals"]},
    "entusiasmo": {"modo": "major", "tonalidades": ["C","G","D", "E", "B"], "generos": ["pop", "reggaeton"]},
    "drama": {"modo": "minor", "tonalidades": ["F", "D", "C", "Gm"], "generos": ["vals"]},
    "melancolia bittersweet": {"modo": "minor", "tonalidades": ["D", "A", "E", "Am"], "generos": ["pop", "lofi"]},
    "funebre": {"modo": "minor", "tonalidades": ["C", "D", "Fm"], "generos": ["vals"]},
    "oscuridad": {"modo": "minor", "tonalidades": ["C#", "G#", "D#", "Fm"], "generos": ["techno", "reggaeton", "vals"]},
    "epico": {"modo": "major", "tonalidades": ["D#", "A#", "E", "C"], "generos": []},
    "inquietud": {"modo": "minor", "tonalidades": ["C#", "G#", "Fm"], "generos": []},
}

MAPEO_GENERO_SENTIMIENTO_MODO = {
    "jazz": {"melancolia": "minor", "nostalgia": "minor", "blues": "minor", "glamour": "major", "sofisticacion": "major", "alegria": "major", "calma": "major", "romance": "major", "sensualidad": "major"},
    "lofi": {"calma": "major", "relajacion": "major", "soledad": "minor", "reflexion": "minor", "melancolia": "minor", "tristeza": "minor", "añoranza": "minor", "dolor emocional": "minor", "vulnerabilidad": "minor"},
    "r&b": {"romance": "major", "pasion": "major", "seduccion": "major", "vulnerabilidad": "minor", "desamor": "minor", "tristeza": "minor", "dolor emocional": "minor", "amor": "major"},
    "techno": {"euforia": "major", "energia": "major", "tension": "minor", "hipnosis": "minor", "industrial": "minor", "oscuro": "minor", "ira": "minor"},
    "reggaeton": {"festividad": "major", "diversion": "major", "sensualidad": "major", "rabia": "minor", "frustracion": "minor", "rabia callejera": "minor", "oscuro": "minor", "energia": "major", "alegria": "major"},
    "pop": {"alegria": "major", "entusiasmo": "major", "amor": "major", "melancolia": "minor", "tristeza": "minor", "desamor": "minor", "añoranza": "minor", "diversion": "major", "energia": "major"},
    "vals": {"elegancia": "major", "romance": "major", "tragedia": "minor", "drama": "minor", "nostalgia": "minor", "tristeza": "minor", "funebre": "minor", "melancolia": "minor"},
}

def normalizar_texto_para_sentimientos(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s&#ñáéíóúü\-]", " ", texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def detectar_sentimiento_en_prompt(prompt_crudo):
    prompt_normalizado = normalizar_texto_para_sentimientos(prompt_crudo)
    if not prompt_normalizado:
        return None

    detected_sentiments = {}
    palabras_prompt_lista = prompt_normalizado.split()

    for longitud_frase in range(3, 0, -1):
        for i in range(len(palabras_prompt_lista) - longitud_frase + 1):
            frase_candidata = " ".join(palabras_prompt_lista[i : i + longitud_frase])
            if frase_candidata in PALABRAS_CLAVE_SENTIMIENTOS:
                sentimiento_canonico = PALABRAS_CLAVE_SENTIMIENTOS[frase_candidata]
                detected_sentiments[sentimiento_canonico] = detected_sentiments.get(sentimiento_canonico, 0) + (longitud_frase * 10) + 5

    for palabra in palabras_prompt_lista:
        if palabra in PALABRAS_CLAVE_SENTIMIENTOS:
            sentimiento_canonico = PALABRAS_CLAVE_SENTIMIENTOS[palabra]
            # Solo añadir si no fue detectado como parte de una frase más larga (o darle menos peso)
            if sentimiento_canonico not in detected_sentiments or detected_sentiments[sentimiento_canonico] < 10:
                 detected_sentiments[sentimiento_canonico] = detected_sentiments.get(sentimiento_canonico, 0) + 1


    if detected_sentiments:
        sentimiento_elegido = max(detected_sentiments, key=detected_sentiments.get)
        print(f"INFO (Sentimientos): Sentimiento elegido: '{sentimiento_elegido}' de {detected_sentiments}")
        return sentimiento_elegido
    print(f"INFO (Sentimientos): No se detectó ningún sentimiento conocido en '{prompt_crudo}'.")
    return None


def inferir_parametros_desde_sentimiento(sentimiento, genero_actual, raiz_actual, modo_actual, generos_disponibles_entrenados):
    genero_inferido = genero_actual
    raiz_inferida = raiz_actual
    modo_inferido = modo_actual

    if not sentimiento:
        print(f"INFO (Inferencia): No hay sentimiento detectado. Parámetros sin cambios: G='{genero_inferido}', R='{raiz_inferida}', M='{modo_inferido}'")
        return genero_inferido, raiz_inferida, modo_inferido

    datos_sentimiento = MAPEO_SENTIMIENTO_A_PARAMETROS.get(sentimiento)
    if not datos_sentimiento:
        print(f"INFO (Inferencia): Sentimiento '{sentimiento}' no tiene mapeo general. Parámetros sin cambios.")
        return genero_inferido, raiz_inferida, modo_inferido

    # 1. Inferir Género (solo si no fue explícito y es "normal" o None)
    if genero_inferido == "normal" or genero_inferido is None:
        generos_sugeridos_por_sentimiento = datos_sentimiento.get("generos", [])
        generos_entrenados_validos_para_sentimiento = [g for g in generos_sugeridos_por_sentimiento if g in generos_disponibles_entrenados]

        if generos_entrenados_validos_para_sentimiento:
            genero_inferido = random.choice(generos_entrenados_validos_para_sentimiento)
            print(f"INFO (Inferencia): Género '{genero_inferido}' inferido por sentimiento '{sentimiento}' (de los entrenados y sugeridos).")
        elif generos_disponibles_entrenados:
            genero_inferido = random.choice(list(generos_disponibles_entrenados))
            print(f"INFO (Inferencia): Sentimiento no sugiere géneros entrenados o los sugeridos no están. Género aleatorio '{genero_inferido}' elegido de los disponibles.")
        else:
            print(f"INFO (Inferencia): No hay géneros entrenados disponibles. Género se mantiene '{genero_inferido}'.")

    # 2. Inferir Modo
    modo_sugerido_por_sentimiento_general = datos_sentimiento.get("modo")
    if modo_actual is None and modo_sugerido_por_sentimiento_general:
        modo_inferido = modo_sugerido_por_sentimiento_general
        print(f"INFO (Inferencia): Modo '{modo_inferido}' inferido por sentimiento general '{sentimiento}'.")

    if genero_inferido and genero_inferido != "normal" and genero_inferido in MAPEO_GENERO_SENTIMIENTO_MODO:
        modos_especificos_genero = MAPEO_GENERO_SENTIMIENTO_MODO[genero_inferido]
        modo_especifico_gen_sent = modos_especificos_genero.get(sentimiento)
        if modo_especifico_gen_sent:
            if modo_actual is None or modo_actual.lower() != modo_especifico_gen_sent.lower():
                modo_inferido = modo_especifico_gen_sent
                print(f"INFO (Inferencia): Modo '{modo_inferido}' (re)inferido por combinación específica género '{genero_inferido}' y sentimiento '{sentimiento}'.")

    # 3. Inferir Raíz (solo si no fue explícita)
    if raiz_inferida is None:
        raices_sugeridas_por_sentimiento = datos_sentimiento.get("tonalidades", [])
        if raices_sugeridas_por_sentimiento:
            # Usar nota_equivalente directamente ya que fue importada
            raices_validas = [r for r in raices_sugeridas_por_sentimiento if r in nota_equivalente.values() or r.lower() in nota_equivalente]
            if raices_validas:
                raiz_inferida = random.choice(raices_validas)
                print(f"INFO (Inferencia): Raíz '{raiz_inferida}' inferida por sentimiento '{sentimiento}'.")
            else:
                print(f"WARN (Inferencia): Las raíces sugeridas por sentimiento '{sentimiento}' no son válidas o no están en nota_equivalente: {raices_sugeridas_por_sentimiento}")
        else:
             print(f"INFO (Inferencia): Sentimiento '{sentimiento}' no sugiere tonalidades específicas.")

    if modo_inferido is None:
        modo_inferido = "major"
        print(f"INFO (Inferencia): Modo inferido por defecto a '{modo_inferido}'.")
        
    print(f"INFO (Inferencia Final): G='{genero_inferido}', R='{raiz_inferida}', M='{modo_inferido}'")
    return genero_inferido, raiz_inferida, modo_inferido

if __name__ == '__main__':
    print("--- Pruebas de procesador_sentimientos.py ---")
    test_prompts = [
        "cancion alegre",
        "musica triste en jazz",
        "algo romantico en pop",
        "reggaeton con mucha energia",
        "lofi para la nostalgia",
        "vals funebre",
        "techno oscuro e industrial",
        "balada de desamor",
        "pop energetico en Do mayor",
        "sentimiento de euforia",
        "jazz melancolico en Re menor",
        "Quiero algo triste",
        "Reggaeton triste",
        "r&b romántico",
        "r&b romantico",
        "feliz",
        "pasion"
    ]
    generos_entrenados_test = {"pop", "jazz", "reggaeton", "lofi", "techno", "vals", "r&b"}

    from generos import detectar_estilo as detectar_estilo_generos
    from generador_acordes import extraer_tonalidad as extraer_tonalidad_acordes
    # procesador_prompt ya está importado arriba

    for prompt in test_prompts:
        print(f"\nPROMPT: \"{prompt}\"")
        estilo_inicial = detectar_estilo_generos(prompt)
        sentimiento = detectar_sentimiento_en_prompt(prompt)
        raiz_expl, modo_expl = extraer_tonalidad_acordes(prompt, estilo_inicial)

        print(f"  - Estilo Inicial Detectado: {estilo_inicial}")
        print(f"  - Sentimiento Detectado: {sentimiento}")
        print(f"  - Raíz Explícita: {raiz_expl}, Modo Explícito: {modo_expl}")

        genero_final, raiz_final, modo_final = inferir_parametros_desde_sentimiento(
            sentimiento, estilo_inicial, raiz_expl, modo_expl, generos_entrenados_test
        )
        print(f"  -> RESULTADO FINAL: Género='{genero_final}', Raíz='{raiz_final}', Modo='{modo_final}'")
        print("-" * 30)

    print("\nPrueba de mapeo de 'tristeza':")
    print(MAPEO_SENTIMIENTO_A_PARAMETROS.get("tristeza"))
