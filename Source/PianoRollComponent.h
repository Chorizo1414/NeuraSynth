#pragma once

#include <JuceHeader.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class PianoRollComponent : public juce::Component
{
public:
    PianoRollComponent();
    ~PianoRollComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    void setMusicData(const py::dict& data);

private:
    // Estructura para almacenar la información de cada nota de forma clara
    struct Note
    {
        int midiNote;
        float startTime; // en beats
        float duration;  // en beats
        bool isChordNote;
    };

    // Usamos un juce::Array para almacenar nuestras notas.
    // ESTE ERA EL PUNTO DEL ERROR ANTERIOR
    juce::Array<Note> notes;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PianoRollComponent)
};