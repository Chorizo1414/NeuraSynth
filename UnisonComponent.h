// UnisonComponent.h
#pragma once

#include <JuceHeader.h>
 
class UnisonComponent : public juce::Component
{
public:
    UnisonComponent();
    ~UnisonComponent() override;

    void resized() override;

    // Callbacks para notificar al exterior cuando un valor cambia
    std::function<void(int)> onVoicesChanged;
    std::function<void(float)> onDetuneChanged;
    std::function<void(float)> onBalanceChanged;

    void mouseWheelMove(const juce::MouseEvent& event, const juce::MouseWheelDetails& wheel) override;

private:
    juce::ComboBox voiceCountBox;
    juce::Slider detuneAmountSlider;
    juce::Slider detuneBalanceSlider;

    juce::Label voicesLabel;    
    juce::Label detuneLabel;
    juce::Label balanceLabel;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(UnisonComponent)
};
