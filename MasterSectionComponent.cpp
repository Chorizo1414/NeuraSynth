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
    addAndMakeVisible(masterGainKnob);
    masterGainKnob.setRange(0.0, 1.0);
    masterGainKnob.setValue(0.7);
    masterGainKnob.onValueChange = [this]() { audioProcessor.setMasterGain(masterGainKnob.getValue()); };

    addAndMakeVisible(glideKnob);
    glideKnob.setRange(0.0, 2.0); // Glide time in seconds
    glideKnob.onValueChange = [this]() { audioProcessor.setGlide(glideKnob.getValue()); };

    addAndMakeVisible(darkKnob);
    darkKnob.setRange(0.0, 1.0);
    darkKnob.onValueChange = [this]() { audioProcessor.setDark(darkKnob.getValue()); };

    addAndMakeVisible(brightKnob);
    brightKnob.setRange(0.0, 1.0);
    brightKnob.onValueChange = [this]() { audioProcessor.setBright(brightKnob.getValue()); };

    addAndMakeVisible(driveKnob);
    driveKnob.setRange(0.0, 1.0);
    driveKnob.onValueChange = [this]() { audioProcessor.setDrive(driveKnob.getValue()); };

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