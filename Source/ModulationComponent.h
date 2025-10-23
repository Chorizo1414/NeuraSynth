#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class ModulationComponent : public juce::Component
{
public:
    ModulationComponent(NeuraSynthAudioProcessor& p);
    ~ModulationComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;
    void setFmAmountValue(float amount, juce::NotificationType notification = juce::sendNotificationSync);
    void setLfoSpeedValue(float hz, juce::NotificationType notification = juce::sendNotificationSync);
    void setLfoAmountValue(float amount, juce::NotificationType notification = juce::sendNotificationSync);
    void setCallbacksSuppressed(bool shouldSuppress);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    // --- Aquí irán los controles de LFO y FM ---
    CustomKnob fmKnob;
    CustomKnob lfoSpeedKnob;
    CustomKnob lfoAmountKnob;
    bool suppressCallbacks = false;

};