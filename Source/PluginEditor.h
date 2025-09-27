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

    juce::TabbedComponent tabbedComponent;
    SynthTabComponent synthTab;
    ChordMelodyTabComponent chordMelodyTab;
   
    juce::MidiKeyboardState keyboardState;
    juce::MidiKeyboardComponent keyboardComponent;

    std::unique_ptr<juce::ComponentBoundsConstrainer> constrainer;
    juce::AudioProcessorValueTreeState::Listener* vtsListener = nullptr;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NeuraSynthAudioProcessorEditor)
};