#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class MasterSectionComponent  : public juce::Component
{
public:
    MasterSectionComponent(NeuraSynthAudioProcessor& p);
    ~MasterSectionComponent() override;

    void paint (juce::Graphics& g) override;
    void resized() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob glideKnob;
    CustomKnob darkKnob;
    CustomKnob brightKnob;
    CustomKnob driveKnob;
    juce::ImageButton chorusButton;
    
    // El Master Gain Knob lo dejaremos fuera por ahora, ya que está separado visualmente,
    // pero si quieres moverlo aquí más tarde, es fácil hacerlo.
};