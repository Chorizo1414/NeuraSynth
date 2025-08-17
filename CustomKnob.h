#pragma once
#include <JuceHeader.h>

class CustomKnob : public juce::Slider
{
public:
    CustomKnob(const void* imageData, int imageSize, float totalAngleDegrees = 280.0f, double defaultVal = 0.5);
    ~CustomKnob() override;

    void paint(juce::Graphics&) override;
    void mouseDoubleClick(const juce::MouseEvent& event) override;

private:
    juce::Image knobImage;
    float rotationRangeDegrees;
    double defaultValue;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CustomKnob)
};