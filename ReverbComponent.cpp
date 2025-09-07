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
    dryKnob.setValue(0.8, juce::sendNotificationSync);
    wetKnob.setValue(0.1, juce::sendNotificationSync);
    sizeKnob.setValue(0.7, juce::sendNotificationSync);
    preDelayKnob.setValue(0.1, juce::sendNotificationSync);
    diffusionKnob.setValue(0.8, juce::sendNotificationSync);
    dampKnob.setValue(0.8, juce::sendNotificationSync);
    decayKnob.setValue(0.5, juce::sendNotificationSync);
}

ReverbComponent::~ReverbComponent() {}

void ReverbComponent::paint (juce::Graphics& g) 
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

void ReverbComponent::resized()
{
    const auto& designBounds = LayoutConstants::REVERB_SECTION;
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect) {
        comp.setBounds(designRect.getX() * scaleX, designRect.getY() * scaleY, designRect.getWidth() * scaleX, designRect.getHeight() * scaleY);
    };

    scaleAndSet(dryKnob, LayoutConstants::Reverb::DRY_KNOB);
    scaleAndSet(wetKnob, LayoutConstants::Reverb::WET_KNOB);
    scaleAndSet(sizeKnob, LayoutConstants::Reverb::SIZE_KNOB);
    scaleAndSet(preDelayKnob, LayoutConstants::Reverb::PRE_DELAY_KNOB);
    scaleAndSet(diffusionKnob, LayoutConstants::Reverb::DIFFUSION_KNOB);
    scaleAndSet(dampKnob, LayoutConstants::Reverb::DAMP_KNOB);
    scaleAndSet(decayKnob, LayoutConstants::Reverb::DECAY_KNOB);
}