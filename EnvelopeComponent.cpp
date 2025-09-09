 // EnvelopeComponent.cpp
#include "EnvelopeComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

EnvelopeComponent::EnvelopeComponent(NeuraSynthAudioProcessor & p) : audioProcessor(p),
attackKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.01),
decayKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.5),
sustainKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.5),
releaseKnob(BinaryData::knobenvelope_png, BinaryData::knobenvelope_pngSize, 300.0f, 0.5)
{
	addAndMakeVisible(envelopeDisplay);
	addAndMakeVisible(attackKnob);
	attackKnob.setRange(0.0, 5.0);
	addAndMakeVisible(decayKnob);
	decayKnob.setRange(0.0, 5.0);
	addAndMakeVisible(sustainKnob);
	sustainKnob.setRange(0.0, 1.0);
	addAndMakeVisible(releaseKnob);
	releaseKnob.setRange(0.0, 5.0);
	
	auto updateEnvelope = [this]() {
		float attack = attackKnob.getValue();
		float decay = decayKnob.getValue();
		float sustain = sustainKnob.getValue();
		float release = releaseKnob.getValue();
		
		envelopeDisplay.setADSR(attack, decay, sustain, release);
		audioProcessor.setAttack(attack);
		audioProcessor.setDecay(decay);
		audioProcessor.setSustain(sustain);
		audioProcessor.setRelease(release);
	};
	
	attackKnob.onValueChange = updateEnvelope;
	decayKnob.onValueChange = updateEnvelope;
	sustainKnob.onValueChange = updateEnvelope;
	releaseKnob.onValueChange = updateEnvelope;
	
	updateEnvelope();
}

EnvelopeComponent::~EnvelopeComponent() {}

void EnvelopeComponent::paint(juce::Graphics& g)
{
	// Solo dibuja el borde si el designMode del editor está activo
	if (auto* tab = findParentComponentOfClass<SynthTabComponent>())
	{
		if (tab->designMode)
		{
			g.setColour(juce::Colours::red);
			g.drawRect(getLocalBounds(), 2.0f);
		}
	}
}

void EnvelopeComponent::resized()
{
    const auto& designBounds = LayoutConstants::ENVELOPE_SECTION;
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect) {
        comp.setBounds(designRect.getX() * scaleX, designRect.getY() * scaleY, designRect.getWidth() * scaleX, designRect.getHeight() * scaleY);
    };

    scaleAndSet(envelopeDisplay, LayoutConstants::Envelope::DISPLAY);
    scaleAndSet(attackKnob, LayoutConstants::Envelope::ATTACK_KNOB);
    scaleAndSet(decayKnob, LayoutConstants::Envelope::DECAY_KNOB);
    scaleAndSet(sustainKnob, LayoutConstants::Envelope::SUSTAIN_KNOB);
    scaleAndSet(releaseKnob, LayoutConstants::Envelope::RELEASE_KNOB);
}