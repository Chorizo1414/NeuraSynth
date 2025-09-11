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

class SynthTabComponent : public juce::Component
{
public:
    SynthTabComponent(NeuraSynthAudioProcessor& p);
    ~SynthTabComponent() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    // Mantenemos la referencia al procesador de audio
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

    juce::MidiKeyboardComponent midiKeyboardComponent;

    // El resto del código que tenías en PluginEditor.h para el modo diseño...
    juce::ComponentDragger componentDragger;

    class DesignMouseListener : public juce::MouseListener
    {
    public:
        DesignMouseListener(juce::ComponentDragger& drag, SynthTabComponent* ownerComponent)
            : componentDragger(drag), owner(ownerComponent)
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
            if (auto* componentToReport = getDraggableComponentFrom(event))
            {
                auto bounds = componentToReport->getBounds();
                float unscaledX = 0.0f;
                float unscaledY = 0.0f;

                // NUEVA LÓGICA: Distinguimos entre mover un knob o una sección.
                if (event.mods.isShiftDown())
                {
                    // MODO SHIFT: Se movió un knob DENTRO de una sección.
                    // Sus coordenadas son relativas al padre, solo necesitamos des-escalar.
                    unscaledX = bounds.getX() / owner->scale;
                    unscaledY = bounds.getY() / owner->scale;
                }
                else
                {
                    // MODO NORMAL: Se movió una sección entera.
                    // Sus coordenadas son relativas a la ventana, necesitamos corregir el desfase.
                    unscaledX = (bounds.getX() - owner->getBounds().getX()) / owner->scale;
                    unscaledY = (bounds.getY() - owner->getBounds().getY()) / owner->scale;
                }

                // El ancho y alto siempre se calculan de la misma forma.
                float unscaledWidth = bounds.getWidth() / owner->scale;
                float unscaledHeight = bounds.getHeight() / owner->scale;

                DBG(componentToReport->getName() + " RELATIVE DESIGN bounds: "
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
        SynthTabComponent* owner;
    };

    DesignMouseListener designMouseListener;

public:
    bool designMode = false;
    float scale = 1.0f;
    juce::Rectangle<float> scaledGuiArea;


private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SynthTabComponent)
};