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

	void setAttackValue(float value);
	void setDecayValue(float value);
	void setSustainValue(float value);
	void setReleaseValue(float value);
	
private:
	NeuraSynthAudioProcessor & audioProcessor;
	
	EnvelopeDisplay envelopeDisplay;
	CustomKnob attackKnob;
	CustomKnob decayKnob;
	CustomKnob sustainKnob;
	CustomKnob releaseKnob;
};