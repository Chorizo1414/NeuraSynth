#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class ModulationComponent : public juce::Component
{
public:
    ModulationComponent(NeuraSynthAudioProcessor& p);
    ~ModulationComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    // --- Aquí irán los controles de LFO y FM ---
    CustomKnob fmKnob;
    CustomKnob lfoSpeedKnob;
    CustomKnob lfoAmountKnob;

};