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

    OscillatorSection oscSection;
    WaveformDisplay waveDisplay;

    CustomKnob octKnob;
    CustomKnob fineKnob;
    CustomKnob pitchKnob;
    CustomKnob panKnob;
    CustomKnob positionKnob;
    CustomKnob gainKnob;

private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(OscillatorComponent)
};