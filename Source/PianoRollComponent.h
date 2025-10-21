#pragma once

#include <JuceHeader.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <functional>

namespace py = pybind11;

struct NoteInfo
{
    bool isMelody;
    double startTime; // en beats
    double duration;  // en beats
    int midiValue; // Para melodía
    std::vector<int> chordMidiValues; // Para acordes
    std::vector<double> chordNoteOffsets; // Offset por nota respecto al inicio del acorde
    std::vector<double> chordNoteDurations; // Duración individual por nota de acorde
};

class PianoRollComponent : public juce::Component, private juce::Timer
{
public:
    PianoRollComponent();
    ~PianoRollComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;
    void mouseWheelMove(const juce::MouseEvent& event, const juce::MouseWheelDetails& wheel) override;
    void mouseDown(const juce::MouseEvent& event) override;
    void mouseDrag(const juce::MouseEvent& event) override;
    void mouseUp(const juce::MouseEvent& event) override;
    void setMusicData(const py::dict& chords, const py::dict& melody);

    // Esta función nos permitirá leer las notas de forma segura.
    const std::vector<NoteInfo>& getMusicData() const { return musicData; }
    // Estructura para almacenar la información de cada nota de forma clara
    struct Note
    {
        int midiNote;
        float startTime; // en beats
        float duration;  // en beats
        bool isChordNote;
        int infoIndex;
        int chordNoteSlot;
    };

    void setMusicData(const py::dict& data);
    // --- AÑADE ESTA FUNCIÓN ---
    const juce::Array<Note>& getNotes() const { return notes; }
    void startPlayback(double bpm);
    void stopPlayback();

    void setContentChangedCallback(std::function<void()> callback);
    void writeCurrentStateToPyDict(py::dict& target) const;


private:
    
    // Usamos un juce::Array para almacenar nuestras notas.
    juce::Array<Note> notes;
    std::vector<NoteInfo> musicData;

    // --- Parámetros de vista y navegación ---
    float horizontalZoom = 1.0f;
    double horizontalScrollBeats = 0.0;
    double contentLengthBeats = 0.0;

    bool isPlaybackActive = false;
    double playbackPositionBeats = 0.0;
    double secondsPerBeat = 0.5;
    double lastPlaybackUpdateSeconds = 0.0;

    static constexpr int defaultLowestNote = 21;   // A0
    static constexpr int defaultHighestNote = 143; // B10

    int displayLowestNote = defaultLowestNote;
    int visibleNoteCount = 24;
    int displayHighestNote = defaultLowestNote + 24 - 1;
    float verticalScrollRemainder = 0.0f;

    bool isPanning = false;
    juce::Point<int> lastPanPosition;

    bool isDraggingNotes = false;
    int primaryDragNoteIndex = -1;
    juce::Array<int> draggedNoteIndices;
    std::vector<int> draggedMidiOffsets;
    std::vector<double> draggedStartOffsets;
    double dragOffsetBeats = 0.0;
    float dragOffsetNoteY = 0.0f;

    bool isResizingNotes = false;
    juce::Array<int> resizingNoteIndices;
    double resizeAnchorBeats = 0.0;

    void clampHorizontalScroll();
    void clampVerticalScroll();
    void scrollHorizontally(double deltaBeats);
    int scrollVertically(int deltaNotes);
    int getKeyWidth() const noexcept { return 45; }

    int hitTestNote(juce::Point<float> position) const;
    void beginNoteDrag(int noteIndex, const juce::MouseEvent& event);
    void updateDraggedNotes(const juce::MouseEvent& event);
    void endNoteDrag();
    void updateResizedNotes(const juce::MouseEvent& event);
    void endNoteResize();
    void deleteNoteAt(int noteIndex);
    void refreshNoteInfo(int infoIndex);
    void recalculateContentLength();
    void markContentDirty();
    void commitContentChange();

    void timerCallback() override;

    std::function<void()> contentChangedCallback;
    bool hasPendingContentChange = false;
    
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PianoRollComponent)
};