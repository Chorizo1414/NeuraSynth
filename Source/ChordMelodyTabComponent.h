#pragma once
#include <JuceHeader.h>
#include "PythonManager.h"
#include "PianoRollComponent.h" // <-- Incluir nuestro nuevo componente

class ChordMelodyTabComponent : public juce::Component
{
public:
    ChordMelodyTabComponent(PythonManager& pm);
    ~ChordMelodyTabComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

private:
    PythonManager& pythonManager;

    juce::TextEditor promptEditor;
    PianoRollComponent pianoRollComponent; // <-- Añadir el piano roll

    // Usaremos ImageButton para los iconos
    juce::ImageButton generateButton;
    juce::ImageButton playButton;
    juce::ImageButton stopButton;
    juce::ImageButton likeButton;
    juce::ImageButton dislikeButton;
    juce::ImageButton exportButton;

    // Función para cargar las imágenes de los botones
    void loadButtonImages();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};