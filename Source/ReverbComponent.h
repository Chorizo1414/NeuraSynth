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

    void setDryLevel(float value);
    void setWetLevel(float value);
    void setRoomSize(float value);
    void setPreDelay(float value);
    void setDiffusion(float value);
    void setDamping(float value);
    void setDecay(float value);

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