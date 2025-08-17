#include "ModulationComponent.h"
#include "BinaryData.h"

ModulationComponent::ModulationComponent(NeuraSynthAudioProcessor& p) : audioProcessor(p),
    // Inicializamos el knob de FM. El 0.5 asegura que su valor por defecto sea el centro.
    fmKnob(BinaryData::knobfm_png, BinaryData::knobfm_pngSize, 300.0f, 0.5)
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

    // Aquí iría la configuración de los knobs de LFO más adelante.
}

ModulationComponent::~ModulationComponent() {}

void ModulationComponent::paint(juce::Graphics& g)
{
    // Puedes dibujar un fondo o texto para esta sección si lo necesitas.
}

void ModulationComponent::resized()
{
    // Posicionamos el knob de FM dentro de este componente.
    // Usaremos coordenadas relativas. El knob de la derecha.
    fmKnob.setBounds(188, 5, 100, 100);
    
    // Aquí posicionarías los knobs de LFO, por ejemplo:
    // lfoSpeedKnob.setBounds(0, 0, 100, 100);
    // lfoAmountKnob.setBounds(62, 0, 100, 100);
}