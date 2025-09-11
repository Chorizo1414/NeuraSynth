#pragma once
#include <JuceHeader.h>

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
    juce::Label promptLabel;
    juce::TextEditor promptEditor;
    juce::Label numChordsLabel;
    juce::ComboBox numChordsBox;
    juce::TextButton newRhythmButton{ "Nuevo Ritmo" };
    juce::TextButton pauseButton{ "Pausa" };

    juce::Label bpmLabel;
    juce::Slider bpmSlider;

    juce::TextButton createChordsButton{ "Crear Acordes" };
    juce::TextButton generateMelodyButton{ "Generar Melodia" };
    juce::TextButton playAllButton{ "Reproducir Todo" };
    juce::TextButton transposeUpButton{ "Subir Semitono" };
    juce::TextButton transposeDownButton{ "Bajar Semitono" };
    juce::TextButton playMelodyButton{ "Reproducir Melodia" };

    juce::Component pianoRollPlaceholder;
    juce::Label resultsLabel;
    
    // Funciones de acción
    void createChords();
    void generateMelody();
    void playAll();
    void playMelody();
    void transpose(bool up);

    NeuraSynthAudioProcessor& audioProcessor;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};