#pragma once
#include <JuceHeader.h>

// Creamos nuestra propia clase de "diseño" que hereda de la de JUCE
class CustomLookAndFeel : public juce::LookAndFeel_V4
{
public:
    CustomLookAndFeel()
    {
        // Define aquí tu paleta de colores minimalista
        setColour(juce::TabbedComponent::backgroundColourId, juce::Colours::black);
        setColour(juce::TabbedComponent::outlineColourId, juce::Colours::transparentBlack);
    }

    // Esta función es la más importante: dibuja cada botón de pestaña
    void drawTabButton(juce::TabBarButton& button, juce::Graphics& g, bool isMouseOver, bool isMouseDown) override
    {
        const auto area = button.getLocalBounds();
        const auto text = button.getButtonText();

        // Si la pestaña está seleccionada
        if (button.isFrontTab())
        {
            // Dibujamos solo una línea inferior para indicar la selección
            g.setColour(juce::Colour::fromRGB(80, 101, 135)); // Azul sutil
            g.fillRect(area.withHeight(3).withY(area.getHeight() - 3));
            
            // Dibujamos el texto en un color brillante
            g.setColour(juce::Colours::white);
        }
        else // Si la pestaña no está seleccionada
        {
            // Dibujamos el texto en un color más apagado
            g.setColour(juce::Colours::grey);
        }

        // Dibuja el texto centrado
        g.setFont(16.0f); // Puedes ajustar el tamaño de la fuente
        g.drawText(text, area, juce::Justification::centred);
    }

    // Esta función define la forma del área de la pestaña. La hacemos un rectángulo simple.
    void createTabButtonShape(juce::TabBarButton&, juce::Path& p, bool, bool) override
    {
        // Simplemente no hacemos nada para que la forma sea rectangular por defecto
        // y no tenga los bordes redondeados del estilo genérico.
    }
    
    int getTabButtonBestWidth(juce::TabBarButton& button, int tabDepth) override
    {
        return juce::LookAndFeel_V2::getTabButtonBestWidth(button, tabDepth) + 24;
    }
};