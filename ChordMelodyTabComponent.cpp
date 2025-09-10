#include <JuceHeader.h>
#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h" // <--- ¡AÑADE ESTA LÍNEA IMPORTANTE!

//==============================================================================
// ++ MODIFICA EL CONSTRUCTOR COMPLETAMENTE ++
ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& p)
    : audioProcessor(p), generateButton("Generar")
{
    addAndMakeVisible(promptEditor);
    promptEditor.setMultiLine(true);
    promptEditor.setReturnKeyStartsNewLine(true);
    promptEditor.setText("reggaeton en Eb major"); // Texto de ejemplo

    addAndMakeVisible(generateButton);

    generateButton.onClick = [this]
        {
            audioProcessor.startGeneration(promptEditor.getText());
        };
}

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

// ++ MODIFICA LA FUNCIÓN RESIZED COMPLETAMENTE ++
void ChordMelodyTabComponent::resized()
{
    auto bounds = getLocalBounds().reduced(20); // Un poco de margen

    auto topArea = bounds.removeFromTop(100);

    generateButton.setBounds(topArea.removeFromRight(120).withTrimmedRight(10));
    promptEditor.setBounds(topArea);
}