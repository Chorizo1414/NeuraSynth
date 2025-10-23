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
            if (suppressCallbacks)
                return;
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

    auto applyChorusImages = [this, normalImage, toggledImage](bool enabled)
        {
            const auto& image = enabled ? toggledImage : normalImage;

            chorusButton.setImages(
                false, true, true,
                image, 1.0f, juce::Colours::transparentBlack,
                image, 1.0f, juce::Colours::transparentBlack,
                image, 1.0f, juce::Colours::transparentBlack
            );
        };

    applyChorusImages(false);

    chorusButton.onClick = [this, applyChorusImages]()
        {
            const bool enabled = chorusButton.getToggleState();

            if (!suppressCallbacks)
                audioProcessor.setChorus(enabled);

            applyChorusImages(enabled);
        };

}

MasterSectionComponent::~MasterSectionComponent() {}

void MasterSectionComponent::setMasterGain(float value, juce::NotificationType notification)
{
    masterGainKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void MasterSectionComponent::setGlide(float value, juce::NotificationType notification)
{
    glideKnob.setValue(juce::jlimit(0.0f, 2.0f, value), notification);
}

void MasterSectionComponent::setDark(float value, juce::NotificationType notification)
{
    darkKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void MasterSectionComponent::setBright(float value, juce::NotificationType notification)
{
    brightKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void MasterSectionComponent::setDrive(float value, juce::NotificationType notification)
{
    driveKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void MasterSectionComponent::setChorusEnabled(bool enabled, juce::NotificationType notification)
{
    chorusButton.setToggleState(enabled, notification);
}

void MasterSectionComponent::setCallbacksSuppressed(bool shouldSuppress)
{
    suppressCallbacks = shouldSuppress;
}

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
    const auto& designBounds = LayoutConstants::MASTER_SECTION;

    // 2. Calculamos los factores de escala LOCALES (solo para este componente).
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    // 3. Función auxiliar para simplificar el posicionamiento.
    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<float>& designRect)
        {
            juce::Rectangle<float> scaled(designRect.getX() * scaleX,
                designRect.getY() * scaleY,
                designRect.getWidth() * scaleX,
                designRect.getHeight() * scaleY);
            comp.setBounds(scaled.toNearestInt());
        };

    // 4. Aplicamos el posicionamiento a cada control usando el plano.
    scaleAndSet(masterGainKnob, LayoutConstants::Master::MASTER_GAIN_KNOB);
    scaleAndSet(glideKnob, LayoutConstants::Master::GLIDE_KNOB);
    scaleAndSet(driveKnob, LayoutConstants::Master::DRIVE_KNOB);
    scaleAndSet(darkKnob, LayoutConstants::Master::DARK_KNOB);
    scaleAndSet(brightKnob, LayoutConstants::Master::BRIGHT_KNOB);
    scaleAndSet(chorusButton, LayoutConstants::Master::CHORUS_BUTTON);
}
