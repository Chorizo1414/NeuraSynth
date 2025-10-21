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
    designMouseListener(componentDragger, this),
    keyboardComponent(p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    addAndMakeVisible(keyboardComponent);
    setWantsKeyboardFocus(true);
    backgroundImage = juce::ImageCache::getFromMemory(BinaryData::boceto_png, BinaryData::boceto_pngSize);

    // Asignamos nombres para el modo diseño y fijamos el layout específico de cada oscilador
    osc1.setName("Oscillator 1");
    osc2.setName("Oscillator 2");
    osc3.setName("Oscillator 3");
    osc1.setLayoutVariant(1);
    osc2.setLayoutVariant(2);
    osc3.setLayoutVariant(3);
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

    // Conexion de Callbacks para el Oscilador 1 (el que est  activo)
    osc1.oscSection.onWaveLoaded = [this](const juce::AudioBuffer<float>& buffer) {
        audioProcessor.setWavetable1(buffer); 
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
        audioProcessor.setWavePosition1(newPosition); 
        osc1.waveDisplay.setDisplayPosition(newPosition);
        };

    // Conexion de displays para OSC2 y OSC3 (solo visual, sin afectar audio)
    osc2.oscSection.onWaveLoaded = [this](const juce::AudioBuffer<float>& buffer) {
        audioProcessor.setWavetable2(buffer);
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
        audioProcessor.setWavePosition2(newPosition); 
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
    const auto accentColour = juce::Colour::fromRGB(255, 163, 72);
    const auto controlBackground = juce::Colour::fromRGB(58, 68, 83);
    const auto inputBackground = juce::Colour::fromRGB(32, 39, 52);
    const auto successColour = juce::Colour::fromRGB(124, 205, 150);
    const auto dangerColour = juce::Colour::fromRGB(223, 126, 118);
    const auto outlineColour = juce::Colour::fromRGB(73, 85, 103);
    const auto mutedTextColour = juce::Colour::fromRGB(214, 223, 237);

    soundPromptEditor.setMultiLine(false);
    soundPromptEditor.setReturnKeyStartsNewLine(false);
    soundPromptEditor.setReadOnly(false);
    soundPromptEditor.setScrollbarsShown(false);
    soundPromptEditor.setCaretVisible(true);
    soundPromptEditor.setPopupMenuEnabled(true);
    soundPromptEditor.setTextToShowWhenEmpty("Escribe un sonido (ej: 'Warm Lead', 'Bright Pad')...", mutedTextColour.withAlpha(0.6f));
    soundPromptEditor.setFont(juce::Font(17.0f));
    soundPromptEditor.setBorder({});
    soundPromptEditor.setColour(juce::TextEditor::backgroundColourId, inputBackground);
    soundPromptEditor.setColour(juce::TextEditor::outlineColourId, outlineColour);
    soundPromptEditor.setColour(juce::TextEditor::focusedOutlineColourId, accentColour);
    soundPromptEditor.setColour(juce::TextEditor::textColourId, mutedTextColour);
    soundPromptEditor.setColour(juce::TextEditor::highlightColourId, accentColour.withAlpha(0.35f));

    addAndMakeVisible(soundPromptLabel);
    soundPromptLabel.setText("Generador de Sonido:", juce::dontSendNotification);
    soundPromptLabel.setColour(juce::Label::textColourId, mutedTextColour.withAlpha(0.9f));
    soundPromptLabel.setFont(juce::Font(15.0f, juce::Font::bold));
    soundPromptLabel.attachToComponent(&soundPromptEditor, true);

    auto styleUtilityButton = [controlBackground, mutedTextColour](juce::TextButton& button, juce::Colour background)
        {
            button.setColour(juce::TextButton::buttonColourId, background);
            button.setColour(juce::TextButton::buttonOnColourId, background.brighter(0.25f));
            button.setColour(juce::TextButton::textColourOffId, mutedTextColour);
            button.setColour(juce::TextButton::textColourOnId, mutedTextColour);
            button.setWantsKeyboardFocus(false);
            button.setMouseClickGrabsKeyboardFocus(false);
            button.setTriggeredOnMouseDown(true);
        };

    // --- Inicialización de los nuevos botones de historial ---
    generateButton.setButtonText("Generar");
    addAndMakeVisible(generateButton);
    // Asignamos la misma funcion que presionar Enter en el editor de texto
    generateButton.onClick = [this] { textEditorReturnKeyPressed(soundPromptEditor); };

    generateButton.setTooltip("Generar un nuevo preset a partir del prompt actual");
    const auto generateButtonColour = juce::Colour::fromRGB(80, 101, 135); // Un azul sutil
    generateButton.setColour(juce::TextButton::buttonColourId, generateButtonColour);
    generateButton.setColour(juce::TextButton::buttonOnColourId, generateButtonColour.brighter(0.2f));
    generateButton.setColour(juce::TextButton::textColourOffId, mutedTextColour.brighter(0.5f));
    generateButton.setColour(juce::TextButton::textColourOnId, juce::Colours::white);
    generateButton.setWantsKeyboardFocus(false);
    generateButton.setMouseClickGrabsKeyboardFocus(false);
    generateButton.setTriggeredOnMouseDown(true);

    undoButton.setButtonText(juce::CharPointer_UTF8("\xe2\x9f\xb2"));
    addAndMakeVisible(undoButton);
    undoButton.onClick = [this] { undoButtonClicked(); };
    undoButton.setTooltip("Deshacer el último preset aplicado");
    styleUtilityButton(undoButton, controlBackground);

    redoButton.setButtonText(juce::CharPointer_UTF8("\xe2\x9f\xb3"));
    addAndMakeVisible(redoButton);
    redoButton.onClick = [this] { redoButtonClicked(); };
    redoButton.setTooltip("Rehacer el último preset aplicado");
    styleUtilityButton(redoButton, controlBackground);

    // Establecemos el estado inicial de los botones (deshabilitados)
    updateUndoRedoButtonStates();

    // --- Inicialización de los botones de feedback ---
    likeButton.setButtonText(juce::CharPointer_UTF8("\xf0\x9f\x91\x8d"));
    addAndMakeVisible(likeButton);
    likeButton.setTooltip("Guardar el preset actual en favoritos");
    likeButton.onClick = [this]
        {
        // Llamamos a la función y guardamos el resultado
        bool success = audioProcessor.pythonManager->likeLastSound();

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
    likeButton.setColour(juce::TextButton::buttonColourId, controlBackground.brighter(0.2f));
    likeButton.setColour(juce::TextButton::buttonOnColourId, controlBackground.brighter(0.3f));
    likeButton.setColour(juce::TextButton::textColourOffId, successColour); // El icono se pone verde
    likeButton.setColour(juce::TextButton::textColourOnId, successColour.brighter(0.5f));
    likeButton.setWantsKeyboardFocus(false);
    likeButton.setMouseClickGrabsKeyboardFocus(false);
    likeButton.setTriggeredOnMouseDown(true);

    dislikeButton.setButtonText(juce::CharPointer_UTF8("\xf0\x9f\x91\x8e"));
    addAndMakeVisible(dislikeButton);
    dislikeButton.setTooltip("Descartar y generar un nuevo preset al instante");
    dislikeButton.onClick = [this]
        {
            // La acción de "dislike" simplemente genera un nuevo sonido
            textEditorReturnKeyPressed(soundPromptEditor);
        };

    dislikeButton.setColour(juce::TextButton::buttonColourId, controlBackground.brighter(0.2f));
    dislikeButton.setColour(juce::TextButton::buttonOnColourId, controlBackground.brighter(0.3f));
    dislikeButton.setColour(juce::TextButton::textColourOffId, dangerColour); // El icono se pone rojo
    dislikeButton.setColour(juce::TextButton::textColourOnId, dangerColour.brighter(0.5f));
    dislikeButton.setWantsKeyboardFocus(false);
    dislikeButton.setMouseClickGrabsKeyboardFocus(false);
    dislikeButton.setTriggeredOnMouseDown(true);

    // --- Inicialización de los componentes de presets ---
    addAndMakeVisible(presetLabel);
    presetLabel.setText("Presets:", juce::dontSendNotification);
    presetLabel.setJustificationType(juce::Justification::centredRight);
    presetLabel.setColour(juce::Label::textColourId, mutedTextColour.withAlpha(0.85f));

    addAndMakeVisible(presetSelector);
    presetSelector.setTextWhenNoChoicesAvailable("No hay presets guardados");
    presetSelector.setJustificationType(juce::Justification::centred);
    presetSelector.setTooltip("Selecciona un preset generado anteriormente");
    presetSelector.setColour(juce::ComboBox::backgroundColourId, inputBackground);
    presetSelector.setColour(juce::ComboBox::outlineColourId, outlineColour);
    presetSelector.setColour(juce::ComboBox::textColourId, mutedTextColour);
    presetSelector.setColour(juce::ComboBox::arrowColourId, mutedTextColour);
    presetSelector.onChange = [this]
        {
        int selectedId = presetSelector.getSelectedId();
        if (selectedId > 0)
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
    refreshPresetsButton.setTooltip("Actualizar la lista de presets guardados");
    refreshPresetsButton.onClick = [this] { populatePresets(); };

    populatePresets();

    // --- Botón de ayuda para tipos de sonido ---
    addAndMakeVisible(soundTypesHelpButton);
    soundTypesHelpButton.setButtonText("?");
    soundTypesHelpButton.setTooltip("Muestra una lista de los tipos de sonido que puedes generar (ej: pad, lead, bass...)");

    soundTypesHelpButton.onClick = [this]
        {
            // 1. Obtenemos la lista de sonidos desde Python
            juce::StringArray soundTypes = audioProcessor.pythonManager->getSoundArchetypes();

            if (soundTypes.isEmpty())
            {
                juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon,
                    "Sin información",
                    "No se pudo obtener la lista de tipos de sonido.");
                return;
            }

            // 2. Creamos el menú popup
            juce::PopupMenu menu;
            for (int i = 0; i < soundTypes.size(); ++i)
            {
                // Añadimos cada tipo de sonido como un item (no seleccionable)
                menu.addItem(i + 1, soundTypes[i]);
            }

            // 3. Mostramos el menú al lado del botón
            menu.showMenuAsync(juce::PopupMenu::Options().withTargetComponent(&soundTypesHelpButton));
        };

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

}

SynthTabComponent::~SynthTabComponent()
{
}

void SynthTabComponent::paint(juce::Graphics& g)
{
    // 1. Rellenamos todo el fondo de negro. Esto creará la barra negra inferior.
    g.fillAll(juce::Colours::black);

    if (backgroundImage.isValid())
    {
        // 2. Dibujamos la imagen de fondo SOLAMENTE en el 'guiArea',
        //    que ahora tendrá la proporción correcta y no estará deformada.
        g.drawImage(backgroundImage, guiArea.toFloat(), juce::RectanglePlacement::stretchToFit);
    }
}

void SynthTabComponent::resized()
{
    auto totalBounds = getLocalBounds();
    const float widthScale = (float)getWidth() / LayoutConstants::DESIGN_WIDTH;
    int keyboardHeight = juce::roundToInt(LayoutConstants::KEYBOARD_HEIGHT * widthScale);
    if (keyboardHeight < 0) keyboardHeight = 0;
    keyboardComponent.setBounds(totalBounds.removeFromBottom(keyboardHeight));
    guiArea = totalBounds;
    const float scale = (float)guiArea.getWidth() / LayoutConstants::DESIGN_WIDTH;
    const float referenceScale = 0.5f;
    const float minScale = 0.375f;
    offsetFactor = 0.0f;
    if (scale < referenceScale)
    {
        auto normalised = (referenceScale - scale) / (referenceScale - minScale);
        normalised = juce::jlimit(0.0f, 1.0f, normalised);
        offsetFactor = juce::jmap(normalised, 0.0f, 1.0f, 0.0f, -5.0f);
    }
    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<float>& designRect)
        {
            const float scaledX = guiArea.getX() + designRect.getX() * scale;
            const float scaledY = guiArea.getY() + designRect.getY() * scale + offsetFactor;
            const float scaledWidth = designRect.getWidth() * scale;
            const float scaledHeight = designRect.getHeight() * scale;
            comp.setBounds(juce::roundToInt(scaledX), juce::roundToInt(scaledY), juce::roundToInt(scaledWidth), juce::roundToInt(scaledHeight));
        };

    // --- 1. Posicionamos la barra superior (sin el botón de ayuda) ---
    const auto promptDesign = LayoutConstants::PROMPT_SECTION;
    const int promptY = juce::roundToInt(guiArea.getY() + promptDesign.getY() * scale + offsetFactor);
    const int promptLeft = juce::roundToInt(guiArea.getX() + promptDesign.getX() * scale);
    const int rightMargin = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 12.0f, 18.0f));
    const int availableWidth = juce::jmax(0, guiArea.getRight() - promptLeft - rightMargin);
    const int rowHeight = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 20.0f, 26.0f));
    juce::Rectangle<int> topRowBounds(promptLeft, promptY, availableWidth, rowHeight);

    juce::FlexBox topRow;
    topRow.flexDirection = juce::FlexBox::Direction::row;
    topRow.alignItems = juce::FlexBox::AlignItems::center;

    const float spacing = juce::jmap(scale, minScale, referenceScale, 4.0f, 6.0f);
    const int generateWidth = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 60.0f, 80.0f));
    const int feedbackUtilityButtonWidth = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 28.0f, 38.0f));
    const int presetLabelMinWidth = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 50.0f, 65.0f));
    const int presetSelectorWidth = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 80.0f, 110.0f));
    const int refreshWidth = juce::roundToInt(juce::jmap(scale, minScale, referenceScale, 50.0f, 70.0f));

    topRow.items.add(juce::FlexItem(soundPromptEditor).withFlex(1.0f).withHeight(rowHeight));
    topRow.items.add(juce::FlexItem(generateButton).withWidth(generateWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, spacing * 1.5f }));
    topRow.items.add(juce::FlexItem(likeButton).withWidth(feedbackUtilityButtonWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, 0.0f }));
    topRow.items.add(juce::FlexItem(dislikeButton).withWidth(feedbackUtilityButtonWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, 0.0f }));
    topRow.items.add(juce::FlexItem(undoButton).withWidth(feedbackUtilityButtonWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, 0.0f }));
    topRow.items.add(juce::FlexItem(redoButton).withWidth(feedbackUtilityButtonWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, spacing * 2.0f }));
    topRow.items.add(juce::FlexItem().withFlex(0.1f));
    topRow.items.add(juce::FlexItem(presetLabel).withMinWidth(presetLabelMinWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, 0.0f }));
    topRow.items.add(juce::FlexItem(presetSelector).withWidth(presetSelectorWidth).withHeight(rowHeight));
    topRow.items.add(juce::FlexItem(refreshPresetsButton).withWidth(refreshWidth).withHeight(rowHeight).withMargin({ 0.0f, spacing, 0.0f, spacing }));

    topRow.performLayout(topRowBounds);

    // --- 2. Posicionamos todas las secciones principales ---
    scaleAndSet(masterSection, LayoutConstants::MASTER_SECTION);
    scaleAndSet(reverbSection, LayoutConstants::REVERB_SECTION);
    scaleAndSet(delaySection, LayoutConstants::DELAY_SECTION);
    scaleAndSet(osc1, LayoutConstants::OSC_1_SECTION);
    scaleAndSet(osc2, LayoutConstants::OSC_2_SECTION);
    scaleAndSet(osc3, LayoutConstants::OSC_3_SECTION);
    scaleAndSet(unisonComp1, LayoutConstants::UNISON_1_SECTION);
    scaleAndSet(unisonComp2, LayoutConstants::UNISON_2_SECTION);
    scaleAndSet(unisonComp3, LayoutConstants::UNISON_3_SECTION);
    scaleAndSet(filterSection, LayoutConstants::FILTER_SECTION);
    scaleAndSet(modulationComp, LayoutConstants::LFO_FM_SECTION);
    scaleAndSet(envelopeSection, LayoutConstants::ENVELOPE_SECTION);

    const int helpButtonWidth = juce::roundToInt(rowHeight * 0.85f);

    const int buttonY = topRowBounds.getBottom() + (int)spacing * 2;

    const int buttonX = masterSection.getX() - helpButtonWidth - (int)spacing;

    soundTypesHelpButton.setBounds(buttonX, buttonY, helpButtonWidth, helpButtonWidth);

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