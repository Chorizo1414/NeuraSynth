#include "ReverbComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

ReverbComponent::ReverbComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
    dryKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.8),
    wetKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.1),
    sizeKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.7),
    preDelayKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.1),
    diffusionKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.8),
    dampKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.8),
    decayKnob(BinaryData::knobreverb_png, BinaryData::knobreverb_pngSize, 300.0f, 0.5)
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

    setupKnob(dryKnob,       &NeuraSynthAudioProcessor::setReverbDryLevel);
    setupKnob(wetKnob,       &NeuraSynthAudioProcessor::setReverbWetLevel);
    setupKnob(sizeKnob,      &NeuraSynthAudioProcessor::setReverbRoomSize);
    setupKnob(preDelayKnob,  &NeuraSynthAudioProcessor::setReverbPreDelay);
    setupKnob(diffusionKnob, &NeuraSynthAudioProcessor::setReverbDiffusion);
    setupKnob(dampKnob,      &NeuraSynthAudioProcessor::setReverbDamping);
    setupKnob(decayKnob,     &NeuraSynthAudioProcessor::setReverbDecay);

    // Asignamos los valores iniciales para que coincidan con el motor de audio
    dryKnob.setValue(0.8, juce::dontSendNotification);
    wetKnob.setValue(0.1, juce::dontSendNotification);
    sizeKnob.setValue(0.7, juce::dontSendNotification);
    preDelayKnob.setValue(0.1, juce::dontSendNotification);
    diffusionKnob.setValue(0.8, juce::dontSendNotification);
    dampKnob.setValue(0.8, juce::dontSendNotification);
    decayKnob.setValue(0.5, juce::dontSendNotification);
}

ReverbComponent::~ReverbComponent() {}

void ReverbComponent::setDryLevel(float value, juce::NotificationType notification)
{
    dryKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setWetLevel(float value, juce::NotificationType notification)
{
    wetKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setRoomSize(float value, juce::NotificationType notification)
{
    sizeKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setPreDelay(float value, juce::NotificationType notification)
{
    preDelayKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setDiffusion(float value, juce::NotificationType notification)
{
    diffusionKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setDamping(float value, juce::NotificationType notification)
{
    dampKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setDecay(float value, juce::NotificationType notification)
{
    decayKnob.setValue(juce::jlimit(0.0f, 1.0f, value), notification);
}

void ReverbComponent::setCallbacksSuppressed(bool shouldSuppress)
{
    suppressCallbacks = shouldSuppress;
}

void ReverbComponent::paint (juce::Graphics& g) 
{
    // Solo dibuja el borde si el designMode del editor estÅEactivo
    if (auto* tab = findParentComponentOfClass<SynthTabComponent>())
    {
        if (tab->designMode)
        {
            g.setColour(juce::Colours::red);
            g.drawRect(getLocalBounds(), 2.0f);
        }
    }
}

void ReverbComponent::resized()
{
    const auto& designBounds = LayoutConstants::REVERB_SECTION;
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<float>& designRect) {
        juce::Rectangle<float> scaled(designRect.getX() * scaleX,
            designRect.getY() * scaleY,
            designRect.getWidth() * scaleX,
            designRect.getHeight() * scaleY);
        comp.setBounds(scaled.toNearestInt());
        };

    scaleAndSet(dryKnob, LayoutConstants::Reverb::DRY_KNOB);
    scaleAndSet(wetKnob, LayoutConstants::Reverb::WET_KNOB);
    scaleAndSet(sizeKnob, LayoutConstants::Reverb::SIZE_KNOB);
    scaleAndSet(preDelayKnob, LayoutConstants::Reverb::PRE_DELAY_KNOB);
    scaleAndSet(diffusionKnob, LayoutConstants::Reverb::DIFFUSION_KNOB);
    scaleAndSet(dampKnob, LayoutConstants::Reverb::DAMP_KNOB);
    scaleAndSet(decayKnob, LayoutConstants::Reverb::DECAY_KNOB);
}