// FilterComponent.cpp

#include "FilterComponent.h"
#include "BinaryData.h"

FilterComponent::FilterComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
filterCutoffKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 1.0),
filterResonanceKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0),
filterEnvKnob(BinaryData::knobfilter_png, BinaryData::knobfilter_pngSize, 300.0f, 0.0),
keyButton("KeyButton")
{
    // Configuración del Cutoff
    addAndMakeVisible(filterCutoffKnob);
    filterCutoffKnob.setRange(0.0, 1.0); // 0..1 normalizado
    filterCutoffKnob.onValueChange = [this]()
        {
            const double norm = filterCutoffKnob.getValue();                // 0..1
            const double hz = juce::jmap(norm, 0.0, 1.0, 0.0, 20000.0);   // derecha = 20k
            audioProcessor.setFilterCutoff(hz);
        };
    // <<< INICIAL >>>: a la DERECHA (abierto) y enviado al DSP:
    filterCutoffKnob.setValue(1.0, juce::sendNotificationSync);

    // Configuración de la Resonancia
    addAndMakeVisible(filterResonanceKnob);
    filterResonanceKnob.setRange(0.0, 1.0, 0.0000001);
    filterResonanceKnob.onValueChange = [this]()
        {
            audioProcessor.setFilterResonance(filterResonanceKnob.getValue());
        };
    // <<< INICIAL >>>: a la IZQUIERDA (0.0) y enviado al DSP:
    filterResonanceKnob.setValue(0.0, juce::sendNotificationSync);

    // Configuración de la Cantidad de Envolvente
    addAndMakeVisible(filterEnvKnob);
    filterEnvKnob.setRange(0.0, 1.0, 0.01);
    filterEnvKnob.onValueChange = [this]()
        {
            audioProcessor.setFilterEnvAmount(filterEnvKnob.getValue());
        };
    // <<< INICIAL >>>: a la IZQUIERDA (0.00) y enviado al DSP:
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