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
    bool prepareAndPlaySequence(bool includeChords, bool includeMelody);
    void resetPlaybackButtonStates();


    NeuraSynthAudioProcessor& audioProcessor;

    // --- Componentes UI ---
    juce::TextEditor promptEditor;
    juce::Label promptLabel;

    juce::ComboBox genreComboBox;
    juce::Label genreLabel;

    juce::ComboBox chordCountComboBox;
    juce::Label chordCountLabel;

    juce::TextButton generateChordsButton;
    juce::TextButton generateMelodyButton; // Botón nuevo

    juce::TextButton transposeUpButton;
    juce::TextButton transposeDownButton;

    juce::Slider bpmSlider;
    juce::Label bpmLabel;

    juce::TextButton playAllButton;
    juce::TextButton playChordsButton;
    juce::TextButton playMelodyButton;
    juce::TextButton stopButton;
    juce::TextButton exportChordsButton;
    juce::TextButton exportMelodyButton;

    juce::TextButton* activePlaybackButton = nullptr;

    PianoRollComponent pianoRollComponent;

    py::dict generatedChords;
    py::dict generatedMelody;

    bool isPlaying = false;
    double startTime = 0.0;
    int nextEventIndex = 0;

    // Estructura para un evento MIDI temporizado
    struct TimedMidiEvent
    {
        double timeInBeats;
        juce::MidiMessage message;

        // Para poder ordenar los eventos por tiempo
        bool operator<(const TimedMidiEvent& other) const { return timeInBeats < other.timeInBeats; }
    };

    juce::Array<TimedMidiEvent> playbackEvents;

    // Almacenamos el resultado de la generacion de acordes
    py::dict lastGeneratedChordsData;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};