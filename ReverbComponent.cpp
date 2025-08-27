#include "ReverbComponent.h"
#include "BinaryData.h"

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

void ReverbComponent::paint (juce::Graphics& g) {}

void ReverbComponent::resized()
{
    // Posicionamos los knobs relativos a este componente
    // Fila superior
    dryKnob.setBounds(35, -1, 100, 100);      // x=0, y=0
    wetKnob.setBounds(104, 0, 100, 100);      // x=72, y=0
    sizeKnob.setBounds(169, -2, 100, 100);     // x=137, y=0
    // Fila inferior
    preDelayKnob.setBounds(0, 60, 100, 100); // x=-33, y=60
    diffusionKnob.setBounds(66, 62, 100, 100);
    dampKnob.setBounds(132, 61, 100, 100);
    decayKnob.setBounds(198, 62, 100, 100);
}