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
            if (suppressCallbacks)
                return;
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
    dryKnob.setValue(1.0, juce::dontSendNotification);
    centerVolKnob.setValue(0.3, juce::dontSendNotification);
    sideVolKnob.setValue(0.3, juce::dontSendNotification);
    hpKnob.setValue(0.0, juce::dontSendNotification);
    lpKnob.setValue(1.0, juce::dontSendNotification);
    leftKnob.setValue(0.2, juce::dontSendNotification);
    centerKnob.setValue(0.3, juce::dontSendNotification);
    rightKnob.setValue(0.4, juce::dontSendNotification);
    wowKnob.setValue(0.5, juce::dontSendNotification);
    feedbackKnob.setValue(0.4, juce::dontSendNotification);
}

DelayComponent::~DelayComponent() {}

void DelayComponent::setDryLevel(float value, juce::NotificationType notification)
{
    dryKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setCenterLevel(float value, juce::NotificationType notification)
{
    centerVolKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setSideLevel(float value, juce::NotificationType notification)
{
    sideVolKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setHighPass(float value, juce::NotificationType notification)
{
    hpKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setLowPass(float value, juce::NotificationType notification)
{
    lpKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setTimeLeft(float value, juce::NotificationType notification)
{
    leftKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setTimeCenter(float value, juce::NotificationType notification)
{
    centerKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setTimeRight(float value, juce::NotificationType notification)
{
    rightKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setWowDepth(float value, juce::NotificationType notification)
{
    wowKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setFeedback(float value, juce::NotificationType notification)
{
    feedbackKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void DelayComponent::setCallbacksSuppressed(bool shouldSuppress)
{
    suppressCallbacks = shouldSuppress;
}

void DelayComponent::paint(juce::Graphics& g)
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

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<float>& designRect)
        {
            juce::Rectangle<float> scaled(designRect.getX() * scaleX,
                designRect.getY() * scaleY,
                designRect.getWidth() * scaleX,
                designRect.getHeight() * scaleY);
            comp.setBounds(scaled.toNearestInt());
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