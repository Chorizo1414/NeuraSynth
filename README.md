# NeuraSynth

NeuraSynth es un instrumento virtual híbrido que combina un motor de síntesis wavetable escrito en C++/JUCE con generación asistida por IA para acordes, melodías y parches sonoros a través de scripts de Python. El proyecto incluye tanto el plugin de audio (VST3/AU/AAX/Standalone) como el conjunto de herramientas de composición "NeuraChord" integrado directamente en la interfaz.

## Tabla de contenidos
- [Arquitectura general](#arquitectura-general)
- [Flujo de datos](#flujo-de-datos)
- [Stack tecnológico y dependencias](#stack-tecnológico-y-dependencias)
- [Decisiones técnicas clave](#decisiones-técnicas-clave)
- [Configuración y requisitos previos](#configuración-y-requisitos-previos)
- [Instalación y construcción](#instalación-y-construcción)
- [Uso rápido](#uso-rápido)
- [Ejemplos avanzados](#ejemplos-avanzados)
- [Testing y CI/CD](#testing-y-cicd)
- [Roadmap y mantenimiento](#roadmap-y-mantenimiento)
- [Contribuciones y comunidad](#contribuciones-y-comunidad)
- [Licencia](#licencia)

## Arquitectura general

```mermaid
flowchart LR
    subgraph UI[Interfaz JUCE]
        SynthTab[SynthTabComponent\nOsc/Env/FX]
        ChordTab[ChordMelodyTabComponent\nPrompt + Piano Roll]
    end
    subgraph DSP[Motor de audio C++]
        Processor[NeuraSynthAudioProcessor]
        Voices[juce::Synthesiser + SynthVoice]
        FX[Delay/Reverb/Filter/Modulation]
    end
    subgraph Py[Runtime Python]
        PyMgr[PythonManager (pybind11)]
        Scripts[NeuraChord\nneurachord_api.py\netc.]
    end
    UI -->|Callbacks de parámetros| Processor
    Processor --> Voices
    Voices --> FX -->|Audio| Host
    ChordTab -->|Solicitudes| PyMgr --> Scripts
    Scripts -->|MIDI/Parches| ChordTab
    ChordTab -->|Reproducción/Drag| Processor
```

### Componentes principales
- **Motor de síntesis** (`PluginProcessor.*`, `BuiltInWavetables.*`, `SynthVoice`): tres osciladores wavetable con glide, unison, filtro SVF estéreo y envolvente analógica personalizada.
- **Interfaz de usuario** (`PluginEditor.*`, `SynthTabComponent.*`, componentes en `Source/*Component.*`): interfaz escalable con pestañas para el sinte y el generador de acordes/melodías.
- **Motor creativo NeuraChord** (`Source/NeuraChord/`): módulo Python con modelos heurísticos y basados en reglas para generar progresiones, melodías y presets de síntesis. Incluye exportación MIDI y aprendizaje incremental de sonidos.
- **Integración C++ ↔ Python** (`PythonManager.*`): gestiona el intérprete embebido, asegura acceso thread-safe mediante GIL y expone las funciones de `neurachord_api` al plugin.

## Flujo de datos

### Audio en tiempo real
1. El usuario ajusta controles en la pestaña *Synthesizer*.
2. Cada control invoca un setter en `NeuraSynthAudioProcessor`, sincronizando parámetros compartidos por todas las voces.
3. El host de audio invoca `processBlock`, que despacha eventos MIDI hacia `juce::Synthesiser`.
4. `SynthVoice::renderNextBlock` sintetiza cada voz usando las tablas cargadas, aplica unison, FM/LFO y filtra con el SVF estéreo.
5. La señal pasa por módulos de efectos (delay multitap, reverb) y finalmente se mezcla hacia la salida del host.

### Generación asistida por IA
1. El usuario introduce un *prompt* o parámetros en la pestaña *Chord/Melody Generator*.
2. El componente solicita datos al `PythonManager`, que asegura que el intérprete embebido esté inicializado y agrega las rutas de `NeuraChord` a `sys.path`.
3. `neurachord_api.py` ejecuta los pipelines de análisis de estilo, generación de progresión/melodía y diseño sonoro (dependen de `music21`, heurísticas propias y archivos en `Source/NeuraChord/estilos`).
4. Los datos devueltos (acordes, melodías, BPM, parches sugeridos) se muestran en la UI, se pueden arrastrar como MIDI al DAW o reproducir dentro del plugin.
5. Las ediciones del usuario pueden reenviarse a Python para reentrenar heurísticas sencillas (persistidas en `learned_sounds.json`).

## Stack tecnológico y dependencias

| Capa | Herramientas | Notas |
|------|--------------|-------|
| Motor de audio | [JUCE](https://juce.com/) 7, C++17 | Plugin multiformato (VST3, AU, AAX, Standalone). Utiliza `juce::dsp`, `juce::Synthesiser` y `AudioProcessorValueTreeState`. |
| Integración Python | [pybind11](https://pybind11.readthedocs.io/) embebido | Control explícito del GIL y rutas de `PYTHONHOME`. |
| Generación musical | Python 3.8+, `music21`, heurísticas en `Source/NeuraChord` | Generación basada en reglas y sentimiento, exportación MIDI con `music21`. |
| Recursos | `BinaryData` embebido por Projucer | Incluye wavetables, imágenes y archivos de estilo.

## Decisiones técnicas clave
- **Envolvente analógica custom**: `SynthVoice::AnalogEnvelope` implementa etapas con curvas exponenciales y control sobre exponentes de ataque, permitiendo transiciones más musicales que `juce::ADSR` estándar.
- **Filtro SVF TPT estéreo**: Cada voz ejecuta un filtro de estado variable transpuesto para mantener estabilidad con modulaciones de corte y seguimiento de nota.
- **Wavetables internos + externos**: Se prioriza la carga automática de wavetables desde disco, con fallback a recursos embebidos (`BuiltInWavetables`). Esto permite personalización sin romper builds.
- **Interfaz escalable**: `PluginEditor` usa `ComponentBoundsConstrainer` y `LayoutConstants` para conservar la relación de aspecto y facilitar un modo "design" para reajustar layouts.
- **Runtime Python persistente**: El intérprete se inicializa una vez por proceso para evitar crashes al descargar el plugin; los módulos se limpian en el destructor pero no se llama a `py::finalize_interpreter`.

## Configuración y requisitos previos

1. **Compilador soportado**: Clang 14+/MSVC 2022/GCC 11+ con C++17.
2. **JUCE**: Instalar el framework JUCE y Projucer o utilizar el módulo CMake.
3. **Python 3.8** (recomendado) con dependencias:
   ```bash
   pip install music21 numpy
   ```
4. **Variables de entorno**:
   - `PYTHONHOME` y `PYTHONPATH` deben apuntar a la instalación de Python y a `Source/NeuraChord`. El proyecto incluye rutas hardcodeadas para Windows (véase `PythonManager.cpp`); ajústalas a tu entorno antes de compilar para macOS/Linux.
   - Para personalizar sin editar C++, exporta antes de lanzar el host:
     ```bash
     set PYTHONHOME=C:\Rutas\Python38
     set PYTHONPATH=C:\ruta\al\repositorio\NeuraSynth\Source\NeuraChord
     ```
     o en Unix:
     ```bash
     export PYTHONHOME=$HOME/.pyenv/versions/3.8.18
     export PYTHONPATH=$PWD/Source/NeuraChord
     ```
5. **Recursos opcionales**: Coloca nuevos wavetables en `Source/wavetables` (multiplicidad de 2048 samples) para habilitar su carga desde la UI.

## Instalación y construcción

### Opción Projucer (GUI)
1. Abre `NeuraSynth/NeuraSynth.jucer` con Projucer.
2. Configura los *Exporters* deseados (Xcode, Visual Studio, Makefile, CMake). Asegúrate de añadir la ruta a tu Python en *Header Search Paths* si es necesario.
3. Resincroniza y abre el proyecto generado en tu IDE para compilar el plugin/standalone.

### Opción CMake (si prefieres CLI)
1. Genera un CMakeLists a partir de Projucer (`File > Exporters > CMake`).
2. Desde la carpeta de build:
   ```bash
   cmake -B build -S NeuraSynth -DJUCE_BUILD_EXAMPLES=OFF
   cmake --build build --config Release
   ```
3. El binario standalone y el bundle VST3 quedarán en `build/` bajo el exportador correspondiente.

### Empaquetado e instalador
Una vez compilados los binarios puedes generar un instalador listo para distribuir utilizando `installer/build_installer.py`:

```bash
python installer/build_installer.py \
    --standalone "build/NeuraSynth_artefacts/Release/Standalone/NeuraSynth.exe" \
    --vst3 "build/NeuraSynth_artefacts/Release/VST3/NeuraSynth.vst3" \
    --version 1.0.0 \
    --platform windows \
    --logo resources/branding/neurasynth_logo.svg
```

El script crea una carpeta de staging con la estructura esperada (`Standalone/`, `VST3/`, `Resources/`, `Python/`), genera documentación básica (`INSTALL.md`, `metadata.json`) y empaqueta el resultado (`.zip` en Windows, `.tar.gz` en macOS/Linux). En Windows también produce un script de [Inno Setup](https://jrsoftware.org/isinfo.php) para compilar el instalador `.exe`; si `iscc` está disponible lo invoca automáticamente.

Consulta [installer/README.md](installer/README.md) para opciones avanzadas (incluir runtimes de Python, recursos adicionales, personalizar branding, etc.).

## Uso rápido

1. **Standalone**: Ejecuta el binario generado, selecciona tu interfaz de audio/MIDI.
2. **Plugin**: Copia `NeuraSynth.vst3` en la carpeta estándar de tu DAW y escanéalo.
3. **Síntesis básica**:
   - Selecciona wavetables para los tres osciladores y ajusta ganancia/pan/spread.
   - Configura ADSR, filtro y modulaciones desde la sección central.
   - Añade efectos de delay/reverb desde sus paneles dedicados.
4. **Generación creativa**:
   - Abre la pestaña *Chord/Melody Generator*.
   - Introduce un prompt (por ejemplo: `"R&B suave con groove nocturno"`).
   - Opcional: define número de acordes, BPM o escala.
   - Pulsa *Generate*. Se poblará la lista de acordes, melodía y sugerencias de patch.
   - Usa los manejadores de drag-and-drop para exportar MIDI al DAW o sincroniza la reproducción interna con el sinte.

## Ejemplos avanzados

### 1. Cargar wavetables personalizados
```bash
mkdir -p Source/wavetables
cp ~/Samples/mis_tablas/*.wav Source/wavetables
```
Reinicia el plugin; las tablas aparecerán en los menús desplegables de cada oscilador. Asegúrate de que cada wavetable tenga un número de samples múltiplo de 2048 para una reproducción correcta.

### 2. Crear un preset a partir de un prompt sonoro
1. En la pestaña creativa, usa la opción *Design Sound* (expone `PythonManager::generateSynthSound`).
2. Introduce un prompt como `"Pad cálido, evolución lenta, brillo moderado"`.
3. El módulo Python devolverá parámetros sugeridos; aplícalos con un solo clic para inicializar los controles del sinte.

### 3. Reorquestar una progresión existente
```python
from neurachord_api import generar_progresion, exportar_acordes_midi
progresion = generar_progresion("Lofi hip hop con toques japoneses", num_chords=8)
exportar_acordes_midi(progresion["acordes"], progresion["ritmo"], bpm=78)
```
Importa el MIDI resultante en el DAW o arrástralo desde el plugin.

## Testing y CI/CD
- **Audio DSP**: actualmente se valida mediante pruebas auditivas y análisis en DAWs (no hay pruebas automatizadas). Recomendación: implementar *unit tests* con `juce::UnitTest` para el filtro y la envolvente.
- **Python**: se puede ejecutar `pytest` dentro de `Source/NeuraChord` para validar las funciones de generación (no incluido por defecto).
- **CI/CD sugerido**: usar GitHub Actions con matrices para compilar el plugin en Windows/macOS, ejecutar validaciones de formato (`clang-format`, `black`) y pruebas de Python.

## Roadmap y mantenimiento
- [ ] Migrar rutas de `PYTHONHOME` a configuración externa o archivo `.ini` multiplataforma.
- [ ] Añadir presets guardables y sistema de snapshots.
- [ ] Implementar automatización de parámetros a través de `AudioProcessorValueTreeState` para facilitar mapeo en DAWs.
- [ ] Incluir una suite mínima de pruebas automáticas y análisis estático (Clang-Tidy).
- [ ] Documentar API pública de `neurachord_api` para su uso externo.

## Contribuciones y comunidad

1. Haz un fork y crea una rama con un nombre descriptivo (`feature/wavetable-import`).
2. Sigue el estilo existente (C++17, `clang-format` estilo LLVM/Google). Evita envolver includes en `try/catch`.
3. Asegúrate de que los prompts de Python gestionen caracteres UTF-8; añade pruebas manuales.
4. Abre un Pull Request describiendo:
   - Motivación del cambio.
   - Impacto en DSP y/o integración Python.
   - Pasos de validación manual o scripts ejecutados.
5. Usa los *Issues* para sugerir wavetables nuevos, géneros adicionales o mejoras de UI.

## Licencia

Incluye aquí el texto de licencia correspondiente (MIT, GPL, etc.). Si la licencia aún no está definida, añade una nota indicando que está "Por determinar" antes de publicar el repositorio.
