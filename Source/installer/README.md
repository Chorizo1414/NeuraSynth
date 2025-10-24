# Instalador de NeuraSynth

Este directorio contiene herramientas y recursos para empaquetar NeuraSynth como un instalador moderno que distribuya tanto la aplicación Standalone como el plugin VST3.

## build_installer.py

`installer/build_installer.py` automatiza la creación de la estructura de carpetas, empaqueta recursos opcionales y genera, si estás en Windows, un script de [Inno Setup](https://jrsoftware.org/isinfo.php) listo para compilar el instalador `.exe`.

### Requisitos
- Haber compilado previamente NeuraSynth (standalone y VST3) con JUCE.
- Python 3.9 o superior.
- Opcional (Windows): Inno Setup (`iscc`) disponible en el `PATH` para generar el ejecutable automáticamente.

### Uso básico
```bash
python installer/build_installer.py \
    --standalone "build/NeuraSynth_artefacts/Release/Standalone/NeuraSynth.exe" \
    --vst3 "build/NeuraSynth_artefacts/Release/VST3/NeuraSynth.vst3" \
    --version 1.0.0 \
    --platform windows \
    --output dist \
    --logo resources/branding/neurasynth_logo.svg
```

El script creará:
- Una carpeta de *staging* con la estructura `Standalone/`, `VST3/`, `Resources/`, `Python/` (si los especificas) y documentación (`INSTALL.md`, `metadata.json`).
- Un archivo comprimido (`.zip` en Windows, `.tar.gz` en macOS/Linux).
- En Windows, un script `.iss` con la configuración de Inno Setup. Si `iscc` está presente, también intentará compilar el instalador automáticamente.

### Incluir Python y recursos adicionales
Añade las rutas con `--python-runtime` y `--resources` tantas veces como necesites:
```bash
python installer/build_installer.py \
    --standalone path/al/Standalone/NeuraSynth.exe \
    --vst3 path/al/VST3/NeuraSynth.vst3 \
    --version 1.0.0 \
    --platform windows \
    --python-runtime C:/Python38 \
    --python-runtime "Source/NeuraChord" \
    --resources "docs/Manual.pdf"
```

### Personalizar branding
El logo por defecto incluido en `resources/branding/neurasynth_logo.svg` replica la identidad visual del proyecto. Puedes reemplazarlo con tu propio archivo (`.svg`, `.png`, `.bmp`) utilizando el parámetro `--logo`. El archivo se copia al paquete y se enlaza automáticamente en el script de Inno Setup.

### Variables útiles
- `--skip-archive`: evita generar el `.zip`/`.tar.gz` si solo quieres el árbol de archivos o el script de Inno Setup.
- `--only-generate-scripts`: en Windows, genera el `.iss` pero no invoca `iscc`.
- `--license`: ruta a la licencia que se mostrará en el instalador de Inno Setup.
- `--company-name` y `--product-name`: ajustan los textos del instalador.

## Flujo recomendado
1. Compila NeuraSynth en modo *Release* para obtener el ejecutable standalone y el paquete `.vst3`.
2. Ejecuta `installer/build_installer.py` con la plataforma deseada.
3. (Windows) Abre o compila el `.iss` con Inno Setup para producir `NeuraSynth-<version>-Setup.exe`.
4. Distribuye el `.exe` y/o el archivo comprimido generado.

## Logo
El archivo `resources/branding/neurasynth_logo.svg` proporciona el logotipo utilizado en la versión standalone del sintetizador y en el instalador. Puedes sustituirlo por una versión vectorial diferente si necesitas otro idioma o variación cromática.