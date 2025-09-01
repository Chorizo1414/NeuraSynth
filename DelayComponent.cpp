// DelayComponent.cpp
#include "DelayComponent.h"
#include "BinaryData.h"
 
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

void DelayComponent::paint (juce::Graphics& g) {}

void DelayComponent::resized()
{
    // Fila Superior
    dryKnob.setBounds(-17, 0, 100, 100);
    centerVolKnob.setBounds(37, 0, 100, 100);
    sideVolKnob.setBounds(88, 0, 100, 100);
    hpKnob.setBounds(139, 0, 100, 100);
    lpKnob.setBounds(191, 0, 100, 100);

    // Fila Inferior
    leftKnob.setBounds(-16, 65, 100, 100);
    centerKnob.setBounds(36, 65, 100, 100);
    rightKnob.setBounds(89, 65, 100, 100);
    wowKnob.setBounds(140, 65, 100, 100);
    feedbackKnob.setBounds(189, 65, 100, 100);
}