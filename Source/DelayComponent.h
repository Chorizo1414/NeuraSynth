// DelayComponent.h
#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class DelayComponent : public juce::Component
{
public:
    DelayComponent(NeuraSynthAudioProcessor& p);
    ~DelayComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    void setDryLevel(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setCenterLevel(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setSideLevel(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setHighPass(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setLowPass(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setTimeLeft(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setTimeCenter(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setTimeRight(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setWowDepth(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setFeedback(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setCallbacksSuppressed(bool shouldSuppress);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob dryKnob;
    CustomKnob centerVolKnob;
    CustomKnob sideVolKnob;
    CustomKnob hpKnob;
    CustomKnob lpKnob;
    CustomKnob leftKnob;
    CustomKnob centerKnob;
    CustomKnob rightKnob;
    CustomKnob wowKnob;
    CustomKnob feedbackKnob;
    bool suppressCallbacks = false;
};