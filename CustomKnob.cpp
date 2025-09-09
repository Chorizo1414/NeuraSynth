#include "CustomKnob.h"
#include "BinaryData.h"

CustomKnob::CustomKnob(const void* imageData, int imageSize, float totalAngleDegrees, double defaultVal)
    : juce::Slider(juce::Slider::RotaryHorizontalVerticalDrag, juce::Slider::NoTextBox),
    rotationRangeDegrees(totalAngleDegrees),
    defaultValue(defaultVal)
{
    knobImage = juce::ImageCache::getFromMemory(imageData, imageSize);
    setWantsKeyboardFocus(false);

    // Asegura que el valor inicial del knob sea su valor por defecto
    setValue(defaultValue, juce::dontSendNotification);
}

CustomKnob::~CustomKnob() {}

void CustomKnob::paint(juce::Graphics& g)
{
    if (knobImage.isValid())
    {
        const float normalizedValue = (float)((getValue() - getMinimum()) / (getMaximum() - getMinimum()));
        const float totalAngleRadians = rotationRangeDegrees * juce::MathConstants<float>::pi / 180.0f;
        const float angle = (normalizedValue - 0.5f) * totalAngleRadians;

        // Calculamos un factor de escala para que la imagen siempre quepa dentro del componente
        const float scale = juce::jmin((float)getWidth() / knobImage.getWidth(), (float)getHeight() / knobImage.getHeight());

        const float centerX = getWidth() * 0.5f;
        const float centerY = getHeight() * 0.5f;
        const float halfWidth = knobImage.getWidth() * 0.5f;
        const float halfHeight = knobImage.getHeight() * 0.5f;
        juce::AffineTransform transform = juce::AffineTransform::translation(-halfWidth, -halfHeight)
            .rotated(angle)
            .scaled(scale) // Aplicamos el factor de escala
            .translated(centerX, centerY);
        g.drawImageTransformed(knobImage, transform, false);
    }
    else
    {
        juce::Slider::paint(g);
    }
}

void CustomKnob::mouseDoubleClick(const juce::MouseEvent&)
{
    // Calculamos el valor de destino basonos en el 'defaultValue' (0.0, 0.5, o 1.0)
    // y el rango actual del knob (por ejemplo, -12 a 12).
    double targetValue = getMinimum() + (getMaximum() - getMinimum()) * defaultValue;

    // Para los knobs que se mueven en pasos (como octava o pitch),
    // nos aseguramos de que el valor se ajuste al paso ms cercano.
    if (getInterval() > 0)
        targetValue = std::round(targetValue / getInterval()) * getInterval();

    setValue(targetValue);
}