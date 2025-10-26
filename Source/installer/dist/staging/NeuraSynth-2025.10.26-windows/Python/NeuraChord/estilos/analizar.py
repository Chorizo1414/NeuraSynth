import importlib
import argparse
import os
import sys
from collections import defaultdict
import re

def analyze_base_file(filepath):
    """
    Analiza el diccionario INFO_GENERO dentro de un archivo base_*.py
    y cuenta el número de progresiones aprendidas por tonalidad.
    """
    tonality_counts = defaultdict(lambda: defaultdict(int))

    # Asegurarse de que el directorio del archivo esté en la ruta de Python
    # para que se pueda importar correctamente.
    dir_name = os.path.dirname(filepath)
    if dir_name not in sys.path and dir_name: # Añadir solo si no está vacío y no está ya
        sys.path.insert(0, dir_name)
    elif not dir_name and '.' not in sys.path: # Añadir directorio actual si no está
         sys.path.insert(0, '.')


    # 1. Convertir la ruta del archivo al nombre del módulo
    if not os.path.exists(filepath):
        print(f"Error: El archivo '{filepath}' no existe.")
        return None

    module_name = os.path.splitext(os.path.basename(filepath))[0]

    try:
        # 2. Importar dinámicamente el módulo
        # Si ya estaba importado, lo recargamos para obtener la versión más reciente
        if module_name in sys.modules:
             style_module = importlib.reload(sys.modules[module_name])
        else:
             style_module = importlib.import_module(module_name)

        # 3. Verificar si INFO_GENERO existe y es un diccionario
        if not hasattr(style_module, 'INFO_GENERO') or not isinstance(style_module.INFO_GENERO, dict):
            print(f"Error: El archivo '{filepath}' no contiene un diccionario 'INFO_GENERO' válido.")
            # Limpiar sys.path si se modificó
            if dir_name and dir_name == sys.path[0]:
                sys.path.pop(0)
            elif not dir_name and '.' == sys.path[0]:
                 sys.path.pop(0)
            return None

        info_genero = style_module.INFO_GENERO

        # Asumimos que hay una sola clave de género por archivo (ej. 'pop', 'techno')
        if len(info_genero) != 1:
             print(f"Advertencia: Se esperaba un solo género en '{filepath}', se encontraron {len(info_genero)}. Usando el primero: '{list(info_genero.keys())[0]}'")

        genre_key = list(info_genero.keys())[0]
        tonalities_data = info_genero[genre_key]

        # 4. Iterar a través de las tonalidades definidas en el diccionario
        for tonality_str, data in tonalities_data.items():
            # Ignorar la clave 'patrones_ritmicos' si está al mismo nivel que las tonalidades
            if tonality_str == 'patrones_ritmicos':
                continue

            # Intentar parsear la cadena de tonalidad (ej. "a major", "c# minor")
            match = re.match(r'([a-gA-G][#b]?)\s+(major|minor)', tonality_str, re.IGNORECASE)
            if match:
                key_raw = match.group(1)
                mode_raw = match.group(2).lower()

                # Normalizar Tonalidad (Nota)
                key = key_raw[0].upper() + key_raw[1:].lower() # Ej: 'C#', 'Eb', 'A'

                # Normalizar Modo
                mode = 'Mayor' if 'major' in mode_raw else 'Menor'

                # Contar cuántas progresiones están definidas para esta tonalidad
                num_progressions = 0
                if 'learned_progressions' in data and isinstance(data['learned_progressions'], list):
                     num_progressions = len(data['learned_progressions'])

                # Acumular el conteo de progresiones para esa tonalidad/modo
                # Si no hay progresiones, se sumará 0, pero la tonalidad quedará registrada.
                tonality_counts[mode][key] += num_progressions

            else:
                print(f"Advertencia: No se pudo parsear la clave de tonalidad '{tonality_str}' en '{filepath}'. Se ignora.")

    except ImportError as e:
        print(f"Error: No se pudo importar el módulo '{module_name}' desde '{filepath}'. Detalles: {e}")
        print("Asegúrate de ejecutar este script desde la carpeta raíz ('NeuraChord') o que la ruta sea correcta.")
        return None
    except Exception as e:
        print(f"Error inesperado procesando '{filepath}': {e}")
        return None
    finally:
        # Limpiar sys.path si se modificó
        if dir_name and dir_name == sys.path[0]:
             sys.path.pop(0)
        elif not dir_name and '.' == sys.path[0]:
             sys.path.pop(0)


    return tonality_counts

def print_formatted_counts(counts, filename):
    """Imprime los conteos con el formato solicitado."""
    if not counts:
        print(f"No se encontraron datos de tonalidad válidos en '{filename}'.")
        return

    print(f"\n--- ANÁLISIS DE '{filename}' ---")
    total_progressions = 0

    print("\nESCALA MENOR:")
    minor_keys = counts.get('Menor', {})
    if minor_keys:
        # Ordenar tonalidades alfabéticamente para una salida consistente
        for key in sorted(minor_keys.keys()):
            count = minor_keys[key]
            print(f"{key}: {count}")
            total_progressions += count
    else:
        print("No se definieron progresiones en tonalidades menores.")

    print("\nESCALA MAYOR:")
    major_keys = counts.get('Mayor', {})
    if major_keys:
        # Ordenar tonalidades alfabéticamente
        for key in sorted(major_keys.keys()):
            count = major_keys[key]
            print(f"{key}: {count}")
            total_progressions += count
    else:
        print("No se definieron progresiones en tonalidades mayores.")

    print(f"\nTotal de progresiones aprendidas: {total_progressions}")
    print("---------------------------------")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Analiza la estructura de tonalidades y cuenta progresiones en un archivo base_*.py.")
    # El argumento ahora es el archivo .py que queremos analizar
    parser.add_argument('base_file', type=str, help='Ruta al archivo base_*.py a analizar (ej. base_pop.py o estilos/base_pop.py).')
    args = parser.parse_args()

    filepath = args.base_file

    counts = analyze_base_file(filepath)
    if counts is not None: # Verificar si el análisis fue exitoso
        print_formatted_counts(counts, os.path.basename(filepath))

if __name__ == "__main__":
    main()