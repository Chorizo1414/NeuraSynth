# Instalador de NeuraSynth

Este directorio contiene herramientas y recursos para empaquetar NeuraSynth como un instalador moderno que distribuya tanto la aplicación Standalone como el plugin VST3.

## build_installer.py

`Source/installer/build_installer.py` automatiza la creación de la estructura de carpetas, empaqueta recursos opcionales y genera, si estás en Windows, un script de [Inno Setup](https://jrsoftware.org/isinfo.php) listo para compilar el instalador `.exe`.

### Requisitos
- Haber compilado previamente NeuraSynth (standalone y VST3) con JUCE.
- Python 3.9 o superior.
- Opcional (Windows): Inno Setup (`iscc`) disponible en el `PATH` para generar el ejecutable automáticamente.

### Uso básico
```bash
python Source/installer/build_installer.py \
    --standalone "build/NeuraSynth_artefacts/Release/Standalone/NeuraSynth.exe" \
    --vst3 "build/NeuraSynth_artefacts/Release/VST3/NeuraSynth.vst3" \
    --version 1.0.0 \
    --platform windows \
    --output dist \
    --logo Source/installer/resources/branding/neurasynth_logo.svg
```

> 💡 **Sugerencia:** si omites `--standalone`, `--vst3` o `--version`, el script intentará detectarlos automáticamente
> buscando en las carpetas de compilación típicas (`Builds/VisualStudio20xx/.../Release`, `build/**/Release`, etc.) y
> leyendo la versión desde Git. Aun así puedes sobreescribir cualquier valor pasando el parámetro explícito.

### Dependencias obligatorias en Windows

Para generar correctamente el instalador de Windows debes proporcionar:

- `VC_redist.x64.exe` (Visual C++ Redistributable 2015-2022).
- `python-3.8.10-amd64.exe` (instalador oficial de Python).

Colócalos dentro de `Source/installer/resources/` para que se detecten automáticamente o indica sus rutas con `--vc-redist` y `--python-installer`. Durante la compilación, ambos se copian a `Dependencies/` dentro del staging y el script `.iss` los extrae en modo silencioso antes de finalizar la instalación.

El script creará:
- Una carpeta de *staging* con la estructura `Standalone/`, `VST3/`, `Resources/`, `Python/` (si los especificas) y documentación (`INSTALL.md`, `metadata.json`). El archivo `INSTALL.md` incluye una advertencia explícita para ejecutar el instalador como administrador y detalla que el plugin VST3 se copiará en `C:\Program Files\Common Files\VST3` mientras que el runtime de Python se desplegará en `C:\ProgramData\NeuraSynth\Python`.
- Un archivo comprimido (`.zip` en Windows, `.tar.gz` en macOS/Linux).
- En Windows, un script `.iss` con la configuración de Inno Setup. Si `iscc` está presente, también intentará compilar el instalador automáticamente con las rutas estándar (`{autopf64}\NeuraSynth` para la aplicación y `{commoncf64}\VST3` para el plugin) y permisos heredados para que cualquier usuario pueda cargar el VST3.

### Incluir Python y recursos adicionales

El script empaqueta automáticamente `Source/NeuraChord` dentro de la carpeta `Python/` porque es imprescindible para que el motor funcione. Además, si detecta un runtime embebido en `Source/installer/python-runtime/<plataforma>/`, lo copia sin que tengas que pasar parámetros extra.

A partir de esta versión, el empaquetador también clona automáticamente los módulos críticos `music21`, `numpy`, `pygame`, `tkinterdnd2`, `PIL`, `fuzzywuzzy` y `customtkinter` desde el entorno de Python con el que ejecutes `build_installer.py`. Si alguno falta, mostrará una advertencia para que puedas instalarlo antes de volver a generar el paquete. Puedes añadir módulos adicionales con `--python-package`, desactivar los predeterminados con `--no-default-python-packages` y omitir sus dependencias transitivas con `--skip-python-package-deps` cuando lo necesites.

Si deseas sobreescribir esta selección (por ejemplo para añadir una versión distinta del runtime, librerías adicionales o documentación), añade las rutas con `--python-runtime` y `--resources` tantas veces como necesites:
```bash
python Source/installer/build_installer.py \
    --standalone path/al/Standalone/NeuraSynth.exe \
    --vst3 path/al/VST3/NeuraSynth.vst3 \
    --version 1.0.0 \
    --platform windows \
    --python-runtime C:/Python38 \
    --python-runtime "Source/NeuraChord" \
    --resources "docs/Manual.pdf"
```

> 💾 **Runtime recomendado:** descarga la [distribución embebida de Python](https://www.python.org/downloads/windows/) (por ejemplo `python-3.8.x-embed-amd64.zip`), descomprímela dentro de `Source/installer/python-runtime/windows/` y vuelve a ejecutar el script. Verás un mensaje indicando que se detectó automáticamente.

Si el paquete resultante no contiene archivos como `python38.dll`, el standalone mostrará un error al abrirse en máquinas que no tengan Python instalado. El script avisará con una advertencia cuando detecte este escenario.

### Personalizar branding
El parámetro `--logo` es opcional: si no lo proporcionas, el script buscará `Source/installer/resources/icon.png` automáticamente. Ese archivo replica la identidad visual del proyecto y puedes reemplazarlo con tu propio recurso (`.png`, `.bmp`, `.ico`).

Cuando el logo es un `.png`, el script genera automáticamente un `.ico` en la carpeta `branding/` para que los accesos directos de Windows y el instalador utilicen la misma imagen. Si proporcionas directamente un `.ico`, se reutiliza tal cual. El logo original (PNG/BMP) se sigue copiando para que puedas mostrarlo en documentación o en el propio instalador. Asegúrate de que cualquier PNG utilizado para este fin no supere los 256×256 píxeles, que es el tamaño máximo admitido por el conversor integrado y por Inno Setup.

### Variables útiles
- `--skip-archive`: evita generar el `.zip`/`.tar.gz` si solo quieres el árbol de archivos o el script de Inno Setup.
- `--only-generate-scripts`: en Windows, genera el `.iss` pero no invoca `iscc`.
- `--license`: ruta a la licencia que se mostrará en el instalador de Inno Setup.
- `--company-name` y `--product-name`: ajustan los textos del instalador.

## Flujo recomendado
1. Compila NeuraSynth en modo *Release* para obtener el ejecutable standalone y el paquete `.vst3`.
2. Ejecuta `Source/installer/build_installer.py` con la plataforma deseada.
3. Revisa el resumen JSON impreso por el script: verás la carpeta de *staging*, los archivos comprimidos y, en Windows, la ruta del script `.iss` generado.
4. (Windows) Si `iscc` no estaba en tu `PATH`, abre `dist/windows/<producto>-<versión>.iss` con Inno Setup Compiler y compílalo manualmente para producir `NeuraSynth-<versión>-Setup.exe`.
5. Distribuye el `.exe` y/o el archivo comprimido generado.

### ¿Qué hacer después de generar los artefactos?
- **Verifica la carpeta de staging** (`dist/staging/...`) para confirmar que el standalone, el VST3 y los recursos adicionales se copiaron correctamente.
- **Prueba los binarios directamente** desde la carpeta de staging antes de empaquetarlos o firmarlos.
- **Personaliza el instalador**: dentro del script `.iss` puedes ajustar textos, iconos o rutas adicionales si necesitas un flujo más complejo.
- **Firma y versiona** los artefactos finales según las políticas de tu organización antes de publicarlos.

## Checklist de lanzamiento
Antes de compartir el instalador con otros usuarios, valida estos puntos:

1. **Prueba el modo standalone** desde la carpeta de *staging* generada (`dist/staging/.../Standalone`). Comprueba que el logo y la animación del latido aparecen al abrir la aplicación.
2. **Instala el plugin VST3 manualmente** copiando `VST3/NeuraSynth.vst3` en la carpeta estándar de tu sistema y verifica que tu DAW lo reconoce.
3. **Revisa los recursos adicionales** (presets, documentación, runtimes de Python) dentro de `Resources/` y `Python/` si los incluiste.
4. **Ejecuta el instalador compilado** (si usaste Inno Setup) en una máquina de pruebas limpia o en una máquina virtual para asegurarte de que copia los archivos correctos.
5. **Actualiza la versión** en `--version` y en cualquier documento de lanzamiento/notas de cambios antes de subir los artefactos finales.

## SmartScreen y firma de código

Para evitar el mensaje de *"No se descarga habitualmente"* que muestra SmartScreen, es necesario firmar tanto el instalador como el ejecutable standalone con un certificado válido (Authenticode). Una vez que generes `NeuraSynth-<versión>-Setup.exe` y `Standalone/NeuraSynth.exe`, firma ambos con `signtool` u otra herramienta equivalente. Si trabajas con un certificado EV, la reputación de SmartScreen se acumulará más rápido. Sin la firma, Windows advertirá a los usuarios que el binario es de "editor desconocido".

Cuando utilices `signtool`, recuerda firmar primero el ejecutable standalone y después el instalador para que éste pueda encapsular la firma interna:

```powershell
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a "dist/staging/.../Standalone/NeuraSynth.exe"
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a "dist/windows/NeuraSynth-<versión>-Setup.exe"
```

Tras la firma, vuelve a ejecutar el instalador en una máquina de pruebas para verificar que Windows muestra al emisor correcto en lugar de "Desconocido".

## Variables de entorno opcionales

En tiempo de ejecución puedes forzar rutas personalizadas sin recompilar:

- `NEURASYNTH_PYTHON_HOME`: apunta al directorio que contiene `python38.dll` (u otra versión embebida). Si está definido, la aplicación lo utilizará antes de buscar en `Program Files\NeuraSynth\Python` o `CommonAppData`.
- `NEURASYNTH_PYTHON_MODULE`: permite indicar la carpeta donde vive `neurachord_api.py` cuando quieras probar parches externos.

Estas variables son útiles para depurar instalaciones en las que se quiera aislar el runtime o para ejecutar desde un pendrive antes de empaquetar definitivamente.

## Logo
El archivo `Source/installer/resources/branding/neurasynth_logo.svg` proporciona el logotipo utilizado en la versión standalone del sintetizador y en el instalador. Puedes sustituirlo por una versión vectorial diferente si necesitas otro idioma o variación cromática.

Para que la ventana standalone y la barra de tareas de Windows muestren el icono correcto, la imagen también se empaqueta en el binario mediante `Source/pictures/app_icon.png`. Si actualizas el logo, recuerda reemplazar ambos archivos (o ejecutar nuevamente el script para copiar el recurso actualizado).
