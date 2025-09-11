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
    juce::TextEditor promptEditor;
    juce::TextButton generateButton{ "Generate" };
    juce::Label resultsLabel;
    
    void generateChords(); // Funcion que llamar a Python
    NeuraSynthAudioProcessor& audioProcessor;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};