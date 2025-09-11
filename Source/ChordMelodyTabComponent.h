#pragma once

#include <JuceHeader.h>
#include "PythonManager.h"

// Adelantamos la declaración para poder usar la clase sin incluir el header completo
class NeuraSynthAudioProcessor;

//==============================================================================
class ChordMelodyTabComponent : public juce::Component
{
public:
    // El constructor ahora recibe correctamente el procesador de audio
    ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor);
    ~ChordMelodyTabComponent() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    // Guardamos una referencia al procesador para acceder a sus datos, como el PythonManager
    NeuraSynthAudioProcessor& audioProcessor;

    // --- Componentes de la Interfaz ---
    juce::TextEditor promptEditor;
    juce::Label promptLabel;

    juce::ComboBox genreComboBox;
    juce::Label genreLabel;

    juce::ComboBox sentimentComboBox;
    juce::Label sentimentLabel;

    juce::TextButton generateButton;
    juce::TextButton playButton;
    juce::TextButton stopButton;
    juce::TextButton exportButton;

    // Componente para simular el Piano Roll
    juce::Component pianoRollComponent;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};