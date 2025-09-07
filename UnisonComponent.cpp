// UnisonComponent.cpp
#include "UnisonComponent.h"
#include "LayoutConstants.h"
#include "PluginEditor.h"

// --- Implementación del Visualizador ---
void UnisonComponent::UnisonVisualizer::paint(juce::Graphics & g)
{
   g.fillAll(juce::Colours::black.withAlpha(0.5f));
   g.setColour(juce::Colours::white.withAlpha(0.7f));
   g.drawRect(getLocalBounds(), 1.0f);
    
   if (voices <= 0) return;
    
   const float barWidth = 2.0f;
   const float maxSpread = getWidth() * 0.8f; // Las barras ocuparán hasta el 80% del ancho
    
   g.setColour(juce::Colours::deepskyblue);
    
   for (int i = 0; i < voices; ++i)
   {
        float voicePosition = 0.0f;
        if (voices > 1)
            voicePosition = juce::jmap((float)i, 0.0f, (float)voices - 1.0f, -1.0f, 1.0f);
        
        float horizontalOffset = voicePosition * detune * (maxSpread / 2.0f);
        float x = (float)getWidth() / 2.0f + horizontalOffset - (barWidth / 2.0f);
        
        juce::Rectangle<float> bar(x, 2.0f, barWidth, (float)getHeight() - 4.0f);
        g.fillRect(bar);
   }
}

void UnisonComponent::UnisonVisualizer::setUnisonData(int numVoices, float detuneAmount)
{
   voices = numVoices;
   detune = detuneAmount;
   repaint();
}

UnisonComponent::UnisonComponent()
{
    // --- Voces ---
    addAndMakeVisible(voicesControl);
    voicesControl.setRange(1, 16, 1);
    voicesControl.setValue(1.0);
    voicesControl.onValueChange = [this](double newValue) {
        if (onVoicesChanged)
            onVoicesChanged(static_cast<int>(newValue));
        visualizer.setUnisonData(static_cast<int>(newValue), detuneControl.getValue() / 100.0);
        };

    // --- Balance ---
    addAndMakeVisible(balanceControl);
    balanceControl.setRange(-1.0, 1.0, 0.01);
    balanceControl.setValue(0.0);
    balanceControl.onValueChange = [this](double newValue) {
        if (onBalanceChanged)
            onBalanceChanged(newValue);
        };

    // --- Detune ---
    addAndMakeVisible(detuneControl);
    detuneControl.setRange(0, 100, 1); // Rango de 0 a 100%
    detuneControl.setValue(20.0);
    detuneControl.onValueChange = [this](double newValue) {
        if (onDetuneChanged)
            onDetuneChanged(newValue / 100.0); // Convertir de 0-100 a 0-1 para el procesador
        visualizer.setUnisonData(voicesControl.getValue(), newValue / 100.0);
        };

    voicesControl.setName("Unison Voices");
    balanceControl.setName("Unison Balance");
    detuneControl.setName("Unison Detune");
    visualizer.setName("Unison Visualizer");

    // --- Etiquetas ---
    addAndMakeVisible(voicesLabel);
    voicesLabel.setJustificationType(juce::Justification::centred);

    addAndMakeVisible(detuneLabel);
    detuneLabel.setJustificationType(juce::Justification::centred);

    addAndMakeVisible(balanceLabel);
    balanceLabel.setJustificationType(juce::Justification::centred);

    // --- Visualizador ---
    addAndMakeVisible(visualizer);
    // Actualización inicial
    visualizer.setUnisonData(voicesControl.getValue(), detuneControl.getValue() / 100.0);
}

UnisonComponent::~UnisonComponent() {}

void UnisonComponent::paint(juce::Graphics& g)
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

void UnisonComponent::resized()
{
    // Ahora que Unison es una sección principal, su layout es simple.
    // OBTENEMOS LAS DIMENSIONES DE DISEÑO DIRECTAMENTE DE UNISON_1_SECTION (usamos la 1 como referencia para todas)
    const auto& designBounds = LayoutConstants::UNISON_1_SECTION;

    // Calculamos la escala local basándonos en nuestro propio tamaño de diseño
    float scaleX = (float)getWidth() / designBounds.getWidth();
    float scaleY = (float)getHeight() / designBounds.getHeight();

    // Función auxiliar simple
    auto scaleAndSet = [&](juce::Component& comp, const juce::Rectangle<int>& designRect)
    {
        comp.setBounds(designRect.getX() * scaleX,
                       designRect.getY() * scaleY,
                       designRect.getWidth() * scaleX,
                       designRect.getHeight() * scaleY);
    };

    // Posicionamos los controles usando el plano de namespace Unison
    scaleAndSet(voicesControl,  LayoutConstants::Unison::VOICES_SLIDER);
    scaleAndSet(balanceControl, LayoutConstants::Unison::BALANCE_SLIDER);
    scaleAndSet(detuneControl,  LayoutConstants::Unison::DETUNE_SLIDER);
    scaleAndSet(visualizer,     LayoutConstants::Unison::VISUALIZER);
}