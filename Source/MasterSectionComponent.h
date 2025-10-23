#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class MasterSectionComponent : public juce::Component
{
public:
    MasterSectionComponent(NeuraSynthAudioProcessor& p);
    ~MasterSectionComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    void setMasterGain(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setGlide(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setDark(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setBright(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setDrive(float value, juce::NotificationType notification = juce::sendNotificationSync);
    void setChorusEnabled(bool enabled, juce::NotificationType notification = juce::sendNotificationSync);
    void setCallbacksSuppressed(bool shouldSuppress);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob masterGainKnob;
    CustomKnob glideKnob;
    CustomKnob darkKnob;
    CustomKnob brightKnob;
    CustomKnob driveKnob;
    juce::ImageButton chorusButton;
    bool suppressCallbacks = false;
};