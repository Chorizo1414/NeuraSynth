// FilterComponent.h

#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class FilterComponent : public juce::Component
{
public:
    FilterComponent(NeuraSynthAudioProcessor& p);
    ~FilterComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob filterCutoffKnob;
    CustomKnob filterResonanceKnob;
    CustomKnob filterEnvKnob;
    juce::ImageButton keyButton;
    
    // Si usas el modo diseño, puedes añadir esto también
    // DesignMouseListener designMouseListener;
};