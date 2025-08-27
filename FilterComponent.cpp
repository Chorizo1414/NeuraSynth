// FilterComponent.cpp

#include "FilterComponent.h"
#include "BinaryData.h"

FilterComponent::FilterComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
filterCutoffKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 1.0),
filterResonanceKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0),
filterEnvKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0),
keyButton("KeyButton")
{
    // El knob de Cutoff tiene una lógica especial (jmap), lo configuramos por separado
    addAndMakeVisible(filterCutoffKnob);
    filterCutoffKnob.setRange(0.0, 1.0); // 0..1 normalizado
    filterCutoffKnob.onValueChange = [this]() {
        const double hz = juce::jmap(filterCutoffKnob.getValue(), 0.0, 1.0, 20.0, 20000.0);
        audioProcessor.setFilterCutoff(hz);
        };
    filterCutoffKnob.setSkewFactorFromMidPoint(1000.0); // Mapping logarítmico
    filterCutoffKnob.setValue(1.0, juce::sendNotificationSync);

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
    // Puedes dibujar un fondo o borde para esta sección si quieres
}

void FilterComponent::resized()
{
    // Posiciona los controles DENTRO de este componente
    filterCutoffKnob.setBounds(0, 0, 100, 100);
    filterResonanceKnob.setBounds(78, 0, 100, 100);
    filterEnvKnob.setBounds(166, 0, 100, 100);
    keyButton.setBounds(112, 98, 35, 35);
}