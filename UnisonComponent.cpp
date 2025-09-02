// UnisonComponent.cpp
#include "UnisonComponent.h"
 
UnisonComponent::UnisonComponent()
{
    // --- Configuración del ComboBox de Voces ---
    addAndMakeVisible(voiceCountBox);
    for (int i = 1; i <= 16; ++i)
        voiceCountBox.addItem(juce::String(i), i);

    voiceCountBox.setSelectedId(1, juce::dontSendNotification);
    voiceCountBox.onChange = [this]
    {
        if (onVoicesChanged)
            onVoicesChanged(voiceCountBox.getSelectedId());
    };

    // --- Configuración del Slider de Detune ---
    addAndMakeVisible(detuneAmountSlider);
    detuneAmountSlider.setSliderStyle(juce::Slider::LinearHorizontal);
    detuneAmountSlider.setTextBoxStyle(juce::Slider::TextBoxRight, false, 50, 20);
    detuneAmountSlider.setRange(0.0, 1.0, 0.01);
    detuneAmountSlider.setValue(0.2, juce::dontSendNotification);

    detuneAmountSlider.onValueChange = [this]
    {
        if (onDetuneChanged)
            onDetuneChanged(detuneAmountSlider.getValue());
    };

    // --- Configuración del Slider de Balance ---
    addAndMakeVisible(detuneBalanceSlider);
    detuneBalanceSlider.setSliderStyle(juce::Slider::LinearHorizontal);
    detuneBalanceSlider.setTextBoxStyle(juce::Slider::TextBoxRight, false, 50, 20);
    detuneBalanceSlider.setRange(-1.0, 1.0, 0.01);
    detuneBalanceSlider.setValue(0.0, juce::dontSendNotification);
    detuneBalanceSlider.onValueChange = [this]
    {
        if (onBalanceChanged)
            onBalanceChanged(detuneBalanceSlider.getValue());
    };

    // --- Etiquetas ---
    addAndMakeVisible(voicesLabel);
    voicesLabel.setText("Voices", juce::dontSendNotification);
    voicesLabel.setJustificationType(juce::Justification::centred);

    addAndMakeVisible(detuneLabel);
    detuneLabel.setText("Detune", juce::dontSendNotification);
    detuneLabel.setJustificationType(juce::Justification::centred);

    addAndMakeVisible(balanceLabel);
    balanceLabel.setText("Balance", juce::dontSendNotification);
    balanceLabel.setJustificationType(juce::Justification::centred);
}

UnisonComponent::~UnisonComponent() {}

void UnisonComponent::resized()
{
    auto bounds = getLocalBounds();
    
    const int controlWidth = bounds.getWidth() / 3;
    
    // Área para "Voices"
    auto voicesArea = bounds.removeFromLeft(controlWidth).reduced(2);
    voicesLabel.setBounds(voicesArea.removeFromTop(15));
    voiceCountBox.setBounds(voicesArea);
    
    // Área para "Balance"
    auto balanceArea = bounds.removeFromLeft(controlWidth).reduced(2);
    balanceLabel.setBounds(balanceArea.removeFromTop(15));
    detuneBalanceSlider.setBounds(balanceArea);

    // Área para "Detune"
    auto detuneArea = bounds.reduced(2);
    detuneLabel.setBounds(detuneArea.removeFromTop(15));
    detuneAmountSlider.setBounds(detuneArea);
}

void UnisonComponent::mouseWheelMove(const juce::MouseEvent& event, const juce::MouseWheelDetails& wheel)
{
    // Comprobamos sobre qué componente se hizo el scroll
    if (voiceCountBox.isMouseOver())
    {
        int currentId = voiceCountBox.getSelectedId();
        int newId = currentId + (wheel.deltaY > 0 ? 1 : -1);
        newId = juce::jlimit(1, 16, newId);
        voiceCountBox.setSelectedId(newId);
    }
    else if (detuneAmountSlider.isMouseOver())
    {
        double currentValue = detuneAmountSlider.getValue();
        double newValue = currentValue + (wheel.deltaY > 0 ? 0.05 : -0.05);
        detuneAmountSlider.setValue(newValue, juce::sendNotificationSync);
    }
    else if (detuneBalanceSlider.isMouseOver())
    {
        double currentValue = detuneBalanceSlider.getValue();
        double newValue = currentValue + (wheel.deltaY > 0 ? 0.05 : -0.05);
        detuneBalanceSlider.setValue(newValue, juce::sendNotificationSync);
    }
    else
    {
           // Si no está sobre ninguno en particular, que no haga nada
           Component::mouseWheelMove(event, wheel);
    }
}