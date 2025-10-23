#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class ReverbComponent : public juce::Component
{
public:
    ReverbComponent(NeuraSynthAudioProcessor& p);
    ~ReverbComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    void setDryLevel(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setWetLevel(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setRoomSize(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setPreDelay(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setDiffusion(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setDamping(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setDecay(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setCallbacksSuppressed(bool shouldSuppress);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob dryKnob;
    CustomKnob wetKnob;
    CustomKnob sizeKnob;
    CustomKnob preDelayKnob;
    CustomKnob diffusionKnob;
    CustomKnob dampKnob;
    CustomKnob decayKnob;
    bool suppressCallbacks = false;
};