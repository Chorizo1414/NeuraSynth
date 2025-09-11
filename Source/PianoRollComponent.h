#pragma once

#include <JuceHeader.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

class PianoRollComponent  : public juce::Component
{
public:
    PianoRollComponent();
    ~PianoRollComponent() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    
    // Función para recibir los datos musicales desde Python
    void setMusicData(const py::dict& data);

private:
    void drawGrid(juce::Graphics& g);
    void drawKeys(juce::Graphics& g);
    void drawNotes(juce::Graphics& g);
    
    // Almacenamos los datos de las notas aquí
    juce::Array<juce::MidiMessage> notes;
    
    float keyWidth = 30.0f;
    int lowestNote = 36; // C2
    int highestNote = 96; // C7
    
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PianoRollComponent)
};