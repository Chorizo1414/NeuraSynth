// TextValueSlider.cpp
#include "TextValueSlider.h"

TextValueSlider::TextValueSlider(juce::String parameterName, juce::String suffix)
    : name(parameterName), suffix(suffix)
{
    addAndMakeVisible(valueLabel);
    valueLabel.setJustificationType(juce::Justification::centred);
    valueLabel.setColour(juce::Label::textColourId, juce::Colours::white);
    //this->setTooltip("Arrastra o usa la rueda del ratón para cambiar " + name);
}

void TextValueSlider::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black.withAlpha(0.5f));
    g.setColour(juce::Colours::white.withAlpha(0.7f));
    g.drawRect(getLocalBounds(), 1.0f);
}

void TextValueSlider::resized()
{
    valueLabel.setBounds(getLocalBounds());
}

void TextValueSlider::setRange(double min, double max, double interval)
{
    minValue = min;
    maxValue = max;
    this->interval = interval;
}

void TextValueSlider::setValue(double newValue)
{
    currentValue = juce::jlimit(minValue, maxValue, newValue);

    int decimalPlaces = (interval < 1.0) ? 2 : 0;
    valueLabel.setText(juce::String(currentValue, decimalPlaces) + suffix, juce::dontSendNotification);

    if (onValueChange)
        onValueChange(currentValue);
}

void TextValueSlider::mouseDown(const juce::MouseEvent& event)
{
    dragStartPos = event.getPosition();
    valueAtDragStart = currentValue;
}

void TextValueSlider::mouseDrag(const juce::MouseEvent& event)
{
    int dy = dragStartPos.y - event.getPosition().y;
    double sensitivity = (maxValue - minValue) / 200.0; // 200 pixeles para recorrer todo el rango
    double newValue = valueAtDragStart + dy * sensitivity;

    // Ajustar al intervalo (snapping)
    newValue = std::round(newValue / interval) * interval;

    setValue(newValue);
}

void TextValueSlider::mouseWheelMove(const juce::MouseEvent&, const juce::MouseWheelDetails& wheel)
{
    double increment = interval * (wheel.isReversed ? -1.0 : 1.0);
    if (wheel.deltaY < 0) increment *= -1.0;

    setValue(currentValue + increment);
}