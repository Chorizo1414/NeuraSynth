#pragma once

#include <JuceHeader.h>
#include <vector>
#include "PythonManager.h"
#include "PianoRollComponent.h" // Incluimos nuestro nuevo componente

class NeuraSynthAudioProcessor;

class ChordMelodyTabComponent : public juce::Component, public juce::Timer
{
public:
    ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor);
    ~ChordMelodyTabComponent() override;

    void paint(juce::Graphics&) override;
    void resized() override;

    void timerCallback() override;

private:
    void transpose(int semitones);
    bool prepareAndPlaySequence(bool includeChords, bool includeMelody);
    void resetPlaybackButtonStates();
    void adjustBpmValue(int delta);
    void commitBpmEditorText();
    void updateBpmDisplayFromSlider();
    void setBpmValue(double newValue, juce::NotificationType notification = juce::sendNotification);
    void showNotification(const juce::String& message);
    void updateUiForCurrentState();
    void pushStateToHistory(const py::dict& data);
    void applyStateFromHistory(int newIndex);
    void updateUndoRedoButtonStates();
    py::dict deepCopyMusicDict(const py::dict& source);

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

    std::unique_ptr<juce::ImageButton> likeButton;
    std::unique_ptr<juce::ImageButton> dislikeButton;

    juce::TextButton undoButton;
    juce::TextButton redoButton;

    juce::Slider bpmSlider;
    juce::Label bpmLabel;
    juce::Label bpmValueLabel;
    juce::TextButton bpmIncreaseButton;
    juce::TextButton bpmDecreaseButton;

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

    juce::Label notificationLabel;

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

    struct MusicState
    {
        py::dict data;
        double bpm = 120.0;
    };

    std::vector<MusicState> historyStates;
    int historyCurrentIndex = -1;


    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};