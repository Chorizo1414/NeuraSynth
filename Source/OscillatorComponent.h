#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "OscillatorSection.h"
#include "WaveformDisplay.h"

class OscillatorComponent : public juce::Component
{
public:
    OscillatorComponent();
    ~OscillatorComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    void setLayoutVariant(int variant);

    OscillatorSection oscSection;
    WaveformDisplay waveDisplay;

    juce::Component fxPanel; 
    juce::TextButton fxToggleButton{ "FX" };

    CustomKnob octKnob;
    CustomKnob fineKnob;
    CustomKnob pitchKnob;
    CustomKnob spreadKnob;
    CustomKnob panKnob;
    CustomKnob positionKnob;
    CustomKnob gainKnob;

private:
    int layoutVariant = 1;
    juce::Rectangle<float> designReferenceBounds;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(OscillatorComponent)
};