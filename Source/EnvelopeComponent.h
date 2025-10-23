// EnvelopeComponent.h
#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "CustomKnob.h"
#include "EnvelopeDisplay.h"

class EnvelopeComponent : public juce::Component
{
public:
    EnvelopeComponent(NeuraSynthAudioProcessor& p);
    ~EnvelopeComponent() override;
    void paint(juce::Graphics& g) override;
    void resized() override;

    void setAttackValue(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setDecayValue(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setSustainValue(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setReleaseValue(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setCallbacksSuppressed(bool shouldSuppress);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    EnvelopeDisplay envelopeDisplay;
    CustomKnob attackKnob;
    CustomKnob decayKnob;
    CustomKnob sustainKnob;
    CustomKnob releaseKnob;
    bool suppressCallbacks = false;
};