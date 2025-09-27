#include "PluginProcessor.h"
#include "PluginEditor.h"


NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p),

    // Inicializamos el componente de pestañas en la parte superior
    tabbedComponent(juce::TabbedButtonBar::Orientation::TabsAtTop),
    // Inicializamos nuestras pestañas, pasando el procesador a la del sinte
    synthTab(p),
    chordMelodyTab(p)
{
    addAndMakeVisible(tabbedComponent);

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
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    // El fondo ahora es gestionado por cada pestaña individualmente.
    // Simplemente rellenamos de negro para evitar artefactos visuales.
    g.fillAll(juce::Colours::black);
}


void NeuraSynthAudioProcessorEditor::resized()
{
    // Hacemos que el componente de pestañas ocupe toda la ventana del editor.
    tabbedComponent.setBounds(getLocalBounds());
}