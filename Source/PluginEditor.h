#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "SynthTabComponent.h"
#include "ChordMelodyTabComponent.h"

class NeuraSynthAudioProcessorEditor : public juce::AudioProcessorEditor
{
public:
    NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor&);
    ~NeuraSynthAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    // Componente que gestionará las pestañas
    juce::TabbedComponent tabbedComponent;
    
    // Instancias de nuestras dos pestañas
    SynthTabComponent synthTab;
    ChordMelodyTabComponent chordMelodyTab;
   
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NeuraSynthAudioProcessorEditor)
};