#include "MasterSectionComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

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

void MasterSectionComponent::paint(juce::Graphics& g)
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

void MasterSectionComponent::resized()
{
    // El componente ya tiene el tamaño correcto gracias al PluginEditor.
    // Ahora escalamos los knobs internos basándonos en el plano de diseño.
      
    // 1. Obtenemos las dimensiones de diseño de esta sección desde el plano.
    const auto & designBounds = LayoutConstants::MASTER_SECTION;
    
    // 2. Calculamos los factores de escala LOCALES (solo para este componente).
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();
   
    // 3. Función auxiliar para simplificar el posicionamiento.
    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect)
    {
        comp.setBounds(designRect.getX() * scaleX,
        designRect.getY() * scaleY,
        designRect.getWidth() * scaleX,
        designRect.getHeight() * scaleY);
    };
    
    // 4. Aplicamos el posicionamiento a cada control usando el plano.
    scaleAndSet(masterGainKnob, LayoutConstants::Master::MASTER_GAIN_KNOB);
    scaleAndSet(glideKnob, LayoutConstants::Master::GLIDE_KNOB);
    scaleAndSet(driveKnob, LayoutConstants::Master::DRIVE_KNOB);
    scaleAndSet(darkKnob, LayoutConstants::Master::DARK_KNOB);
    scaleAndSet(brightKnob, LayoutConstants::Master::BRIGHT_KNOB);
    scaleAndSet(chorusButton, LayoutConstants::Master::CHORUS_BUTTON);
}
