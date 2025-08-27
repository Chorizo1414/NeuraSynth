#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class ReverbComponent  : public juce::Component
{
public:
    ReverbComponent(NeuraSynthAudioProcessor& p);
    ~ReverbComponent() override;

    void paint (juce::Graphics& g) override;
    void resized() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob dryKnob;
    CustomKnob wetKnob;
    CustomKnob sizeKnob;
    CustomKnob preDelayKnob;
    CustomKnob diffusionKnob;
    CustomKnob dampKnob;
    CustomKnob decayKnob;
};