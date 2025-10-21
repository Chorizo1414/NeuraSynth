#include "OscillatorComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

OscillatorComponent::OscillatorComponent() :
    octKnob(BinaryData::knoboct_png, BinaryData::knoboct_pngSize, 300.0f, 0.5),
    fineKnob(BinaryData::knoboct_png, BinaryData::knoboct_pngSize, 300.0f, 0.5),
    pitchKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),
    spreadKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.0),
    panKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),
    positionKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.0),
    gainKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5)
{
    designReferenceBounds = LayoutConstants::OSC_1_SECTION;

    addAndMakeVisible(oscSection);
    addAndMakeVisible(waveDisplay);
    addAndMakeVisible(octKnob);
    addAndMakeVisible(fineKnob);
    addAndMakeVisible(pitchKnob);
    addAndMakeVisible(spreadKnob);
    addAndMakeVisible(panKnob);
    addAndMakeVisible(positionKnob);
    addAndMakeVisible(gainKnob);
}

OscillatorComponent::~OscillatorComponent() {}

void OscillatorComponent::paint(juce::Graphics& g) 
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

void OscillatorComponent::resized()
{
    if (getWidth() <= 0 || getHeight() <= 0)
        return;

    if (designReferenceBounds.getWidth() <= 0.0f || designReferenceBounds.getHeight() <= 0.0f)
        designReferenceBounds = LayoutConstants::OSC_1_SECTION;

    const auto layout = LayoutConstants::Oscillator::getLayoutForVariant(layoutVariant);

    float scaleX = (float)getWidth() / designReferenceBounds.getWidth();
    float scaleY = (float)getHeight() / designReferenceBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<float>& designRect) {
        juce::Rectangle<float> scaled(designRect.getX() * scaleX,
            designRect.getY() * scaleY,
            designRect.getWidth() * scaleX,
            designRect.getHeight() * scaleY);
        comp.setBounds(scaled.toNearestInt());
        };

    scaleAndSet(oscSection, layout.waveSelect);
    scaleAndSet(waveDisplay, layout.waveDisplay);
    scaleAndSet(octKnob, layout.octKnob);
    scaleAndSet(fineKnob, layout.fineKnob);
    scaleAndSet(pitchKnob, layout.pitchKnob);
    scaleAndSet(spreadKnob, layout.spreadKnob);
    scaleAndSet(panKnob, layout.panKnob);
    scaleAndSet(positionKnob, layout.positionKnob);
    scaleAndSet(gainKnob, layout.gainKnob);
}

void OscillatorComponent::setLayoutVariant(int variant)
{
    int clamped = juce::jlimit(1, 3, variant);
    if (layoutVariant == clamped && designReferenceBounds.getWidth() > 0.0f)
        return;

    layoutVariant = clamped;

    switch (layoutVariant)
    {
    case 2:
        designReferenceBounds = LayoutConstants::OSC_2_SECTION;
        break;
    case 3:
        designReferenceBounds = LayoutConstants::OSC_3_SECTION;
        break;
    default:
        designReferenceBounds = LayoutConstants::OSC_1_SECTION;
        break;
    }

    resized();
}