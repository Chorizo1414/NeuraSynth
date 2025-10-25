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

> 💡 **Sugerencia:** si omites `--standalone`, `--vst3` o `--version`, el script intentará detectarlos automáticamente
> buscando en las carpetas de compilación típicas (`Builds/VisualStudio20xx/.../Release`, `build/**/Release`, etc.) y
> leyendo la versión desde Git. Aun así puedes sobreescribir cualquier valor pasando el parámetro explícito.

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
El parámetro `--logo` es opcional: si no lo proporcionas, el script buscará `installer/resources/icon.png` automáticamente. Ese archivo replica la identidad visual del proyecto y puedes reemplazarlo con tu propio recurso (`.png`, `.bmp`, `.ico`).

Cuando el logo es un `.png`, el script genera automáticamente un `.ico` en la carpeta `branding/` para que los accesos directos de Windows y el instalador utilicen la misma imagen. Si proporcionas directamente un `.ico`, se reutiliza tal cual. El logo original (PNG/BMP) se sigue copiando para que puedas mostrarlo en documentación o en el propio instalador.

### Variables útiles
- `--skip-archive`: evita generar el `.zip`/`.tar.gz` si solo quieres el árbol de archivos o el script de Inno Setup.
- `--only-generate-scripts`: en Windows, genera el `.iss` pero no invoca `iscc`.
- `--license`: ruta a la licencia que se mostrará en el instalador de Inno Setup.
- `--company-name` y `--product-name`: ajustan los textos del instalador.

## Flujo recomendado
1. Compila NeuraSynth en modo *Release* para obtener el ejecutable standalone y el paquete `.vst3`.
2. Ejecuta `installer/build_installer.py` con la plataforma deseada.
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

## Logo
El archivo `resources/branding/neurasynth_logo.svg` proporciona el logotipo utilizado en la versión standalone del sintetizador y en el instalador. Puedes sustituirlo por una versión vectorial diferente si necesitas otro idioma o variación cromática.

Para que la ventana standalone y la barra de tareas de Windows muestren el icono correcto, la imagen también se empaqueta en el binario mediante `Source/pictures/app_icon.png`. Si actualizas el logo, recuerda reemplazar ambos archivos (o ejecutar nuevamente el script para copiar el recurso actualizado).