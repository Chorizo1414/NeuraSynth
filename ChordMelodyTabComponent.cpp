#include <JuceHeader.h>
#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h" // <--- ¡AÑADE ESTA LÍNEA IMPORTANTE!

//==============================================================================
ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor & p)
    : audioProcessor(p)
{
    // --- Editor de Prompt ---
    addAndMakeVisible(promptEditor);
    promptEditor.setMultiLine(false);
    promptEditor.setReturnKeyStartsNewLine(false);
    promptEditor.setText("reggaeton en Eb major"); // Texto de ejemplo
    
    // --- Botón de Generar ---
    addAndMakeVisible(generateButton);
    generateButton.onClick = [this] { generateChords(); };
    
    // --- Etiqueta de Resultados ---
    addAndMakeVisible(resultsLabel);
    resultsLabel.setFont(juce::Font(16.0f));
    resultsLabel.setJustificationType(juce::Justification::centredTop);
    resultsLabel.setColour(juce::Label::textColourId, juce::Colours::white);
}

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

void ChordMelodyTabComponent::resized()
{
    // Posicionamos los controles en la pestaña
    auto bounds = getLocalBounds().reduced(20);
    promptEditor.setBounds(bounds.removeFromTop(30));
    bounds.removeFromTop(10); // Espacio
    generateButton.setBounds(bounds.removeFromTop(30));
    bounds.removeFromTop(10); // Espacio
    resultsLabel.setBounds(bounds);
}

void ChordMelodyTabComponent::generateChords()
{
    // 1. Obtenemos el texto del prompt
    juce::String prompt = promptEditor.getText();
    if (prompt.isEmpty())
    {
        resultsLabel.setText("Please enter a prompt.", juce::dontSendNotification);
        return;
    }
    
    // 2. Llamamos a la función de Python a través del manager
    resultsLabel.setText("Generating...", juce::dontSendNotification);
    juce::StringArray chords = audioProcessor.pythonManager.generateChordProgression(prompt);
    
    // 3. Mostramos los resultados
    if (chords.isEmpty())
    {
        resultsLabel.setText("Failed to generate chords.", juce::dontSendNotification);
    }
    else
    {
        resultsLabel.setText(chords.joinIntoString(" - "), juce::dontSendNotification);
    }
}