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

namespace pybind11 { class dict; }

class SynthTabComponent : public juce::Component, public juce::TextEditor::Listener
{
public:
    SynthTabComponent(NeuraSynthAudioProcessor& p);
    ~SynthTabComponent() override;

    void paint(juce::Graphics&) override;
    void resized() override;

    void textEditorReturnKeyPressed(juce::TextEditor& editor) override;
    void applyPatchFromPython(const pybind11::dict& patchData);

private:
    NeuraSynthAudioProcessor& audioProcessor;
    juce::Image backgroundImage;
    juce::Rectangle<int> guiArea;

    // --- Componentes de UI (sin cambios) ---
    OscillatorComponent osc1, osc2, osc3;
    UnisonComponent unisonComp1, unisonComp2, unisonComp3;
    MasterSectionComponent masterSection;
    ReverbComponent reverbSection;
    DelayComponent delaySection;
    FilterComponent filterSection;
    EnvelopeComponent envelopeSection;
    ModulationComponent modulationComp;
    juce::File wavetableDirectory;
    juce::TextEditor soundPromptEditor;
    juce::Label soundPromptLabel;
    juce::TextButton generateButton, undoButton, redoButton, likeButton, dislikeButton;
    juce::Label presetLabel;
    juce::ComboBox presetSelector;
    juce::TextButton refreshPresetsButton;
    juce::MidiKeyboardComponent keyboardComponent;
    juce::TextButton soundTypesHelpButton;

    // --- Miembros privados (sin cambios) ---
    void populatePresets();
    pybind11::dict currentPresets;
    void undoButtonClicked();
    void redoButtonClicked();
    void updateUndoRedoButtonStates();
    void addToHistory(const pybind11::dict& newPatch);
    void refreshWaveDisplaysFromProcessor();
    std::vector<pybind11::dict> patchHistory;
    int currentHistoryIndex = -1;

    juce::ComponentDragger componentDragger;

    // ==============================================================================
    // INICIO DE LA SECCIÓN CORREGIDA
    // ==============================================================================
    class DesignMouseListener : public juce::MouseListener
    {
    public:
        DesignMouseListener(juce::ComponentDragger& drag, SynthTabComponent* ownerComponent)
            : componentDragger(drag), owner(ownerComponent) {
        }

        void mouseDown(const juce::MouseEvent& event) override
        {
            if (owner->designMode)
                if (auto* c = getDraggableComponentFrom(event))
                    componentDragger.startDraggingComponent(c, event);
        }

        void mouseDrag(const juce::MouseEvent& event) override
        {
            if (owner->designMode)
                if (auto* c = getDraggableComponentFrom(event))
                    componentDragger.dragComponent(c, event, nullptr);
        }

        void mouseUp(const juce::MouseEvent& event) override
        {
            if (owner->designMode)
            {
                if (auto* c = getDraggableComponentFrom(event))
                {
                    auto bounds = c->getBounds().toFloat();
                    const float invScale = 1.0f / owner->scale;
                    float designX, designY;

                    // --- ESTA ES LA LÓGICA CORREGIDA ---
                    if (event.mods.isShiftDown())
                    {
                        // MODO SHIFT: Se movió un knob DENTRO de una sección.
                        // Sus coordenadas son relativas a su padre (la sección),
                        // por lo que solo necesitamos des-escalarlas.
                        designX = bounds.getX() * invScale;
                        designY = bounds.getY() * invScale;
                    }
                    else
                    {
                        // MODO NORMAL: Se movió una sección entera.
                        // Sus coordenadas son relativas a la ventana, por lo que
                        // necesitamos revertir la transformación completa.
                        designX = bounds.getX() * invScale;
                        designY = (bounds.getY() - owner->guiArea.getY() - owner->offsetFactor) * invScale;
                    }

                    // El ancho y el alto siempre se des-escalan de la misma manera.
                    const float designWidth = bounds.getWidth() * invScale;
                    const float designHeight = bounds.getHeight() * invScale;

                    // Imprimimos el resultado correcto en la consola.
                    DBG(juce::String(c->getName()) + " = { " +
                        juce::String(designX) + "f, " +
                        juce::String(designY) + "f, " +
                        juce::String(designWidth) + "f, " +
                        juce::String(designHeight) + "f };");
                }
            }
        }
    private:
        // Esta función ya estaba correcta, la mantenemos.
        juce::Component* getDraggableComponentFrom(const juce::MouseEvent& event)
        {
            auto* clickedComponent = event.eventComponent;
            if (clickedComponent == nullptr) return nullptr;

            if (event.mods.isShiftDown())
            {
                return clickedComponent;
            }

            if (auto* parent = clickedComponent->findParentComponentOfClass<MasterSectionComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<ReverbComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<DelayComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<UnisonComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<OscillatorComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<FilterComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<ModulationComponent>()) return parent;
            if (auto* parent = clickedComponent->findParentComponentOfClass<EnvelopeComponent>()) return parent;

            return clickedComponent;
        }

        juce::ComponentDragger& componentDragger;
        SynthTabComponent* owner;
    };

    DesignMouseListener designMouseListener;

public:
    bool designMode = false;
    float scale = 1.0f;
    float offsetFactor = 0.0f; // Necesario para la corrección

private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SynthTabComponent);
};