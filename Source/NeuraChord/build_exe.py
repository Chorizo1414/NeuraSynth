# build_exe.py
import PyInstaller.__main__
import os
import shutil

# --- Configuración de la Aplicación ---
APP_NAME = "NeuraChord"  # El nombre que tendrá tu aplicación y el ejecutable.
MAIN_SCRIPT = "main.py"  # Tu script principal de Python.
ICON_FILE = os.path.join("sources", "piano.ico") # Ruta a tu archivo de icono (.ico para Windows).
                                                # Asegúrate de tener piano.ico en la carpeta sources,
                                                # o cambia esto a piano.png si prefieres que PyInstaller intente convertirlo.

# --- Carpetas y Archivos de Datos para Incluir ---
# Lista de tuplas o listas: ('ruta_origen_en_proyecto', 'ruta_destino_en_bundle')
# La ruta de destino es relativa a la raíz del paquete del ejecutable.
# Usa ';' como separador para Windows, ':' para macOS/Linux.
DATA_TO_ADD = [
    ('estilos', 'estilos'),    # Copia la carpeta 'estilos' completa a una carpeta 'estilos' en el bundle.
    ('sources', 'sources'),    # Copia la carpeta 'sources' completa a una carpeta 'sources' en el bundle.
    # ('otro_archivo.txt', '.') # Ejemplo: copia un archivo a la raíz del bundle.
    # ('otra_carpeta_datos', 'datos_internos') # Ejemplo: copia 'otra_carpeta_datos' a 'datos_internos' en el bundle.
]

# --- Módulos Ocultos ---
# Lista de módulos que PyInstaller podría no detectar automáticamente pero que tu app necesita.
# Si obtienes errores de 'ModuleNotFound' al ejecutar el .exe, añádelos aquí.
HIDDEN_IMPORTS = [
    'pygame',
    'tkinterdnd2',
    'customtkinter', # Si estás usando customtkinter
    'music21',
    # A veces es útil ser más específico con sub-módulos de music21 si hay problemas:
    'music21.stream', 'music21.note', 'music21.chord', 'music21.key',
    'music21.tempo', 'music21.harmony', 'music21.pitch', 'music21.roman',
    'music21.converter', 'music21.instrument', 'music21.scale', 'music21.midi',
    'PIL._tkinter_finder' # A veces necesario para Pillow con Tkinter
]

# --- Opciones de PyInstaller ---
# Consulta la documentación de PyInstaller para ver todas las opciones disponibles.
PYINSTALLER_OPTIONS = [
    '--noconfirm',    # Sobrescribe las carpetas 'build' y 'dist' sin preguntar.
    '--clean',        # Limpia los cachés de PyInstaller y archivos temporales antes de construir.
    '--windowed',     # Para aplicaciones GUI (sin ventana de consola en Windows).
                      # En Windows, a veces '--noconsole' es preferible si '--windowed' aún muestra una consola brevemente.
    # '--onefile',    # Descomenta esta línea si quieres un único archivo ejecutable.
                      # Advertencia: El inicio puede ser más lento y el manejo de rutas a datos es más complejo.
                      # Es mejor probar primero en modo directorio (sin --onefile).
    # '--debug=all',  # Para obtener muchos mensajes de depuración durante la compilación (útil si algo falla).
]

