// UnisonComponent.h
#pragma once

#include <JuceHeader.h>
#include "TextValueSlider.h"

class UnisonComponent : public juce::Component
{
public:
    UnisonComponent();
    ~UnisonComponent() override;

    void paint(juce::Graphics& g) override;
    void resized() override;

    // Callbacks para notificar al exterior cuando un valor cambia
    std::function<void(int)> onVoicesChanged;
    std::function<void(float)> onDetuneChanged;
    std::function<void(float)> onBalanceChanged;


private:

    // --- Sub-componente para el visualizador de barras ---
    class UnisonVisualizer : public juce::Component
        {
    public:
        void paint(juce::Graphics & g) override;
        void setUnisonData(int numVoices, float detuneAmount);
        
    private:
        int voices = 1;
        float detune = 0.2f;
        };

    TextValueSlider voicesControl{ "Voces" };
    TextValueSlider balanceControl{ "Balance" };
    TextValueSlider detuneControl{ "Detune", "%" };

    UnisonVisualizer visualizer;

    juce::Label voicesLabel{ "Voices", "Voices" };
    juce::Label balanceLabel{ "Balance", "Balance" };
    juce::Label detuneLabel{ "Detune", "Detune" };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(UnisonComponent)
};
