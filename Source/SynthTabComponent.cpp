#include "SynthTabComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"

namespace
{
    juce::File findDefaultWavetableDirectory()
    {
        const juce::StringArray relativeCandidates
        {
            "wavetables",
            "Source/wavetables",
            "Resources/wavetables",
            "Contents/Resources/wavetables"
        };

        juce::Array<juce::File> searchRoots;

        auto addSearchRoot = [&searchRoots](const juce::File& file)
            {
                if (!file.exists())
                    return;

                auto directory = file.isDirectory() ? file : file.getParentDirectory();
                if (directory.exists() && !searchRoots.contains(directory))
                    searchRoots.add(directory);
            };

        addSearchRoot(juce::File::getSpecialLocation(juce::File::currentApplicationFile));
        addSearchRoot(juce::File::getSpecialLocation(juce::File::invokedExecutableFile));
        addSearchRoot(juce::File::getSpecialLocation(juce::File::currentExecutableFile));
        addSearchRoot(juce::File::getCurrentWorkingDirectory());

        for (auto root : searchRoots)
        {
            auto current = root;
            for (int depth = 0; depth < 5 && current.exists(); ++depth)
            {
                for (const auto& relative : relativeCandidates)
                {
                    auto candidate = current.getChildFile(relative);
                    if (candidate.isDirectory())
                        return candidate;
                }

                auto parent = current.getParentDirectory();
                if (parent == current || !parent.exists())
                    break;

                current = parent;
            }
        }

        return {};
    }
}

