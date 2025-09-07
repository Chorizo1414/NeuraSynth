#include "ModulationComponent.h"
#include "BinaryData.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

ModulationComponent::ModulationComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
    // Inicializamos el knob de FM. El 0.5 asegura que su valor por defecto sea el centro.
    fmKnob(BinaryData::knobfm_png, BinaryData::knobfm_pngSize, 300.0f, 0.5),
    lfoSpeedKnob(BinaryData::knoblfo_png, BinaryData::knoblfo_pngSize, 300.0f, 0.0),
    lfoAmountKnob(BinaryData::knoblfo_png, BinaryData::knoblfo_pngSize, 300.0f, 0.0)
{
    // --- Configuración del Knob de FM ---
    addAndMakeVisible(fmKnob);
    // Rango bipolar: -1.0 (izquierda) a 1.0 (derecha), con 0.0 en el centro.
    fmKnob.setRange(-1.0, 1.0);

    // Conectamos el cambio de valor del knob a una función en el procesador de audio.
    fmKnob.onValueChange = [this]()
    {
        audioProcessor.setFMAmount(fmKnob.getValue()); 
    };
    
    // <<< INICIAL >>>: el knob empieza en el centro (0.0) y se lo comunicamos al DSP.
    fmKnob.setValue(0.0, juce::sendNotificationSync);

    // --- Configuración del Knob LFO Speed ---
    addAndMakeVisible(lfoSpeedKnob);
    lfoSpeedKnob.setRange(0.1, 8.0); // Rango de velocidad en Hz (de muy lento a rápido)
    lfoSpeedKnob.setSkewFactorFromMidPoint(4.0);
    lfoSpeedKnob.onValueChange = [this]() { audioProcessor.setLfoSpeed(lfoSpeedKnob.getValue()); };
    lfoSpeedKnob.setValue(0.1, juce::sendNotificationSync);

    // --- Configuración del Knob LFO Amount ---
    addAndMakeVisible(lfoAmountKnob);
    lfoAmountKnob.setRange(0.0, 1.0); // Rango normalizado para la cantidad
    lfoAmountKnob.onValueChange = [this]() { audioProcessor.setLfoAmount(lfoAmountKnob.getValue()); };
    lfoAmountKnob.setValue(0.0, juce::sendNotificationSync);
}

ModulationComponent::~ModulationComponent() {}

void ModulationComponent::paint(juce::Graphics& g)
{
    // Solo dibuja el borde si el designMode del editor está activo
    if (auto* editor = findParentComponentOfClass<NeuraSynthAudioProcessorEditor>())
    {
        if (editor->designMode)
        {
            g.setColour(juce::Colours::red);
            g.drawRect(getLocalBounds(), 2.0f);
        }
    }
}

void ModulationComponent::resized()
{
    const auto& designBounds = LayoutConstants::LFO_FM_SECTION;
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect) {
        comp.setBounds(designRect.getX() * scaleX, designRect.getY() * scaleY, designRect.getWidth() * scaleX, designRect.getHeight() * scaleY);
    };

    scaleAndSet(lfoSpeedKnob, LayoutConstants::LFO_FM::LFO_SPEED_KNOB);
    scaleAndSet(lfoAmountKnob, LayoutConstants::LFO_FM::LFO_AMOUNT_KNOB);
    scaleAndSet(fmKnob, LayoutConstants::LFO_FM::FM_KNOB);
}