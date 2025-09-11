#pragma once

#include <JuceHeader.h>
#include "PythonManager.h"
#include "PianoRollComponent.h" // Incluimos nuestro nuevo componente

class NeuraSynthAudioProcessor;

class ChordMelodyTabComponent : public juce::Component
{
public:
    ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor);
    ~ChordMelodyTabComponent() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    // --- Componentes UI ---
    juce::TextEditor promptEditor;
    juce::Label promptLabel;

    juce::ComboBox genreComboBox;
    juce::Label genreLabel;

    juce::TextButton generateChordsButton;
    juce::TextButton generateMelodyButton; // Botón nuevo

    juce::TextButton playButton;
    juce::TextButton stopButton;
    juce::TextButton exportButton;

    // Usamos nuestro componente de Piano Roll personalizado
    PianoRollComponent pianoRollComponent;

    // Almacenamos el resultado de la generación de acordes
    py::dict lastGeneratedChordsData;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};