// El constructor ahora recibe la referencia al procesador
SynthTabComponent::SynthTabComponent(NeuraSynthAudioProcessor& p)
    : audioProcessor(p),
    modulationComp(p),
    reverbSection(p),
    masterSection(p),
    delaySection(p),
    filterSection(p),
    envelopeSection(p),
    designMouseListener(componentDragger, this)
{
    setWantsKeyboardFocus(true);
    backgroundImage = juce::ImageCache::getFromMemory(BinaryData::boceto_png, BinaryData::boceto_pngSize);

    // Asignamos nombres para el modo dise     osc1.setName("Oscillator 1");
    osc2.setName("Oscillator 2");
    osc3.setName("Oscillator 3");
    unisonComp1.setName("Unison 1");
    unisonComp2.setName("Unison 2");
    unisonComp3.setName("Unison 3");
    masterSection.setName("Master Section");
    reverbSection.setName("Reverb Section");
    delaySection.setName("Delay Section");
    modulationComp.setName("Modulation Section");

    // --- SECCI N OSCILADORES ---
    addAndMakeVisible(osc1);
    addAndMakeVisible(osc2);
    addAndMakeVisible(osc3);

    auto setupOscillatorKnobs = [](OscillatorComponent& osc)
        {

            // Octave: 0 (centro) en un rango de -2 a 2
            osc.octKnob.setRange(-2.0, 2.0, 1.0);
            osc.octKnob.setValue(0.0);

            // Fine: 0 (centro) en un rango de -50 a 50 cents
            osc.fineKnob.setRange(-50.0, 50.0);
            osc.fineKnob.setValue(0.0);

            // Pitch: 0 (centro) en un rango de -12 a 12 semitonos
            osc.pitchKnob.setRange(-12.0, 12.0, 1.0);
            osc.pitchKnob.setValue(0.0);

            // Spread: 0.0 (mono) a 0.5 (ancho completo)
            osc.spreadKnob.setRange(0.0, 2.5);
            osc.spreadKnob.setValue(0.0);

            // Pan (L/R): 0.5 (centro)
            osc.panKnob.setRange(0.0, 1.0);
            osc.panKnob.setValue(0.5);

            // Position: 0.0 (izquierda)
            osc.positionKnob.setRange(0.0, 1.0);
            osc.positionKnob.setValue(0.0);

            // Gain: 0.5 (centro)
            osc.gainKnob.setRange(0.0, 1.0);
            osc.gainKnob.setValue(0.5);
        };

    setupOscillatorKnobs(osc1);
    setupOscillatorKnobs(osc2);
    setupOscillatorKnobs(osc3);

    // Conexi n de Callbacks para el Oscilador 1 (el que est  activo)
    osc1.oscSection.onWaveLoaded = [this](const juce::AudioBuffer<float>& buffer) {
        audioProcessor.setWavetable1(buffer); // <-- CORREGIDO
        osc1.waveDisplay.setAudioBuffer(buffer, audioProcessor.getNumFrames1());
        };
    osc1.gainKnob.onValueChange = [this]() { audioProcessor.setOsc1Gain(osc1.gainKnob.getValue()); };
    osc1.panKnob.onValueChange = [this]() { audioProcessor.setOsc1Pan(osc1.panKnob.getValue()); };
    osc1.octKnob.onValueChange = [this]() { audioProcessor.setOsc1Octave(static_cast<int>(osc1.octKnob.getValue())); };
    osc1.pitchKnob.onValueChange = [this]() { audioProcessor.setOsc1Pitch(static_cast<int>(osc1.pitchKnob.getValue())); };
    osc1.fineKnob.onValueChange = [this]() { audioProcessor.setOsc1FineTune(osc1.fineKnob.getValue()); };
    osc1.spreadKnob.onValueChange = [this]() { audioProcessor.setOsc1Spread(osc1.spreadKnob.getValue()); };
    osc1.positionKnob.onValueChange = [this]() {
        float newPosition = osc1.positionKnob.getValue();
        audioProcessor.setWavePosition1(newPosition); // <-- CORREGIDO
        osc1.waveDisplay.setDisplayPosition(newPosition);
        };

    // Conexi n de displays para OSC2 y OSC3 (solo visual, sin afectar audio)
    osc2.oscSection.onWaveLoaded = [this](const juce::AudioBuffer<float>& buffer) {
        audioProcessor.setWavetable2(buffer); // <-- CORREGIDO
        osc2.waveDisplay.setAudioBuffer(buffer, audioProcessor.getNumFrames2());
        };
    osc2.gainKnob.onValueChange = [this]() { audioProcessor.setOsc2Gain(osc2.gainKnob.getValue()); };
    osc2.panKnob.onValueChange = [this]() { audioProcessor.setOsc2Pan(osc2.panKnob.getValue()); };
    osc2.octKnob.onValueChange = [this]() { audioProcessor.setOsc2Octave(static_cast<int>(osc2.octKnob.getValue())); };
    osc2.pitchKnob.onValueChange = [this]() { audioProcessor.setOsc2Pitch(static_cast<int>(osc2.pitchKnob.getValue())); };
    osc2.fineKnob.onValueChange = [this]() { audioProcessor.setOsc2FineTune(osc2.fineKnob.getValue()); };
    osc2.spreadKnob.onValueChange = [this]() { audioProcessor.setOsc2Spread(osc2.spreadKnob.getValue()); };
    osc2.positionKnob.onValueChange = [this]() {
        float newPosition = osc2.positionKnob.getValue();
        audioProcessor.setWavePosition2(newPosition); // <-- CORREGIDO
        osc2.waveDisplay.setDisplayPosition(newPosition);
        };

    // --- Conexi n de Callbacks para el Oscilador 3 ---
    osc3.oscSection.onWaveLoaded = [this](const juce::AudioBuffer<float>& buffer) {
        audioProcessor.setWavetable3(buffer);
        if (buffer.getNumSamples() > 0 && buffer.getNumSamples() % 2048 == 0)
            osc3.waveDisplay.setAudioBuffer(buffer, audioProcessor.getNumFrames3());
        };
    osc3.gainKnob.onValueChange = [this]() { audioProcessor.setOsc3Gain(osc3.gainKnob.getValue()); };
    osc3.panKnob.onValueChange = [this]() { audioProcessor.setOsc3Pan(osc3.panKnob.getValue()); };
    osc3.octKnob.onValueChange = [this]() { audioProcessor.setOsc3Octave(static_cast<int>(osc3.octKnob.getValue())); };
    osc3.pitchKnob.onValueChange = [this]() { audioProcessor.setOsc3Pitch(static_cast<int>(osc3.pitchKnob.getValue())); };
    osc3.fineKnob.onValueChange = [this]() { audioProcessor.setOsc3FineTune(osc3.fineKnob.getValue()); };
    osc3.spreadKnob.onValueChange = [this]() { audioProcessor.setOsc3Spread(osc3.spreadKnob.getValue()); };
    osc3.positionKnob.onValueChange = [this]() {
        float newPosition = osc3.positionKnob.getValue();
        audioProcessor.setWavePosition3(newPosition);
        osc3.waveDisplay.setDisplayPosition(newPosition);
        };

    // Carga de wavetables en cada secci n
    auto waveFolder = findDefaultWavetableDirectory();
    if (waveFolder.exists())
    {
        auto waveFolderPath = waveFolder.getFullPathName();
        osc1.oscSection.loadWavetablesFromFolder(waveFolderPath);
        osc2.oscSection.loadWavetablesFromFolder(waveFolderPath);
        osc3.oscSection.loadWavetablesFromFolder(waveFolderPath);
    }
    else
    {
        DBG("No se encontr・la carpeta de wavetables en las rutas esperadas.");
    }

    // --- SECCI N UNISON ---
    addAndMakeVisible(unisonComp1);
    addAndMakeVisible(unisonComp2);
    addAndMakeVisible(unisonComp3);

    // Conexi n de Callbacks para el Unison del Oscilador 1
    unisonComp1.onVoicesChanged = [this](int voices) { audioProcessor.setOsc1UnisonVoices(voices); };
    unisonComp1.onDetuneChanged = [this](float detune) { audioProcessor.setOsc1UnisonDetune(detune); };
    unisonComp1.onBalanceChanged = [this](float balance) { audioProcessor.setOsc1UnisonBalance(balance); };
    // (Los callbacks para unison 2 y 3 se a adir n cuando el procesador los soporte)

    // Agregar y configurar controles de master
    addAndMakeVisible(masterSection);

    // --- SECCI N FILTER ---
    addAndMakeVisible(filterSection);

    // --- SECCI N ENVELOPE ---
    addAndMakeVisible(envelopeSection);

    // --- SECCI N MODULACI N (LFO & FM) ---
    addAndMakeVisible(modulationComp);

    // --- SECCI N REVERB ---
    addAndMakeVisible(reverbSection);

    // --- SECCI N DELAY ---
    addAndMakeVisible(delaySection);

    addAndMakeVisible(soundPromptEditor);

    // --- Inicializaci de los nuevos botones de historial ---
    generateButton.setButtonText("Generate");
    addAndMakeVisible(generateButton);
    // Asignamos la misma funci que presionar Enter en el editor de texto
    generateButton.onClick = [this] { textEditorReturnKeyPressed(soundPromptEditor); };

    undoButton.setButtonText("Undo");
    addAndMakeVisible(undoButton);
    undoButton.onClick = [this] { undoButtonClicked(); };

    redoButton.setButtonText("Redo");
    addAndMakeVisible(redoButton);
    redoButton.onClick = [this] { redoButtonClicked(); };

    // Establecemos el estado inicial de los botones (deshabilitados)
    updateUndoRedoButtonStates();

    // --- Inicialización de los botones de feedback ---
    likeButton.setButtonText(juce::CharPointer_UTF8("\xf0\x9f\x91\x8d")); // Emoji 👍
    addAndMakeVisible(likeButton);
    likeButton.onClick = [this] {
        // Llamamos a la función y guardamos el resultado
        bool success = audioProcessor.pythonManager->likeLastSound();

        // Mostramos un mensaje dependiendo del resultado
        if (success)
        {
            juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::InfoIcon,
                "Preset Guardado",
                "Preset guardado en favoritos");
        }
        else
        {
            juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon,
                "Error",
                "No se pudo guardar. Genera un sonido nuevo antes de darle 'Like'.");
        }
        };

    dislikeButton.setButtonText(juce::CharPointer_UTF8("\xf0\x9f\x91\x8e")); // Emoji 👎
    addAndMakeVisible(dislikeButton);
    dislikeButton.onClick = [this] {
        // La acción de "dislike" simplemente genera un nuevo sonido
        textEditorReturnKeyPressed(soundPromptEditor);
    };

    // --- Inicialización de los componentes de presets ---
    addAndMakeVisible(presetLabel);
    presetLabel.setText("Presets:", juce::dontSendNotification);
    presetLabel.setJustificationType(juce::Justification::centredRight);

    addAndMakeVisible(presetSelector);
    presetSelector.setTextWhenNoChoicesAvailable("No hay presets guardados");
    presetSelector.onChange = [this] {
        int selectedId = presetSelector.getSelectedId();
        if (selectedId > 0) // ID 0 es "ninguno seleccionado"
        {
            juce::String presetName = presetSelector.getItemText(selectedId - 1);
            if (currentPresets.contains(presetName.toStdString().c_str()))
            {
                pybind11::dict patch = currentPresets[presetName.toStdString().c_str()].cast<pybind11::dict>();
                applyPatchFromPython(patch);
                audioProcessor.applyPatchFromPython(patch);
            }
        }
        };

    addAndMakeVisible(refreshPresetsButton);
    refreshPresetsButton.setButtonText("Refrescar");
    refreshPresetsButton.onClick = [this] { populatePresets(); };

    populatePresets(); // Llenamos los presets al iniciar

    soundPromptEditor.setMultiLine(false);
    soundPromptEditor.setReturnKeyStartsNewLine(false);
    soundPromptEditor.setReadOnly(false);
    soundPromptEditor.setScrollbarsShown(false);
    soundPromptEditor.setCaretVisible(true);
    soundPromptEditor.setPopupMenuEnabled(true);
    soundPromptEditor.setTextToShowWhenEmpty("Escribe un sonido (ej: 'Warm Lead', 'Bright Pad')...", juce::Colours::darkgrey);

    addAndMakeVisible(soundPromptLabel);
    soundPromptLabel.setText("Generador de Sonido:", juce::dontSendNotification);
    soundPromptLabel.attachToComponent(&soundPromptEditor, true);

    soundPromptEditor.addListener(this);

    if (designMode)
    {
        masterSection.addMouseListener(&designMouseListener, true);

        osc1.addMouseListener(&designMouseListener, true);
        osc2.addMouseListener(&designMouseListener, true);
        osc3.addMouseListener(&designMouseListener, true);

        unisonComp1.addMouseListener(&designMouseListener, true);
        unisonComp2.addMouseListener(&designMouseListener, true);
        unisonComp3.addMouseListener(&designMouseListener, true);

        filterSection.addMouseListener(&designMouseListener, true);

        envelopeSection.addMouseListener(&designMouseListener, true);

        modulationComp.addMouseListener(&designMouseListener, true);

        reverbSection.addMouseListener(&designMouseListener, true);

        delaySection.addMouseListener(&designMouseListener, true);

    }

    // -- - Selector de Tama o-- -
    addAndMakeVisible(sizeLabel);
    sizeLabel.setText("Size:", juce::dontSendNotification);
    sizeLabel.setJustificationType(juce::Justification::centredRight);

    addAndMakeVisible(sizeComboBox);
    sizeComboBox.addItem("75%", 1);
    sizeComboBox.addItem("100%", 2);
    sizeComboBox.setSelectedId(2);

    sizeComboBox.onChange = [this]
    {
            // Usamos la función correcta para obtener la ventana principal del plugin
            if (auto* parent = findParentComponentOfClass<juce::TopLevelWindow>())
            {
                float finalScale = 0.5f; // Valor por defecto para 100%
                int choice = sizeComboBox.getSelectedId();
                if (choice == 1) finalScale = 0.375f; // 75%
                if (choice == 2) finalScale = 0.5f;   // 100%

                const int newWidth = LayoutConstants::DESIGN_WIDTH * finalScale;
                const int newHeight = LayoutConstants::DESIGN_HEIGHT * finalScale;
                parent->setSize(newWidth, newHeight);
            }
    };

}

