// DelayComponent.h
#pragma once
 
#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class DelayComponent  : public juce::Component
{
public:
    DelayComponent(NeuraSynthAudioProcessor& p);
    ~DelayComponent() override;
 
    void paint (juce::Graphics& g) override;
    void resized() override;
 
private:
    NeuraSynthAudioProcessor& audioProcessor;
 
    CustomKnob dryKnob;
    CustomKnob centerVolKnob;
    CustomKnob sideVolKnob;
    CustomKnob hpKnob;
    CustomKnob lpKnob;
    CustomKnob leftKnob;
    CustomKnob centerKnob;
    CustomKnob rightKnob;
    CustomKnob wowKnob;
    CustomKnob feedbackKnob;
};