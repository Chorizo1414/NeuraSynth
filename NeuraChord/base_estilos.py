# base_estilos.py
import importlib.util
import os

INFO_GENERO = {}

# Ruta a la carpeta de estilos
carpeta_estilos = os.path.join(os.path.dirname(__file__), "estilos")

if os.path.exists(carpeta_estilos) and os.path.isdir(carpeta_estilos):
    for archivo in os.listdir(carpeta_estilos):
        if archivo.startswith("base_") and archivo.endswith(".py"):
            nombre_genero = archivo.replace("base_", "").replace(".py", "") # ej: "reggaeton"
            ruta_completa_archivo_estilo = os.path.join(carpeta_estilos, archivo)

            try:
                spec = importlib.util.spec_from_file_location(f"estilos.dinamico.{nombre_genero}", ruta_completa_archivo_estilo) # Nombre de módulo único
                if spec and spec.loader:
                    modulo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(modulo)

                    if hasattr(modulo, "INFO_GENERO"):
                        # INFO_GENERO dentro del archivo base_genero.py tiene la forma:
                        # {'nombre_del_genero_en_el_archivo': {'tonalidad1': ..., 'tonalidad2': ..., 'patrones_ritmicos': ...}}
                        datos_cargados_del_archivo = getattr(modulo, "INFO_GENERO")
                        
                        # Esperamos que la clave principal dentro de datos_cargados_del_archivo sea el nombre del género.
                        if nombre_genero in datos_cargados_del_archivo:
                            INFO_GENERO[nombre_genero] = datos_cargados_del_archivo[nombre_genero]
                        else:
                            # Si la clave del género no está, podría ser un formato antiguo o un error.
                            # Opcionalmente, se podría intentar usar todo el diccionario si solo hay un género por archivo.
                            # Por ahora, seremos estrictos con la nueva estructura.
                            print(f"Advertencia (base_estilos.py): La clave del género '{nombre_genero}' no se encontró "
                                  f"directamente dentro de la variable INFO_GENERO en el archivo '{archivo}'. "
                                  f"Se esperaba una estructura como {{'{nombre_genero}': {{...datos...}}}}. "
                                  f"Contenido real: {list(datos_cargados_del_archivo.keys())}")
                            # Podrías decidir asignar datos_cargados_del_archivo directamente si es apropiado:
                            # INFO_GENERO[nombre_genero] = datos_cargados_del_archivo

                else: # if spec and spec.loader
                    print(f"Advertencia (base_estilos.py): No se pudo crear spec.loader para '{archivo}'.")
            except Exception as e_load_module:
                print(f"Error crítico cargando o procesando el módulo de estilo '{archivo}': {e_load_module}")
else:
    print(f"Advertencia (base_estilos.py): La carpeta de estilos '{carpeta_estilos}' no existe o no es un directorio.")

if not INFO_GENERO:
    print("INFO_GENERO está vacío después de intentar cargar estilos. Asegúrate de que los archivos base_<genero>.py existan y tengan la estructura correcta.")