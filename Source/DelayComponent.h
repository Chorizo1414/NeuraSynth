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
    
    void setDryLevel(float value);
    void setCenterLevel(float value);
    void setSideLevel(float value);
    void setHighPass(float value);
    void setLowPass(float value);
    void setTimeLeft(float value);
    void setTimeCenter(float value);
    void setTimeRight(float value);
    void setWowDepth(float value);
    void setFeedback(float value);

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