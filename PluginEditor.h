#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "CustomKnob.h"
#include "EnvelopeDisplay.h"
#include "OscillatorComponent.h"
#include "ModulationComponent.h"
#include "MasterSectionComponent.h"
#include "ReverbComponent.h"
#include "DelayComponent.h"
#include "UnisonComponent.h"
#include "FilterComponent.h"
#include "EnvelopeComponent.h"

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
    juce::ComboBox sizeComboBox;
    juce::Label sizeLabel;

    // --- Componentes de Oscilador ---
    OscillatorComponent osc1;
    OscillatorComponent osc2;
    OscillatorComponent osc3;

    // --- Componentes de Unison ---
    UnisonComponent unisonComp1;
    UnisonComponent unisonComp2;
    UnisonComponent unisonComp3;

    ModulationComponent modulationComp;
    MasterSectionComponent masterSection;
    ReverbComponent reverbSection;
    DelayComponent delaySection;
    FilterComponent filterSection;
    EnvelopeComponent envelopeSection;

    juce::MidiKeyboardComponent midiKeyboardComponent{ audioProcessor.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard };

    int keyboardHeight = 80;

    juce::ComponentDragger componentDragger;

    class DesignMouseListener : public juce::MouseListener
    {
    public:
        DesignMouseListener(juce::ComponentDragger& drag, NeuraSynthAudioProcessorEditor* ownerEditor)
            : componentDragger(drag), owner(ownerEditor)
        {
        }

        void mouseDown(const juce::MouseEvent& event) override
        {
            // Le decimos al dragger qué componente empezar a mover
            if (auto* componentToDrag = getDraggableComponentFrom(event))
                componentDragger.startDraggingComponent(componentToDrag, event);
        }

        void mouseDrag(const juce::MouseEvent& event) override
        {
            // Le decimos explícitamente qué componente arrastrar.
            // Esto es más compatible con todas las versiones de JUCE.
            componentDragger.dragComponent(getDraggableComponentFrom(event), event, nullptr);
        }

        void mouseUp(const juce::MouseEvent& event) override
        {
            // Reportamos la posición del componente que se movió
            if (auto* componentToReport = getDraggableComponentFrom(event))
            {
                auto bounds = componentToReport->getBounds();

                // "Des-escalamos" los valores para obtener las coordenadas de diseño
                float unscaledX = bounds.getX() / owner->scale;
                float unscaledY = bounds.getY() / owner->scale;
                float unscaledWidth = bounds.getWidth() / owner->scale;
                float unscaledHeight = bounds.getHeight() / owner->scale;

                DBG(componentToReport->getName() + " DESIGN bounds: "
                    + juce::String(unscaledX, 0) + ", "
                    + juce::String(unscaledY, 0) + ", "
                    + juce::String(unscaledWidth, 0) + ", "
                    + juce::String(unscaledHeight, 0));
            }
        }
    private:
        // --- FUNCIÓN AUXILIAR CORREGIDA ---
        // Ahora detecta si la tecla SHIFT está presionada
        juce::Component* getDraggableComponentFrom(const juce::MouseEvent& event)
            {
                auto* clickedComponent = event.eventComponent;
                if (clickedComponent == nullptr)
                    return nullptr;
  
                // SI SHIFT ESTÁ PRESIONADO, SELECCIONAMOS EL COMPONENTE INDIVIDUAL
                if (event.mods.isShiftDown())
                {
                    return clickedComponent;
                }
    
                // SI NO, buscamos el contenedor de la sección
                if (auto* parent = clickedComponent->findParentComponentOfClass<MasterSectionComponent>()) return parent;
                if (auto* parent = clickedComponent->findParentComponentOfClass<ReverbComponent>())      return parent;
                if (auto* parent = clickedComponent->findParentComponentOfClass<DelayComponent>())       return parent;
                if (auto* parent = clickedComponent->findParentComponentOfClass<UnisonComponent>())      return parent; // <-- ¡AQUÍ ESTÁ LA LÍNEA!
                if (auto* parent = clickedComponent->findParentComponentOfClass<OscillatorComponent>())  return parent;
                if (auto* parent = clickedComponent->findParentComponentOfClass<FilterComponent>())      return parent;
                if (auto* parent = clickedComponent->findParentComponentOfClass<ModulationComponent>())  return parent;
                if (auto* parent = clickedComponent->findParentComponentOfClass<EnvelopeComponent>())    return parent;

                return clickedComponent;
            }

        juce::ComponentDragger& componentDragger;
        NeuraSynthAudioProcessorEditor* owner;
    };

    DesignMouseListener designMouseListener;

public:
    bool designMode = true;
    // Factor de escala para la UI
    float scale = 1.0f;

private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NeuraSynthAudioProcessorEditor)
};