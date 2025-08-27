#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "CustomKnob.h"
#include "EnvelopeDisplay.h"
#include "OscillatorComponent.h"
#include "ModulationComponent.h"
#include "MasterSectionComponent.h"
#include "ReverbComponent.h"

class NeuraSynthAudioProcessorEditor : public juce::AudioProcessorEditor
{
public:
    NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor&);
    ~NeuraSynthAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void visibilityChanged() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;
    juce::Image backgroundImage;

    // --- Componentes de Oscilador ---
    OscillatorComponent osc1;
    OscillatorComponent osc2;
    OscillatorComponent osc3;

    // --- Resto de Componentes de la UI ---
    CustomKnob filterCutoffKnob;
    CustomKnob filterResonanceKnob;
    CustomKnob filterEnvKnob;
    EnvelopeDisplay envelopeDisplay;

    CustomKnob attackKnob;
    CustomKnob decayKnob;
    CustomKnob sustainKnob;
    CustomKnob releaseKnob;

    ModulationComponent modulationComp;
    MasterSectionComponent masterSection;
    ReverbComponent reverbSection;

    CustomKnob delayDryKnob;
    CustomKnob delayCenterVolKnob;
    CustomKnob delaySideVolKnob;
    CustomKnob delayHPKnob;
    CustomKnob delayLPKnob;
    CustomKnob delayLeftKnob;
    CustomKnob delayCenterKnob;
    CustomKnob delayRightKnob;
    CustomKnob delayWowKnob;
    CustomKnob delayFeedbackKnob;
    juce::ImageButton keyButton;
    juce::MidiKeyboardComponent midiKeyboardComponent{ audioProcessor.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard };

    // --- Modo Diseo ---
    bool designMode = true;
    juce::ComponentDragger componentDragger;

    class DesignMouseListener : public juce::MouseListener
    {
    public:
        DesignMouseListener(juce::ComponentDragger& drag) : componentDragger(drag) {}
        void mouseDrag(const juce::MouseEvent& event) override
        {
            componentDragger.dragComponent(event.eventComponent, event, nullptr);
        }
        void mouseUp(const juce::MouseEvent& event) override
        {
            if (event.eventComponent != nullptr)
                DBG(event.eventComponent->getName() + " new bounds: " + event.eventComponent->getBounds().toString());
        }
    private:
        juce::ComponentDragger& componentDragger;
    };

    DesignMouseListener designMouseListener;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NeuraSynthAudioProcessorEditor)
};