SynthTabComponent::~SynthTabComponent()
{
}

void SynthTabComponent::paint(juce::Graphics& g)
{
    // 1. Rellena todo el fondo de negro. Este ser  el color base para la secci n del piano.
    g.fillAll(juce::Colours::black);

    // 2. Calcula la altura actual del teclado para saber d nde termina la secci n de la GUI.
    //    Esta l gica es id	ntica a la de `resized()` para que siempre est	n sincronizadas.
    const float widthScale = (float)getWidth() / LayoutConstants::DESIGN_WIDTH;
    int keyboardHeight = LayoutConstants::KEYBOARD_HEIGHT * widthScale;
    if (keyboardHeight < 0) keyboardHeight = 0;
    juce::Rectangle<int> guiArea = getLocalBounds().withTrimmedBottom(keyboardHeight);

    // 3. Dibuja la imagen de fondo SOLAMENTE en el  rea superior (guiArea).
    if (backgroundImage.isValid())
    {
        g.drawImage(backgroundImage, guiArea.toFloat(), juce::RectanglePlacement::fillDestination);
    }
}

void SynthTabComponent::resized()
{
    // --- 1. Define el área para el teclado (Esto no cambia) ---
    const float widthScale = (float)getWidth() / LayoutConstants::DESIGN_WIDTH;
    int keyboardHeight = LayoutConstants::KEYBOARD_HEIGHT * widthScale;
    if (keyboardHeight < 0) keyboardHeight = 0;

    // --- 2. Define el área para la GUI (Esto no cambia) ---
    guiArea = getLocalBounds().withTrimmedBottom(keyboardHeight);

    // --- 3. LOGICA DE ESCALADO SIMPLIFICADA (Esto no cambia) ---
    const float scale = (float)guiArea.getWidth() / LayoutConstants::DESIGN_WIDTH;

    // La función para posicionar ahora es más directa.
    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect)
        {
            comp.setBounds(guiArea.getX() + designRect.getX() * scale,
                guiArea.getY() + designRect.getY() * scale,
                designRect.getWidth() * scale,
                designRect.getHeight() * scale);
        };

    // --- 4. Posicionamos todas las secciones (Esto no cambia) ---
    scaleAndSet(masterSection, LayoutConstants::MASTER_SECTION);
    scaleAndSet(reverbSection, LayoutConstants::REVERB_SECTION);
    scaleAndSet(delaySection, LayoutConstants::DELAY_SECTION);
    scaleAndSet(soundPromptEditor, LayoutConstants::PROMPT_SECTION);

    auto promptBounds = soundPromptEditor.getBounds();
    const int buttonHeight = 40 * scale;
    const int padding = 10 * scale;

    const int generateButtonWidth = 100 * scale;
    const int undoRedoButtonWidth = 70 * scale;
    const int feedbackButtonWidth = 50 * scale;

    generateButton.setBounds(promptBounds.getRight() + padding, promptBounds.getCentreY() - (buttonHeight / 2), generateButtonWidth, buttonHeight);
    undoButton.setBounds(generateButton.getRight() + padding, generateButton.getY(), undoRedoButtonWidth, buttonHeight);
    redoButton.setBounds(undoButton.getRight() + padding, generateButton.getY(), undoRedoButtonWidth, buttonHeight);
    likeButton.setBounds(redoButton.getRight() + padding, generateButton.getY(), feedbackButtonWidth, buttonHeight);
    dislikeButton.setBounds(likeButton.getRight() + padding, generateButton.getY(), feedbackButtonWidth, buttonHeight);

    // --- Posicionar Selector de Tamaño (Esto no cambia) ---
    sizeLabel.setBounds(getWidth() - 160, 5, 50, 25);
    sizeComboBox.setBounds(getWidth() - 100, 5, 90, 25);

    // --- Posicionamos los componentes de presets ---
    auto sizeLabelBounds = sizeLabel.getBounds();
    const int presetControlHeight = 25;
    const int sectionGap = 30 * scale;

    //Aumentamos el ancho de cada control.
    const int refreshBtnWidth = 140 * scale;    
    const int presetSelectorWidth = 260 * scale; 
    const int presetLabelWidth = 900 * scale;     

    refreshPresetsButton.setBounds(sizeLabelBounds.getX() - refreshBtnWidth - sectionGap,
        sizeLabelBounds.getY(),
        refreshBtnWidth, presetControlHeight);
    presetSelector.setBounds(refreshPresetsButton.getX() - presetSelectorWidth - padding,
        sizeLabelBounds.getY(),
        presetSelectorWidth, presetControlHeight);
    presetLabel.setBounds(presetSelector.getX() - presetLabelWidth,
        sizeLabelBounds.getY(),
        presetLabelWidth, presetControlHeight);

    // --- 6. Posicionamos el resto de las secciones ---
    scaleAndSet(osc1, LayoutConstants::OSC_1_SECTION);
    scaleAndSet(osc2, LayoutConstants::OSC_2_SECTION);
    scaleAndSet(osc3, LayoutConstants::OSC_3_SECTION);
    scaleAndSet(unisonComp1, LayoutConstants::UNISON_1_SECTION);
    scaleAndSet(unisonComp2, LayoutConstants::UNISON_2_SECTION);
    scaleAndSet(unisonComp3, LayoutConstants::UNISON_3_SECTION);
    scaleAndSet(filterSection, LayoutConstants::FILTER_SECTION);
    scaleAndSet(modulationComp, LayoutConstants::LFO_FM_SECTION);
    scaleAndSet(envelopeSection, LayoutConstants::ENVELOPE_SECTION);

    // Actualizamos el factor de escala (Esto no cambia)
    this->scale = scale;
}

