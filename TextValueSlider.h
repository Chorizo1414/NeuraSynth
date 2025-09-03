// TextValueSlider.h
#pragma once

#include <JuceHeader.h>

class TextValueSlider : public juce::Component
{
public:
    TextValueSlider(juce::String parameterName, juce::String suffix = "");

    void paint(juce::Graphics& g) override;
    void resized() override;

    void mouseDown(const juce::MouseEvent& event) override;
    void mouseDrag(const juce::MouseEvent& event) override;
    void mouseWheelMove(const juce::MouseEvent& event, const juce::MouseWheelDetails& wheel) override;

    void setRange(double min, double max, double interval);
    void setValue(double newValue);
    double getValue() const { return currentValue; }

    std::function<void(double)> onValueChange;

private:
    double currentValue = 0.0;
    double minValue = 0.0, maxValue = 1.0, interval = 0.01;

    juce::String name;
    juce::String suffix;

    juce::Label valueLabel;
    juce::Point<int> dragStartPos;
    double valueAtDragStart = 0.0;
};