def build_executable():
    """
    Ejecuta PyInstaller con la configuración definida.
    """
    print(f"--- Iniciando compilación para: {APP_NAME} ---")

    # Construir la lista de argumentos para PyInstaller
    command_args = [
        '--name', APP_NAME,
        MAIN_SCRIPT
    ]
    command_args.extend(PYINSTALLER_OPTIONS) # Añadir opciones generales

    # Añadir icono si existe
    if ICON_FILE and os.path.exists(ICON_FILE):
        command_args.extend(['--icon', ICON_FILE])
        print(f"INFO: Usando icono: {ICON_FILE}")
    elif ICON_FILE: # Si se especificó pero no existe
        print(f"ADVERTENCIA: Archivo de icono '{ICON_FILE}' no encontrado. Se usará el icono por defecto de PyInstaller.")
    else: # Si no se especificó ICON_FILE
        print(f"INFO: No se especificó archivo de icono. Se usará el icono por defecto de PyInstaller.")


    # Añadir datos (carpetas y archivos)
    for data_source, data_destination_in_bundle in DATA_TO_ADD:
        if os.path.exists(data_source):
            # El separador de rutas para --add-data es ';' en Windows, ':' en macOS/Linux
            path_separator = ';' if os.name == 'nt' else ':'
            command_args.extend(['--add-data', f'{os.path.abspath(data_source)}{path_separator}{data_destination_in_bundle}'])
            print(f"INFO: Añadiendo datos: '{data_source}' -> '{data_destination_in_bundle}'")
        else:
            print(f"ADVERTENCIA: La ruta de datos '{data_source}' no fue encontrada y no se incluirá.")

    # Añadir importaciones ocultas
    for hidden_import in HIDDEN_IMPORTS:
        command_args.extend(['--hidden-import', hidden_import])
    print(f"INFO: Importaciones ocultas añadidas: {', '.join(HIDDEN_IMPORTS)}")


    # Imprimir el comando completo que se va a ejecutar (para depuración)
    # Esto es útil si necesitas ejecutarlo manualmente o entender qué está pasando.
    pyinstaller_command_string = "pyinstaller " + " ".join(
        f'"{arg}"' if " " in arg else arg for arg in command_args
    )
    print(f"\nComando PyInstaller a ejecutar:\n{pyinstaller_command_string}\n")

    try:
        # Ejecutar PyInstaller
        PyInstaller.__main__.run(command_args)
        print(f"\n--- ¡Compilación de '{APP_NAME}' completada exitosamente! ---")
        print(f"El ejecutable y los archivos asociados están en la carpeta: dist/{APP_NAME}")
        if '--onefile' in PYINSTALLER_OPTIONS:
            print(f"El ejecutable único está en: dist/{APP_NAME}.exe (o similar según tu OS)")

    except SystemExit as e:
        # PyInstaller a veces sale con SystemExit(0) en éxito, lo cual no es un error real.
        if e.code == 0:
            print(f"\n--- ¡Compilación de '{APP_NAME}' completada (PyInstaller salió con código 0)! ---")
            print(f"El ejecutable y los archivos asociados están en la carpeta: dist/{APP_NAME}")
        else:
            print(f"\n--- Error durante la compilación con PyInstaller (SystemExit con código {e.code}) ---")
            print("Revisa los mensajes de error de PyInstaller arriba para más detalles.")
    except Exception as e:
        print(f"\n--- Error crítico durante la compilación con PyInstaller: {e} ---")
        print("Asegúrate de que PyInstaller esté instalado correctamente y que todas las rutas y configuraciones sean válidas.")
        print("Puede que necesites revisar los 'hidden imports' o cómo se manejan los archivos de datos.")

if __name__ == '__main__':
    # Verificar si el script principal existe en el directorio actual
    if not os.path.exists(MAIN_SCRIPT):
        print(f"Error: El script principal '{MAIN_SCRIPT}' no se encuentra en el directorio actual ({os.getcwd()}).")
        print(f"Por favor, ejecuta este script ({os.path.basename(__file__)}) desde la raíz de tu proyecto "
              f"(la carpeta que contiene '{MAIN_SCRIPT}').")
    else:
        # Opcional: Limpiar compilaciones anteriores antes de construir
        # print("Limpiando compilaciones anteriores (build/, dist/, *.spec)...")
        # if os.path.exists('build'):
        #     shutil.rmtree('build')
        # if os.path.exists('dist'):
        #     shutil.rmtree('dist')
        # spec_file = f"{APP_NAME}.spec"
        # if os.path.exists(spec_file):
        #    try:
        #        os.remove(spec_file)
        #    except Exception as e_rm_spec:
        #        print(f"Advertencia: No se pudo borrar {spec_file}: {e_rm_spec}")
        
        build_executable()
