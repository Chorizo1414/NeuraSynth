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
        // Ahora el valor del knob ya está en Hz, no necesitamos mapearlo.
        audioProcessor.setFilterCutoff(filterCutoffKnob.getValue());
        };
    filterCutoffKnob.setSkewFactorFromMidPoint(1000.0); // Punto medio en 1000 Hz
    filterCutoffKnob.setValue(20000.0, juce::sendNotificationSync);

    // Función auxiliar para los otros knobs
    auto setupKnob = [&](CustomKnob& knob, float minRange, float maxRange, auto setter) {
        addAndMakeVisible(knob);
        knob.setRange(minRange, maxRange);
        knob.onValueChange = [this, setter, &knob]() {
            (audioProcessor.*setter)(knob.getValue());
            };
        };

    // Aplicamos la configuración a los knobs restantes
    setupKnob(filterResonanceKnob, 0.1f, 1.0f, &NeuraSynthAudioProcessor::setFilterResonance);
    setupKnob(filterEnvKnob, 0.0f, 1.0f, &NeuraSynthAudioProcessor::setFilterEnvAmount);

    // Valores iniciales
    filterResonanceKnob.setValue(0.1, juce::sendNotificationSync);
    filterEnvKnob.setValue(0.0, juce::sendNotificationSync);

    // Configuración del botón de Key Tracking
    addAndMakeVisible(keyButton);
    keyButton.setClickingTogglesState(true);

    // --- CORREGIDOS LOS ERRORES DE TIPEO AQUÍ ---
    auto normalKeyImage = juce::ImageCache::getFromMemory(BinaryData::button_png, BinaryData::button_pngSize);
    auto toggledKeyImage = juce::ImageCache::getFromMemory(BinaryData::buttonreverse_png, BinaryData::buttonreverse_pngSize);

    keyButton.setImages(false, true, true, normalKeyImage, 1.0f, juce::Colours::transparentBlack, toggledKeyImage, 1.0f, juce::Colours::transparentBlack, normalKeyImage, 1.0f, juce::Colours::transparentBlack);
    keyButton.onStateChange = [this]() { audioProcessor.setKeyTrack(keyButton.getToggleState()); };

    // Inicial: OFF y mandado al DSP
    keyButton.setToggleState(false, juce::sendNotificationSync);
}

FilterComponent::~FilterComponent() {}

void FilterComponent::paint(juce::Graphics& g)
{
    // Solo dibuja el borde si el designMode del editor está activo
    if (auto* editor = findParentComponentOfClass<NeuraSynthAudioProcessorEditor>())
    {
        if (editor->designMode)
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

auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect) 
{
    comp.setBounds(designRect.getX() * scaleX, designRect.getY() * scaleY, designRect.getWidth() * scaleX, designRect.getHeight() * scaleY);
};

    scaleAndSet(filterCutoffKnob, LayoutConstants::Filter::CUTOFF_KNOB);
    scaleAndSet(filterResonanceKnob, LayoutConstants::Filter::RES_KNOB);
    scaleAndSet(filterEnvKnob, LayoutConstants::Filter::ENV_KNOB);
    scaleAndSet(keyButton, LayoutConstants::Filter::KEY_BUTTON);
}