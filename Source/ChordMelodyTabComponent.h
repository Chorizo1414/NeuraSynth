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
    void transpose(int semitones);
    NeuraSynthAudioProcessor& audioProcessor;

    // --- Componentes UI ---
    juce::TextEditor promptEditor;
    juce::Label promptLabel;

    juce::ComboBox genreComboBox;
    juce::Label genreLabel;

    juce::TextButton generateChordsButton;
    juce::TextButton generateMelodyButton; // Botón nuevo

    juce::TextButton transposeUpButton;
    juce::TextButton transposeDownButton;

    juce::TextButton playButton;
    juce::TextButton stopButton;
    juce::TextButton exportChordsButton;
    juce::TextButton exportMelodyButton;

    // Usamos nuestro componente de Piano Roll personalizado
    PianoRollComponent pianoRollComponent;

    // Almacenamos el resultado de la generación de acordes
    py::dict lastGeneratedChordsData;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};