#pragma once
#include <JuceHeader.h>

class PianoRollComponent : public juce::Component
{
public:
    PianoRollComponent();
    ~PianoRollComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;
    
    // Función para cargar la secuencia MIDI que vamos a dibujar
    void setMidiSequence(const juce::MidiMessageSequence& sequence);

private:
    juce::MidiMessageSequence midiSequence;
    
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PianoRollComponent)
};