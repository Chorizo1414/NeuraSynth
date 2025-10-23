// FilterComponent.cpp

#include "FilterComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"


FilterComponent::FilterComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
filterCutoffKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 1.0),
filterResonanceKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0),
filterEnvKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0),
keyButton("KeyButton")
{
    // El knob de Cutoff tiene una lógica especial (jmap), lo configuramos por separado
    addAndMakeVisible(filterCutoffKnob);
    filterCutoffKnob.setRange(20.0, 20000.0); // Rango en Hertz
    filterCutoffKnob.onValueChange = [this]() {
        if (suppressCallbacks)
            return;
        // Ahora el valor del knob ya está en Hz, no necesitamos mapearlo.
        audioProcessor.setFilterCutoff(filterCutoffKnob.getValue());
        };
    filterCutoffKnob.setSkewFactorFromMidPoint(1000.0); // Punto medio en 1000 Hz
    filterCutoffKnob.setValue(20000.0, juce::dontSendNotification);

    // Función auxiliar para los otros knobs
    auto setupKnob = [&](CustomKnob& knob, float minRange, float maxRange, auto setter) {
        addAndMakeVisible(knob);
        knob.setRange(minRange, maxRange);
        knob.onValueChange = [this, setter, &knob]() {
            if (suppressCallbacks)
                return;
            (audioProcessor.*setter)(knob.getValue());
            };
        };

    // Aplicamos la configuración a los knobs restantes
    setupKnob(filterResonanceKnob, 0.1f, 10.0f, &NeuraSynthAudioProcessor::setFilterResonance);
    setupKnob(filterEnvKnob, -1.0f, 1.0f, &NeuraSynthAudioProcessor::setFilterEnvAmount);

    // Valores iniciales
    filterResonanceKnob.setValue(0.1, juce::dontSendNotification);
    filterEnvKnob.setValue(0.0, juce::dontSendNotification);

    // Configuración del botón de Key Tracking
    addAndMakeVisible(keyButton);

    auto keyOff = juce::ImageCache::getFromMemory(BinaryData::button_png, BinaryData::button_pngSize);
    auto keyOn = juce::ImageCache::getFromMemory(BinaryData::buttonreverse_png, BinaryData::buttonreverse_pngSize);

    keyButton.setImages(false, true, true,
        keyOff, 1.0f, juce::Colours::transparentBlack, // Imagen Normal
        keyOff, 1.0f, juce::Colours::transparentBlack, // Imagen Mouse Encima (Hover)
        keyOn, 1.0f, juce::Colours::transparentBlack); // Imagen Presionado (y Activado)

    keyButton.setClickingTogglesState(true);
    keyButton.onStateChange = [this]() {
        if (suppressCallbacks)
            return;
        audioProcessor.setKeyTrack(keyButton.getToggleState());
        };
}

FilterComponent::~FilterComponent() {}

void FilterComponent::paint(juce::Graphics& g)
{
    // Solo dibuja el borde si el designMode del editor está activo
    if (auto* tab = findParentComponentOfClass<SynthTabComponent>())
    {
        if (tab->designMode)
        {
            g.setColour(juce::Colours::red);
            g.drawRect(getLocalBounds(), 2.0f);
        }
    }
}

void FilterComponent::resized()
{
    const auto& designBounds = LayoutConstants::FILTER_SECTION;
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<float>& designRect)
        {
            juce::Rectangle<float> scaled(designRect.getX() * scaleX,
                designRect.getY() * scaleY,
                designRect.getWidth() * scaleX,
                designRect.getHeight() * scaleY);
            comp.setBounds(scaled.toNearestInt());
        };

    scaleAndSet(filterCutoffKnob, LayoutConstants::Filter::CUTOFF_KNOB);
    scaleAndSet(filterResonanceKnob, LayoutConstants::Filter::RES_KNOB);
    scaleAndSet(filterEnvKnob, LayoutConstants::Filter::ENV_KNOB);
    scaleAndSet(keyButton, LayoutConstants::Filter::KEY_BUTTON);
}

void FilterComponent::setCutoffValue(double hz, juce::NotificationType notification)
{
    filterCutoffKnob.setValue(hz, notification);
}

void FilterComponent::setResonanceValue(double q, juce::NotificationType notification)
{
    filterResonanceKnob.setValue(q, notification);
}

void FilterComponent::setEnvAmountValue(double amount, juce::NotificationType notification)
{
    filterEnvKnob.setValue(amount, notification);
}

void FilterComponent::setKeyTrackEnabled(bool enabled, juce::NotificationType notification)
{
    keyButton.setToggleState(enabled, notification);
}

void FilterComponent::setCallbacksSuppressed(bool shouldSuppress)
{
    suppressCallbacks = shouldSuppress;
}