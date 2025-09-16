#pragma once

#include <JuceHeader.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>

namespace py = pybind11;

struct NoteInfo
{
    bool isMelody;
    double startTime; // en beats
    double duration;  // en beats
    int midiValue; // Para melodía
    std::vector<int> chordMidiValues; // Para acordes
};

class PianoRollComponent : public juce::Component
{
public:
    PianoRollComponent();
    ~PianoRollComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;
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
    };

    void setMusicData(const py::dict& data);
    // --- AÑADE ESTA FUNCIÓN ---
    const juce::Array<Note>& getNotes() const { return notes; }



private:
    
    // Usamos un juce::Array para almacenar nuestras notas.
    juce::Array<Note> notes;
    std::vector<NoteInfo> musicData;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PianoRollComponent)
};