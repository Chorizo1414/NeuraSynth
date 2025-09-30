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

    void setMasterGain(float value);
    void setGlide(float value);
    void setDark(float value);
    void setBright(float value);
    void setDrive(float value);
    void setChorusEnabled(bool enabled);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob masterGainKnob;
    CustomKnob glideKnob;
    CustomKnob darkKnob;
    CustomKnob brightKnob;
    CustomKnob driveKnob;
    juce::ImageButton chorusButton;
};