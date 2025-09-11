// DelayComponent.cpp
#include "DelayComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"
 
DelayComponent::DelayComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
    dryKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 1.0),
    centerVolKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.0),
    sideVolKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.3),
    hpKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.0),
    lpKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 1.0),
    leftKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.2),
    centerKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.5),
    rightKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.7),
    wowKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.5),
    feedbackKnob(BinaryData::knobdelay_png, BinaryData::knobdelay_pngSize, 300.0f, 0.4)
{
    auto setupKnob = [&](CustomKnob& knob, auto setter) {
        addAndMakeVisible(knob);
        knob.setRange(0.0, 1.0);
        knob.onValueChange = [this, setter, &knob]() {
            (audioProcessor.*setter)(knob.getValue());
        };
    };
    
    // Mapeamos los knobs a sus funciones en el procesador
    setupKnob(dryKnob, &NeuraSynthAudioProcessor::setDelayDry);
    setupKnob(centerVolKnob, &NeuraSynthAudioProcessor::setDelayWet);

    setupKnob(sideVolKnob, &NeuraSynthAudioProcessor::setDelaySide);
    setupKnob(hpKnob, &NeuraSynthAudioProcessor::setDelayHPFreq);
    setupKnob(lpKnob, &NeuraSynthAudioProcessor::setDelayLPFreq);
    setupKnob(leftKnob, &NeuraSynthAudioProcessor::setDelayTimeLeft);

    setupKnob(centerKnob, &NeuraSynthAudioProcessor::setDelayTimeCenter);
    setupKnob(rightKnob, &NeuraSynthAudioProcessor::setDelayTimeRight);
    setupKnob(wowKnob, &NeuraSynthAudioProcessor::setDelayWow);
    setupKnob(feedbackKnob, &NeuraSynthAudioProcessor::setDelayFeedback);
    
    // Asignamos valores iniciales para que el DSP y la UI estén sincronizados
    dryKnob.setValue(1.0, juce::sendNotificationSync);
    centerVolKnob.setValue(0.3, juce::sendNotificationSync);
    sideVolKnob.setValue(0.3, juce::sendNotificationSync);
    hpKnob.setValue(0.0, juce::sendNotificationSync);
    lpKnob.setValue(1.0, juce::sendNotificationSync);
    leftKnob.setValue(0.2, juce::sendNotificationSync);
    centerKnob.setValue(0.3, juce::sendNotificationSync);
    rightKnob.setValue(0.4, juce::sendNotificationSync);
    wowKnob.setValue(0.5, juce::sendNotificationSync);
    feedbackKnob.setValue(0.4, juce::sendNotificationSync);
}

DelayComponent::~DelayComponent() {}

void DelayComponent::paint (juce::Graphics& g) 
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

void DelayComponent::resized()
{
    const auto& designBounds = LayoutConstants::DELAY_SECTION;
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect) {
        comp.setBounds(designRect.getX() * scaleX, designRect.getY() * scaleY, designRect.getWidth() * scaleX, designRect.getHeight() * scaleY);
    };

    scaleAndSet(dryKnob, LayoutConstants::Delay::DRY_KNOB);
    scaleAndSet(centerVolKnob, LayoutConstants::Delay::CENTER_VOL_KNOB);
    scaleAndSet(sideVolKnob, LayoutConstants::Delay::SIDE_VOL_KNOB);
    scaleAndSet(hpKnob, LayoutConstants::Delay::HP_KNOB);
    scaleAndSet(lpKnob, LayoutConstants::Delay::LP_KNOB);
    scaleAndSet(leftKnob, LayoutConstants::Delay::LEFT_KNOB);
    scaleAndSet(centerKnob, LayoutConstants::Delay::CENTER_KNOB);
    scaleAndSet(rightKnob, LayoutConstants::Delay::RIGHT_KNOB);
    scaleAndSet(wowKnob, LayoutConstants::Delay::WOW_KNOB);
    scaleAndSet(feedbackKnob, LayoutConstants::Delay::FEEDBACK_KNOB);
}