// FilterComponent.h

#pragma once

#include <JuceHeader.h>
#include "CustomKnob.h"
#include "PluginProcessor.h"

class FilterComponent : public juce::Component
{
public:
    FilterComponent(NeuraSynthAudioProcessor& p);
    ~FilterComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;
    void setCutoffValue(double hz, juce::NotificationType notification = juce::sendNotificationSync);
    void setResonanceValue(double q, juce::NotificationType notification = juce::sendNotificationSync);
    void setEnvAmountValue(double amount, juce::NotificationType notification = juce::sendNotificationSync);
    void setKeyTrackEnabled(bool enabled, juce::NotificationType notification = juce::sendNotificationSync);
    void setCallbacksSuppressed(bool shouldSuppress);

private:
    NeuraSynthAudioProcessor& audioProcessor;

    CustomKnob filterCutoffKnob;
    CustomKnob filterResonanceKnob;
    CustomKnob filterEnvKnob;
    juce::ImageButton keyButton;
    bool suppressCallbacks = false;

    // Si usas el modo diseño, puedes añadir esto también
    // DesignMouseListener designMouseListener;
};