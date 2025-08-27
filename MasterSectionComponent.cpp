#include "MasterSectionComponent.h"
#include "BinaryData.h"

MasterSectionComponent::MasterSectionComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
    masterGainKnob(BinaryData::knobmastergain_png, BinaryData::knobmastergain_pngSize, 300.0f, 0.7),
    glideKnob(BinaryData::knobmaster_png, BinaryData::knobmaster_pngSize, 300.0f, 0.0),
    darkKnob(BinaryData::knobmaster_png, BinaryData::knobmaster_pngSize, 300.0f, 0.0),
    brightKnob(BinaryData::knobmaster_png, BinaryData::knobmaster_pngSize, 300.0f, 0.0),
    driveKnob(BinaryData::knobmaster_png, BinaryData::knobmaster_pngSize, 300.0f, 0.0),
    chorusButton("ChorusButton")
{
    // Función auxiliar para configurar knobs
    auto setupKnob = [&](CustomKnob& knob, float minRange, float maxRange, auto setter) {
        addAndMakeVisible(knob);
        knob.setRange(minRange, maxRange);
        knob.onValueChange = [this, setter, &knob]() {
            (audioProcessor.*setter)(knob.getValue());
            };
        };

    // Aplicamos la configuración a cada knob
    setupKnob(masterGainKnob, 0.0f, 1.0f, &NeuraSynthAudioProcessor::setMasterGain);
    setupKnob(glideKnob, 0.0f, 2.0f, &NeuraSynthAudioProcessor::setGlide);
    setupKnob(darkKnob, 0.0f, 1.0f, &NeuraSynthAudioProcessor::setDark);
    setupKnob(brightKnob, 0.0f, 1.0f, &NeuraSynthAudioProcessor::setBright);
    setupKnob(driveKnob, 0.0f, 1.0f, &NeuraSynthAudioProcessor::setDrive);
    
    // Valores iniciales
    masterGainKnob.setValue(0.7, juce::dontSendNotification);
    glideKnob.setValue(0.0, juce::dontSendNotification);
    darkKnob.setValue(0.0, juce::dontSendNotification);
    brightKnob.setValue(0.0, juce::dontSendNotification);
    driveKnob.setValue(0.0, juce::dontSendNotification);

    // La configuración del botón Chorus es única, así que la dejamos separada
    addAndMakeVisible(chorusButton);
    chorusButton.setClickingTogglesState(true);

    auto normalImage = juce::ImageCache::getFromMemory(BinaryData::button_png, BinaryData::button_pngSize);
    auto toggledImage = juce::ImageCache::getFromMemory(BinaryData::buttonreverse_png, BinaryData::buttonreverse_pngSize);

    // Imagen inicial: solo normal para todos los estados
    chorusButton.setImages(
        false, true, true,
        normalImage, 1.0f, juce::Colours::transparentBlack,
        normalImage, 1.0f, juce::Colours::transparentBlack,
        normalImage, 1.0f, juce::Colours::transparentBlack
    );

    chorusButton.onClick = [this, normalImage, toggledImage]() {
        audioProcessor.setChorus(chorusButton.getToggleState());
        if (chorusButton.getToggleState())
        {
            chorusButton.setImages(
                false, true, true,
                toggledImage, 1.0f, juce::Colours::transparentBlack,
                toggledImage, 1.0f, juce::Colours::transparentBlack,
                toggledImage, 1.0f, juce::Colours::transparentBlack
            );
        }
        else
        {
            chorusButton.setImages(
                false, true, true,
                normalImage, 1.0f, juce::Colours::transparentBlack,
                normalImage, 1.0f, juce::Colours::transparentBlack,
                normalImage, 1.0f, juce::Colours::transparentBlack
            );
        }
        };

}

MasterSectionComponent::~MasterSectionComponent() {}

void MasterSectionComponent::paint (juce::Graphics& g) {}

void MasterSectionComponent::resized()
{
    // Posicionamos los controles relativos a este componente.
    // Usamos las coordenadas que tenías en el editor, pero ajustadas a un origen local.
    masterGainKnob.setBounds(23, 0, 100, 100);
    glideKnob.setBounds(118 - 33, 63 - 58, 100, 100);   // x=85, y=5
    darkKnob.setBounds(33 - 33, 118 - 58, 100, 100);    // x=0, y=60
    brightKnob.setBounds(86 - 33, 118 - 58, 100, 100);  // x=53, y=60
    driveKnob.setBounds(137 - 33, 118 - 58, 100, 100);  // x=104, y=60
    chorusButton.setBounds(225 - 33, 163 - 58, 35, 35); // x=192, y=105
}