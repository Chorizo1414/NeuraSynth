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
    setSize(1200, 800);
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