void SynthTabComponent::textEditorReturnKeyPressed(juce::TextEditor& editor)
{
    // Nos aseguramos de que el evento viene de nuestro editor de texto y no de otro
    if (&editor == &soundPromptEditor)
    {
        juce::String prompt = soundPromptEditor.getText();

        if (prompt.isNotEmpty())
        {
            DBG("Generando sonido con el prompt: " + prompt);

            // Llamamos a la funci del PythonManager que creamos
            py::dict patchData = audioProcessor.pythonManager->generateSynthSound(prompt);

            // Por ahora, solo mostraremos el resultado en la consola de depuraci.
            // En el siguiente paso, usaremos este diccionario para mover los knobs.
            if (patchData.contains("error"))
            {
                juce::String errorMessage = patchData["error"].cast<std::string>();
                DBG("!!! Error desde Python: " + errorMessage);
                // Opcional: Mostrar una alerta al usuario
                // juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Error", errorMessage);
            }
            else
            {
                DBG("Patch generado con 騙ito desde Python!");
                applyPatchFromPython(patchData);
                audioProcessor.applyPatchFromPython(patchData);

                addToHistory(patchData);
            }
        }
    }
}

void SynthTabComponent::applyPatchFromPython(const pybind11::dict& patchData)
{
    auto applyFloat = [&](const char* key, auto&& fn)
        {
            if (patchData.contains(key))
                fn(patchData[key].cast<float>());
        };

    auto applyBool = [&](const char* key, auto&& fn)
        {
            if (patchData.contains(key))
                fn(patchData[key].cast<bool>());
        };

    auto applyKnob = [&](CustomKnob& knob, const char* key)
        {
            applyFloat(key, [&](float value) { knob.setValue(value, juce::sendNotificationSync); });
        };

    // --- Seccin Master ---
    applyFloat("master_gain", [&](float value) { masterSection.setMasterGain(value); });
    applyFloat("master_glide", [&](float value) { masterSection.setGlide(value); });
    applyFloat("master_dark", [&](float value) { masterSection.setDark(value); });
    applyFloat("master_bright", [&](float value) { masterSection.setBright(value); });
    applyFloat("master_drive", [&](float value) { masterSection.setDrive(value); });
    applyBool("master_chorus_on", [&](bool enabled) { masterSection.setChorusEnabled(enabled); });

    // --- Envolvente ---
    applyFloat("attack", [&](float value) { envelopeSection.setAttackValue(value); });
    applyFloat("decay", [&](float value) { envelopeSection.setDecayValue(value); });
    applyFloat("sustain", [&](float value) { envelopeSection.setSustainValue(value); });
    applyFloat("release", [&](float value) { envelopeSection.setReleaseValue(value); });

    // --- Pitching, panormica y ganancia de osciladores ---
    applyFloat("osc1_octave", [&](float value) { osc1.octKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc1_pitch", [&](float value) { osc1.pitchKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc1_fine", [&](float value) { osc1.fineKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc1_pan", [&](float value) { osc1.panKnob.setValue(value, juce::sendNotificationSync); });

    applyFloat("osc2_octave", [&](float value) { osc2.octKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc2_pitch", [&](float value) { osc2.pitchKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc2_fine", [&](float value) { osc2.fineKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc2_pan", [&](float value) { osc2.panKnob.setValue(value, juce::sendNotificationSync); });

    applyFloat("osc3_octave", [&](float value) { osc3.octKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc3_pitch", [&](float value) { osc3.pitchKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc3_fine", [&](float value) { osc3.fineKnob.setValue(value, juce::sendNotificationSync); });
    applyFloat("osc3_pan", [&](float value) { osc3.panKnob.setValue(value, juce::sendNotificationSync); });

    applyKnob(osc1.gainKnob, "osc1_gain");
    applyKnob(osc2.gainKnob, "osc2_gain");
    applyKnob(osc3.gainKnob, "osc3_gain");

    if (patchData.contains("osc1_unison_voices"))
        unisonComp1.setVoices(patchData["osc1_unison_voices"].cast<int>());

    applyFloat("osc1_unison_detune", [&](float value) { unisonComp1.setDetune(value); });
    applyFloat("osc1_unison_balance", [&](float value) { unisonComp1.setBalance(value); });
    applyFloat("osc1_unison_spread", [&](float value) { osc1.spreadKnob.setValue(value, juce::sendNotificationSync); });

    if (patchData.contains("osc2_unison_voices"))
        unisonComp2.setVoices(patchData["osc2_unison_voices"].cast<int>());
    applyFloat("osc2_unison_detune", [&](float value) { unisonComp2.setDetune(value); });
    applyFloat("osc2_unison_balance", [&](float value) { unisonComp2.setBalance(value); });

    if (patchData.contains("osc3_unison_voices"))
        unisonComp3.setVoices(patchData["osc3_unison_voices"].cast<int>());
    applyFloat("osc3_unison_detune", [&](float value) { unisonComp3.setDetune(value); });
    applyFloat("osc3_unison_balance", [&](float value) { unisonComp3.setBalance(value); });

    // --- Filtro y modulacin ---
    applyFloat("filter_cutoff_hz", [&](float value) { filterSection.setCutoffValue(value); });
    applyFloat("filter_q", [&](float value) { filterSection.setResonanceValue(value); });
    applyFloat("filter_env_amt", [&](float value) { filterSection.setEnvAmountValue(value); });

    applyBool("filter_keytrack", [&](bool enabled) { filterSection.setKeyTrackEnabled(enabled); });

    applyFloat("fm_amount", [&](float value) { modulationComp.setFmAmountValue(value); });
    applyFloat("lfo_speed_hz", [&](float value) { modulationComp.setLfoSpeedValue(value); });
    applyFloat("lfo_amount", [&](float value) { modulationComp.setLfoAmountValue(value); });

    auto selectWave = [&](OscillatorComponent& osc, const char* key)
        {
            if (!patchData.contains(key))
                return;

            auto waveName = patchData[key].cast<std::string>();
            if (waveName.empty() || waveName == "None")
                return;

            if (!osc.oscSection.selectWaveByFilename(waveName.c_str()))
                DBG("No se encontr・el wavetable solicitado: " << waveName);
        };

    selectWave(osc1, "osc1_wavetable");
    selectWave(osc2, "osc2_wavetable");
    selectWave(osc3, "osc3_wavetable");

    // --- Reverb ---
    applyFloat("reverb_dry_level", [&](float value) { reverbSection.setDryLevel(value); });
    applyFloat("reverb_wet_level", [&](float value) { reverbSection.setWetLevel(value); });
    applyFloat("reverb_room_size", [&](float value) { reverbSection.setRoomSize(value); });
    applyFloat("reverb_pre_delay", [&](float value) { reverbSection.setPreDelay(value); });
    applyFloat("reverb_diffusion", [&](float value) { reverbSection.setDiffusion(value); });
    applyFloat("reverb_damping", [&](float value) { reverbSection.setDamping(value); });
    applyFloat("reverb_decay", [&](float value) { reverbSection.setDecay(value); });

    // --- Delay ---
    applyFloat("delay_dry_level", [&](float value) { delaySection.setDryLevel(value); });
    applyFloat("delay_wet_level", [&](float value) { delaySection.setCenterLevel(value); });
    applyFloat("delay_side_level", [&](float value) { delaySection.setSideLevel(value); });
    applyFloat("delay_hp_freq", [&](float value) { delaySection.setHighPass(value); });
    applyFloat("delay_lp_freq", [&](float value) { delaySection.setLowPass(value); });
    applyFloat("delay_time_left", [&](float value) { delaySection.setTimeLeft(value); });
    applyFloat("delay_time_center", [&](float value) { delaySection.setTimeCenter(value); });
    applyFloat("delay_time_right", [&](float value) { delaySection.setTimeRight(value); });
    applyFloat("delay_wow_depth", [&](float value) { delaySection.setWowDepth(value); });
    applyFloat("delay_feedback", [&](float value) { delaySection.setFeedback(value); });
}

// --- IMPLEMENTACIﾓN DE LAS NUEVAS FUNCIONES DE HISTORIAL ---

void SynthTabComponent::addToHistory(const pybind11::dict& newPatch)
{
    // Si hemos hecho "undo" y generamos un nuevo sonido,
    // borramos el historial "futuro" que ya no es v疝ido.
    if (currentHistoryIndex < (int)patchHistory.size() - 1)
    {
        patchHistory.erase(patchHistory.begin() + currentHistoryIndex + 1, patchHistory.end());
    }

    // Adimos el nuevo patch al final del vector
    patchHistory.push_back(newPatch);

    // Limitamos el historial a 50 pasos para no consumir memoria infinita
    const int maxHistorySize = 50;
    if (patchHistory.size() > maxHistorySize)
    {
        patchHistory.erase(patchHistory.begin()); // Borra el m疽 antiguo
    }

    // El puntero del historial ahora apunta al 伃timo elemento, el que acabamos de adir
    currentHistoryIndex = (int)patchHistory.size() - 1;

    // Finalmente, actualizamos el estado de los botones
    updateUndoRedoButtonStates();
}

void SynthTabComponent::undoButtonClicked()
{
    // Solo hacemos "undo" si no estamos ya en el primer elemento del historial
    if (currentHistoryIndex > 0)
    {
        currentHistoryIndex--;
        applyPatchFromPython(patchHistory[currentHistoryIndex]);
        // Tambi駭 aplicamos el patch al procesador de audio
        audioProcessor.applyPatchFromPython(patchHistory[currentHistoryIndex]);
        updateUndoRedoButtonStates();
    }
}

void SynthTabComponent::redoButtonClicked()
{
    // Solo hacemos "redo" si no estamos en el 伃timo elemento del historial
    if (currentHistoryIndex < (int)patchHistory.size() - 1)
    {
        currentHistoryIndex++;
        applyPatchFromPython(patchHistory[currentHistoryIndex]);
        // Tambi駭 aplicamos el patch al procesador de audio
        audioProcessor.applyPatchFromPython(patchHistory[currentHistoryIndex]);
        updateUndoRedoButtonStates();
    }
}

void SynthTabComponent::updateUndoRedoButtonStates()
{
    // Habilitar "Undo" si hay elementos anteriores en el historial
    undoButton.setEnabled(currentHistoryIndex > 0);

    // Habilitar "Redo" si hay elementos posteriores en el historial
    redoButton.setEnabled(currentHistoryIndex < (int)patchHistory.size() - 1);
}

void SynthTabComponent::populatePresets()
{
    currentPresets = audioProcessor.pythonManager->getLearnedSounds();
    presetSelector.clear();

    if (currentPresets.contains("error"))
    {
        DBG("No se pudieron cargar los presets desde Python.");
        return;
    }

    int id = 1;
    for (auto item : currentPresets)
    {
        juce::String presetName = item.first.cast<std::string>();
        presetSelector.addItem(presetName, id++);
    }

    presetSelector.setSelectedId(0, juce::dontSendNotification); // Limpiamos la selección
}