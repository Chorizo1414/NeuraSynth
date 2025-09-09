#include "OscillatorComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

OscillatorComponent::OscillatorComponent() :
    octKnob(BinaryData::knoboct_png, BinaryData::knoboct_pngSize, 300.0f, 0.5),      // En medio
    fineKnob(BinaryData::knoboct_png, BinaryData::knoboct_pngSize, 300.0f, 0.5),     // En medio
    pitchKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),    // En medio
    spreadKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.0),   // Izquierda (como estaba)
    panKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),      // En medio (L/R)
    positionKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.0), // Izquierda (como estaba)
    gainKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5)      // En medio (50%)
{
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
    const auto& designBounds = LayoutConstants::OSC_1_SECTION; // Usamos OSC_1 como referencia, son iguales
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect) {
        comp.setBounds(designRect.getX() * scaleX, designRect.getY() * scaleY, designRect.getWidth() * scaleX, designRect.getHeight() * scaleY);
    };

    // No tenemos Unison en el plano, así que lo dejamos como estaba o lo añadimos al plano
    // Por ahora, lo posicionamos manualmente
    // unisonComp.setBounds(...) 

    scaleAndSet(oscSection, LayoutConstants::Oscillator::WAVE_SELECT);
    scaleAndSet(waveDisplay, LayoutConstants::Oscillator::WAVE_DISPLAY);
    scaleAndSet(octKnob, LayoutConstants::Oscillator::OCT_KNOB);
    scaleAndSet(fineKnob, LayoutConstants::Oscillator::FINE_KNOB);
    scaleAndSet(pitchKnob, LayoutConstants::Oscillator::PITCH_KNOB);
    scaleAndSet(spreadKnob, LayoutConstants::Oscillator::SPREAD_KNOB);
    scaleAndSet(panKnob, LayoutConstants::Oscillator::PAN_KNOB);
    scaleAndSet(positionKnob, LayoutConstants::Oscillator::POSITION_KNOB);
    scaleAndSet(gainKnob, LayoutConstants::Oscillator::GAIN_KNOB);
}