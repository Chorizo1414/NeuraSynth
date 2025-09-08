#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "BinaryData.h"
#include "LayoutConstants.h"

NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p),

    midiKeyboardComponent(audioProcessor.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard),

    // LFO & FM
    modulationComp(p),

    // Reverb
    reverbSection(p),

    // Buttons
    masterSection(p),
    delaySection(p),
    filterSection(p),
    envelopeSection(p),
    designMouseListener(componentDragger, this)

{
    setWantsKeyboardFocus(true);
    backgroundImage = juce::ImageCache::getFromMemory(BinaryData::boceto_png, BinaryData::boceto_pngSize);

    // Asignamos nombres para el modo diseño
    osc1.setName("Oscillator 1");
    osc2.setName("Oscillator 2");
    osc3.setName("Oscillator 3");
    unisonComp1.setName("Unison 1");
    unisonComp2.setName("Unison 2");
    unisonComp3.setName("Unison 3");
    masterSection.setName("Master Section");
    reverbSection.setName("Reverb Section");
    delaySection.setName("Delay Section");
    modulationComp.setName("Modulation Section");

    // --- SECCIÓN OSCILADORES ---
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

    // Conexión de Callbacks para el Oscilador 1 (el que está activo)
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

    // Conexión de displays para OSC2 y OSC3 (solo visual, sin afectar audio)
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

    // --- Conexión de Callbacks para el Oscilador 3 ---
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

    // Carga de wavetables en cada sección
    juce::String waveFolderPath = "C:/Users/Progra.CHORI1414/Desktop/Proyectos/JUCE/NeuraSynth/Source/wavetables";
    osc1.oscSection.loadWavetablesFromFolder(waveFolderPath);
    osc2.oscSection.loadWavetablesFromFolder(waveFolderPath);
    osc3.oscSection.loadWavetablesFromFolder(waveFolderPath);

    // --- SECCIÓN UNISON ---
    addAndMakeVisible(unisonComp1);
    addAndMakeVisible(unisonComp2);
    addAndMakeVisible(unisonComp3);
    
    // Conexión de Callbacks para el Unison del Oscilador 1
    unisonComp1.onVoicesChanged = [this](int voices) { audioProcessor.setOsc1UnisonVoices(voices); };
    unisonComp1.onDetuneChanged = [this](float detune) { audioProcessor.setOsc1UnisonDetune(detune); };
    unisonComp1.onBalanceChanged = [this](float balance) { audioProcessor.setOsc1UnisonBalance(balance); };
    // (Los callbacks para unison 2 y 3 se añadirán cuando el procesador los soporte)

    // Agregar y configurar controles de master
    addAndMakeVisible(masterSection);

    // --- SECCIÓN FILTER ---
    addAndMakeVisible(filterSection);

    // --- SECCIÓN ENVELOPE ---
    addAndMakeVisible(envelopeSection);

    // --- SECCIÓN MODULACIÓN (LFO & FM) ---
    addAndMakeVisible(modulationComp);

	// --- SECCIÓN REVERB ---
    addAndMakeVisible(reverbSection);

    // --- SECCIÓN DELAY ---
    addAndMakeVisible(delaySection);

    addAndMakeVisible(midiKeyboardComponent);

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

    // -- - Selector de Tamaño-- -
    addAndMakeVisible(sizeLabel);
    sizeLabel.setText("Size:", juce::dontSendNotification);
    sizeLabel.setJustificationType(juce::Justification::centredRight);

    addAndMakeVisible(sizeComboBox);
    sizeComboBox.addItem("50%", 1);
    sizeComboBox.addItem("75%", 2);
    sizeComboBox.addItem("100%", 3);
    sizeComboBox.setSelectedId(2); // Empezamos al 75%

    sizeComboBox.onChange = [this]
    {
        float finalScale = 0.5f; // El 100% será la mitad del tamaño del diseño
        int choice = sizeComboBox.getSelectedId();
        if (choice == 1) finalScale = 0.25f;  // El 50% será un cuarto del diseño
        if (choice == 2) finalScale = 0.375f; // El 75% será 3/8 del diseño
        if (choice == 3) finalScale = 0.5f;   // El 100% será la mitad del diseño
        
        // Usamos la función correcta para obtener la ventana principal del plugin
        if (auto* parent = findParentComponentOfClass<juce::TopLevelWindow>())
        {
            const int newWidth = LayoutConstants::DESIGN_WIDTH * finalScale;
            const int newHeight = LayoutConstants::DESIGN_HEIGHT * finalScale;
            parent->setSize(newWidth, newHeight);
        }
    };
  
    // Tamaño inicial
    const float initialScale = 0.75f;
    const int initialWidth = LayoutConstants::DESIGN_WIDTH * initialScale;
    const int initialHeight = LayoutConstants::DESIGN_HEIGHT * initialScale;
    setSize(initialWidth, initialHeight);
    setResizable(true, true); // Permite que el ComboBox funcione
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    // 1. Rellena todo el fondo de negro. Este será el color base para la sección del piano.
    g.fillAll(juce::Colours::black);

    // 2. Calcula la altura actual del teclado para saber dónde termina la sección de la GUI.
    //    Esta lógica es idéntica a la de `resized()` para que siempre estén sincronizadas.
    const float widthScale = (float)getWidth() / LayoutConstants::DESIGN_WIDTH;
    int keyboardHeight = LayoutConstants::KEYBOARD_HEIGHT * widthScale;
    if (keyboardHeight < 0) keyboardHeight = 0;
    juce::Rectangle<int> guiArea = getLocalBounds().withTrimmedBottom(keyboardHeight);

    // 3. Dibuja la imagen de fondo SOLAMENTE en el área superior (guiArea).
    if (backgroundImage.isValid())
    {
        g.drawImage(backgroundImage, guiArea.toFloat(), juce::RectanglePlacement::stretchToFit);
    }
}


