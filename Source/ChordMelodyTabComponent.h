#pragma once
#include <JuceHeader.h>
#include "TextValueSlider.h"

class NeuraSynthAudioProcessor;

class ChordMelodyTabComponent : public juce::Component
{
public:
    ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor);
    ~ChordMelodyTabComponent() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    // Controles de la UI
    juce::TextEditor promptEditor;
    juce::TextButton createChordsButton{ "Crear Acordes" };
    juce::TextButton generateMelodyButton{ "Generar Melod
a" };
    juce::ComboBox chordCountCombo;
    juce::TextButton newRhythmButton{ "Nuevo Ritmo" };
    juce::TextButton pauseButton{ "Pausa" };
    TextValueSlider bpmSlider{ "BPM" };
    juce::TextButton transposeUpButton{ "Subir Semitono" };
    juce::TextButton transposeDownButton{ "Bajar Semitono" };
    juce::Label transposeLabel;
    juce::TextButton playAllButton{ "Reproducir Todo" };
    juce::TextButton playMelodyButton{ "Reproducir Melod
a" };
    juce::Label resultsLabel;
    
    int transposition = 0;

    void createChords();     // Funcin que llama a Python para acordes
    void generateody();   // Funcin que llamaPython para la melod
a
    
    NeuraSynthAudioProcessor& audioProcessor;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};