#include "PluginProcessor.h"
#include "PluginEditor.h"


NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p),

    // Inicializamos el componente de pestañas en la parte superior
    tabbedComponent(juce::TabbedButtonBar::Orientation::TabsAtTop),
    // Inicializamos nuestras pestañas, pasando el procesador a la del sinte
    synthTab(p),
    chordMelodyTab(p),
    keyboardComponent(p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    addAndMakeVisible(tabbedComponent);
    addAndMakeVisible(keyboardComponent);

    // Añadimos las pestañas con sus nombres
    tabbedComponent.addTab("Synthesizer", juce::Colours::black, &synthTab, false);
    tabbedComponent.addTab("Chord/Melody Generator", juce::Colours::black, &chordMelodyTab, false);

    // Tamaño inicial de la ventana del plugin
    const double designImageHeight = 1360.0;
    const double designKeyboardHeight = 120.0; // Altura del teclado de tu diseño
    const double designWidth = 2340.0;
    const double totalDesignHeight = designImageHeight + designKeyboardHeight;
    const double aspectRatio = designWidth / totalDesignHeight;

    // Establecemos un tamaño inicial que respete la proporción total
    setSize(1170, 1170 / aspectRatio);

    constrainer = std::make_unique<juce::ComponentBoundsConstrainer>();
    constrainer->setFixedAspectRatio(aspectRatio);
    setConstrainer(constrainer.get());

    setResizable(true, true);

    audioProcessor.keyboardState.addListener(this);
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
    audioProcessor.keyboardState.removeListener(this);
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    // El fondo ahora es gestionado por cada pestaña individualmente.
    // Simplemente rellenamos de negro para evitar artefactos visuales.
    g.fillAll(juce::Colours::black);
}


void NeuraSynthAudioProcessorEditor::resized()
{
    // Obtiene el área total del editor
    auto totalArea = getLocalBounds();

    // Define la altura del teclado. 
    // Lo calculamos dinámicamente basándonos en la proporción del diseño original.
    const double designImageHeight = 1360.0;
    const double designKeyboardHeight = 120.0;
    const double totalDesignHeight = designImageHeight + designKeyboardHeight;
    int keyboardHeight = static_cast<int>(getHeight() * (designKeyboardHeight / totalDesignHeight));

    // El área para el teclado es la franja inferior
    auto keyboardArea = totalArea.removeFromBottom(keyboardHeight);

    // El área restante en la parte superior es para las pestañas (synthTab y chordMelodyTab)
    auto mainArea = totalArea;

    // Asigna las áreas a los componentes
    tabbedComponent.setBounds(mainArea);
    keyboardComponent.setBounds(keyboardArea);
}

void NeuraSynthAudioProcessorEditor::handleNoteOn(juce::MidiKeyboardState*, int midiChannel, int midiNoteNumber, float velocity)
{
    auto message = juce::MidiMessage::noteOn(midiChannel, midiNoteNumber, velocity);
    audioProcessor.midiMessageCollector.addMessageToQueue(message);
}

void NeuraSynthAudioProcessorEditor::handleNoteOff(juce::MidiKeyboardState*, int midiChannel, int midiNoteNumber, float velocity)
{
    auto message = juce::MidiMessage::noteOff(midiChannel, midiNoteNumber, velocity);
    audioProcessor.midiMessageCollector.addMessageToQueue(message);
}