void NeuraSynthAudioProcessorEditor::resized()
{
    // --- 1. Define el área para el teclado (Esto no cambia) ---
    const float widthScale = (float)getWidth() / LayoutConstants::DESIGN_WIDTH;
    int keyboardHeight = LayoutConstants::KEYBOARD_HEIGHT * widthScale;
    if (keyboardHeight < 0) keyboardHeight = 0;
    midiKeyboardComponent.setBounds(0, getHeight() - keyboardHeight, getWidth(), keyboardHeight);

    // --- 2. Define el área para la GUI (Esto no cambia) ---
    juce::Rectangle<int> guiArea = getLocalBounds().withTrimmedBottom(keyboardHeight);

    // --- 3. LÓGICA DE ESCALADO SIMPLIFICADA ---
    // Como tu ComboBox asegura que la proporción es siempre correcta, no necesitamos
    // el cálculo complejo de antes. El área de la GUI ya es perfecta.
    const float scale = (float)guiArea.getWidth() / LayoutConstants::DESIGN_WIDTH;

    // La función para posicionar ahora es más directa.
    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect)
        {
            // Posiciona los componentes relativo al inicio del guiArea (que es 0,0).
            comp.setBounds(guiArea.getX() + designRect.getX() * scale,
                guiArea.getY() + designRect.getY() * scale,
                designRect.getWidth() * scale,
                designRect.getHeight() * scale);
        };

    // --- 4. Posicionamos todas las secciones (Esto no cambia) ---
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

    // --- Posicionar Selector de Tamaño (Esto no cambia) ---
    sizeLabel.setBounds(getWidth() - 160, 5, 50, 25);
    sizeComboBox.setBounds(getWidth() - 100, 5, 90, 25);

    // Actualizamos el factor de escala (Esto no cambia)
    this->scale = scale;
}

void NeuraSynthAudioProcessorEditor::visibilityChanged()
{
    if (isShowing())
    {
        grabKeyboardFocus();
    }
}