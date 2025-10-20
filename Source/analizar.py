import os
import re
import argparse
from collections import defaultdict

def analyze_midi_files(directory):
    """
    Analiza y cuenta los archivos MIDI por tonalidad (mayor/menor)
    basándose en sus nombres de archivo en un directorio determinado.
    """
    # Este diccionario almacenará los conteos así:
    # {'Mayor': {'C': 1, 'G': 2}, 'Menor': {'A': 5, 'C#': 10}}
    tonality_counts = defaultdict(lambda: defaultdict(int))

    # Patrones de expresiones regulares para encontrar la nota y el modo en los nombres de archivo.
    # Están diseñados para ser flexibles con diferentes convenciones de nombres.
    patterns = [
        re.compile(r'([a-gA-G][#b]?)_?(maj|min|m)_', re.IGNORECASE),
        re.compile(r'([a-gA-G][#b]?)_?(maj|min|m)\d?\.mid', re.IGNORECASE),
        re.compile(r'_([a-gA-G][#b]?)(maj|min)\.mid', re.IGNORECASE),
        # Patrón para nombres como 'csharp' o 'fsharp'
        re.compile(r'([a-gA-G](?:sharp|flat))_?(maj|min|m)_', re.IGNORECASE),
    ]

    for filename in os.listdir(directory):
        if not filename.lower().endswith('.mid'):
            continue

        found_match = False
        for pattern in patterns:
            match = pattern.search(filename)
            if match:
                # Normalizar la tonalidad (nota)
                key_raw = match.group(1)
                key = key_raw[0].upper() + key_raw[1:].lower()
                key = key.replace('sharp', '#').replace('flat', 'b')

                # Normalizar el modo (mayor/menor)
                mode_raw = match.group(2).lower()
                mode = 'Mayor' if 'maj' in mode_raw else 'Menor'
                
                tonality_counts[mode][key] += 1
                found_match = True
                break  # Ir al siguiente archivo una vez que se encuentra una coincidencia
        
        if not found_match:
            print(f"-> Advertencia: No se pudo determinar la tonalidad para: {filename}")


    return tonality_counts

def print_formatted_counts(counts):
    """Imprime los conteos con el formato solicitado."""
    
    print("\n--- ANÁLISIS DE TONALIDADES ---")
    
    print("\nESCALA MENOR:")
    if counts['Menor']:
        # Ordenar las tonalidades para una salida consistente
        for key in sorted(counts['Menor'].keys()):
            print(f"{key}: {counts['Menor'][key]}")
    else:
        print("No se encontraron archivos en tonalidades menores.")

    print("\nESCALA MAYOR:")
    if counts['Mayor']:
        # Ordenar las tonalidades
        for key in sorted(counts['Mayor'].keys()):
            print(f"{key}: {counts['Mayor'][key]}")
    else:
        print("No se encontraron archivos en tonalidades mayores.")
    
    print("\n---------------------------------")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Analiza la distribución de tonalidades en archivos MIDI.")
    parser.add_argument('--genero', type=str, required=False, help='Género a analizar (actualmente no afecta el conteo).')
    args = parser.parse_args()

    # El script busca la carpeta MIDI__APRENDER en el mismo directorio donde se ejecuta.
    midi_directory = 'MIDI_APRENDER'

    if not os.path.isdir(midi_directory):
        print(f"Error: La carpeta '{midi_directory}' no existe en el directorio actual.")
        print("Asegúrate de ejecutar este script desde la carpeta raíz de tu proyecto ('NeuraChord').")
        return

    counts = analyze_midi_files(midi_directory)
    print_formatted_counts(counts)


if __name__ == "__main__":
    main()