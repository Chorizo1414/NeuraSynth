#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "BinaryData.h"

NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p),

    midiKeyboardComponent(audioProcessor.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard),
    // Filter
    filterCutoffKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 1.0),
    filterResonanceKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0), 
    filterEnvKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0f),

    // Envelope
    attackKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.01),
    decayKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.5),
    sustainKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.5),
    releaseKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.5),

    // LFO & FM
    modulationComp(p),

    // Reverb
    reverbSection(p),

    // Buttons
    keyButton("KeyButton"),
    masterSection(p),
    delaySection(p),
    designMouseListener(componentDragger)
{
    setWantsKeyboardFocus(true);
    backgroundImage = juce::ImageCache::getFromMemory(BinaryData::boceto_png, BinaryData::boceto_pngSize);

    // --- SECCIÓN OSCILADORES ---
    addAndMakeVisible(osc1);
    addAndMakeVisible(osc2);
    addAndMakeVisible(osc3);

    auto setupOscillatorKnobs = [](OscillatorComponent& osc)
        {
            // Spread: 0.0 (izquierda)
            osc.spreadKnob.setRange(0.0, 1.0);
            osc.spreadKnob.setValue(0.0);

            // Octave: 0 (centro) en un rango de -2 a 2
            osc.octKnob.setRange(-2.0, 2.0, 1.0);
            osc.octKnob.setValue(0.0);

            // Fine: 0 (centro) en un rango de -50 a 50 cents
            osc.fineKnob.setRange(-50.0, 50.0);
            osc.fineKnob.setValue(0.0);

            // Pitch: 0 (centro) en un rango de -12 a 12 semitonos
            osc.pitchKnob.setRange(-12.0, 12.0, 1.0);
            osc.pitchKnob.setValue(0.0);

            // Detune: 0 (centro) en un rango de -25 a 25 cents
            osc.detuneKnob.setRange(-100.0, 100.0); // Rango bipolar para que 0 sea el centro
            osc.detuneKnob.setValue(0.0);

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
    osc1.detuneKnob.onValueChange = [this]() { audioProcessor.setOsc1Detune(osc1.detuneKnob.getValue()); };
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
    osc2.detuneKnob.onValueChange = [this]() { audioProcessor.setOsc2Detune(osc2.detuneKnob.getValue()); };
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
    osc3.detuneKnob.onValueChange = [this]() { audioProcessor.setOsc3Detune(osc3.detuneKnob.getValue()); };
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

    // Agregar y configurar controles de master
    addAndMakeVisible(masterSection);

    // --- SECCIÓN FILTER ---
    addAndMakeVisible(filterCutoffKnob);
    filterCutoffKnob.setRange(20.0, 20000.0);
    // Mejor sensación: mapping log alrededor de 1 kHz
    filterCutoffKnob.setSkewFactorFromMidPoint(1000.0);

    addAndMakeVisible(filterResonanceKnob);
    filterResonanceKnob.setRange(0.1, 4.0); // Q

    addAndMakeVisible(filterEnvKnob);
    filterEnvKnob.setRange(-1.0, 1.0);

    // Callbacks → DSP
    filterCutoffKnob.onValueChange = [this] { audioProcessor.setFilterCutoff(filterCutoffKnob.getValue()); };
    filterResonanceKnob.onValueChange = [this] { audioProcessor.setFilterResonance(filterResonanceKnob.getValue()); };
    filterEnvKnob.onValueChange = [this] { audioProcessor.setFilterEnvAmount(filterEnvKnob.getValue()); };

    // --- AÑADE ESTAS LÍNEAS PARA FIJAR EL ESTADO INICIAL ---
    filterCutoffKnob.setValue(20000.0, juce::sendNotificationSync);
    filterResonanceKnob.setValue(0.1, juce::sendNotificationSync);
    filterEnvKnob.setValue(-1.0, juce::sendNotificationSync);

    addAndMakeVisible(keyButton);
    keyButton.setClickingTogglesState(true);
    keyButton.onClick = [this] { audioProcessor.setKeyTrack(keyButton.getToggleState()); };


    // --- SECCIÓN ENVELOPE ---
    addAndMakeVisible(envelopeDisplay);
    addAndMakeVisible(attackKnob);
    attackKnob.setRange(0.0, 5.0); // Rango en segundos
    addAndMakeVisible(decayKnob);
    decayKnob.setRange(0.0, 5.0);
    addAndMakeVisible(sustainKnob);
    sustainKnob.setRange(0.0, 1.0);
    addAndMakeVisible(releaseKnob);
    releaseKnob.setRange(0.0, 5.0);

    // Conectar knobs de la envolvente al display
    auto updateEnvelopeDisplay = [this]() {
        envelopeDisplay.setADSR(attackKnob.getValue(), decayKnob.getValue(), sustainKnob.getValue(), releaseKnob.getValue());

        // --- AÑADE ESTAS LÍNEAS PARA ENVIAR LOS VALORES AL MOTOR DE AUDIO ---
        audioProcessor.setAttack(attackKnob.getValue());
        audioProcessor.setDecay(decayKnob.getValue());
        audioProcessor.setSustain(sustainKnob.getValue());
        audioProcessor.setRelease(releaseKnob.getValue());

    };
    attackKnob.onValueChange = updateEnvelopeDisplay;
    decayKnob.onValueChange = updateEnvelopeDisplay;
    sustainKnob.onValueChange = updateEnvelopeDisplay;
    releaseKnob.onValueChange = updateEnvelopeDisplay;
    updateEnvelopeDisplay(); // Llamada inicial para dibujar el estado por defecto

    // --- SECCIÓN MODULACIÓN (LFO & FM) ---
    addAndMakeVisible(modulationComp);

	// --- SECCIÓN REVERB ---
    addAndMakeVisible(reverbSection);

    // --- SECCIÓN DELAY ---
    addAndMakeVisible(delaySection);

    addAndMakeVisible(keyButton);
    keyButton.setClickingTogglesState(true);

    auto normalKeyImage = juce::ImageCache::getFromMemory(BinaryData::button_png, BinaryData::button_pngSize);
    auto toggledKeyImage = juce::ImageCache::getFromMemory(BinaryData::buttonreverse_png, BinaryData::buttonreverse_pngSize);

    // Inicialmente, pon la imagen normal
    keyButton.setImages(
        false, true, true,
        normalKeyImage, 1.0f, juce::Colours::transparentBlack,
        normalKeyImage, 1.0f, juce::Colours::transparentBlack,
        normalKeyImage, 1.0f, juce::Colours::transparentBlack
    );

    keyButton.onClick = [this, normalKeyImage, toggledKeyImage] {
        audioProcessor.setKeyTrack(keyButton.getToggleState());
        if (keyButton.getToggleState())
        {
            keyButton.setImages(
                false, true, true,
                toggledKeyImage, 1.0f, juce::Colours::transparentBlack,
                toggledKeyImage, 1.0f, juce::Colours::transparentBlack,
                toggledKeyImage, 1.0f, juce::Colours::transparentBlack
            );
        }
        else
        {
            keyButton.setImages(
                false, true, true,
                normalKeyImage, 1.0f, juce::Colours::transparentBlack,
                normalKeyImage, 1.0f, juce::Colours::transparentBlack,
                normalKeyImage, 1.0f, juce::Colours::transparentBlack
            );
        }
        };

    keyButton.setName("KeyButton");

    addAndMakeVisible(midiKeyboardComponent);

    if (designMode)
    {
        masterSection.addMouseListener(&designMouseListener, true);

        osc1.addMouseListener(&designMouseListener, true);
        osc2.addMouseListener(&designMouseListener, true);
        osc3.addMouseListener(&designMouseListener, true);

        filterCutoffKnob.addMouseListener(&designMouseListener, true);
        filterResonanceKnob.addMouseListener(&designMouseListener, true);
        filterEnvKnob.addMouseListener(&designMouseListener, true);
        keyButton.addMouseListener(&designMouseListener, true);

		envelopeDisplay.addMouseListener(&designMouseListener, true);
        attackKnob.addMouseListener(&designMouseListener, true);
        decayKnob.addMouseListener(&designMouseListener, true);
        sustainKnob.addMouseListener(&designMouseListener, true);
        releaseKnob.addMouseListener(&designMouseListener, true);

        modulationComp.addMouseListener(&designMouseListener, true);

        reverbSection.addMouseListener(&designMouseListener, true);

        delaySection.addMouseListener(&designMouseListener, true);

    }

    setSize(1024, 680);
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    if (backgroundImage.isValid())
    {
        const int interfaceHeight = 600;
        auto backgroundArea = getLocalBounds().withHeight(interfaceHeight);
        g.drawImage(backgroundImage, backgroundArea.toFloat(), juce::RectanglePlacement::fillDestination);
    }
    else
    {
        g.fillAll(getLookAndFeel().findColour(juce::ResizableWindow::backgroundColourId));
    }
}


void NeuraSynthAudioProcessorEditor::resized()
{
    const int oscComponentWidth = 430;
    const int oscComponentHeight = 220;

    osc1.setBounds(403, 8, oscComponentWidth, oscComponentHeight);
    osc2.setBounds(403, 199, oscComponentWidth, oscComponentHeight);
    osc3.setBounds(404, 404, oscComponentWidth, oscComponentHeight);

    // --- Copiamos todas tus posiciones originales para el resto de los componentes ---
    // Sección Master
    masterSection.setBounds(33, 58, 230, 140);

    // Sección Filter
    filterCutoffKnob.setBounds(760, 68, 100, 100);
    filterResonanceKnob.setBounds(838, 68, 100, 100);
    filterEnvKnob.setBounds(926, 68, 100, 100);
    keyButton.setBounds(872, 166, 35, 35);

    // Sección Envelope
    envelopeDisplay.setBounds(787, 240, 210, 95);
    attackKnob.setBounds(770, 311, 100, 100);
    decayKnob.setBounds(817, 311, 100, 100);
    sustainKnob.setBounds(863, 311, 100, 100);
    releaseKnob.setBounds(912, 311, 100, 100);

    // Sección LFO & FM
    modulationComp.setBounds(734, 439, 288, 105);

	// Sección Reverb
    reverbSection.setBounds(-14, 242, 300, 160);

    // Sección Delay
    delaySection.setBounds(0, 419, 300, 165);

    // Teclado
    midiKeyboardComponent.setBounds(0, 600, getWidth(), 80);

}

void NeuraSynthAudioProcessorEditor::visibilityChanged()
{
    if (isShowing())
    {
        grabKeyboardFocus();
    }
}
