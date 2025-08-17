#include "OscillatorComponent.h"
#include "BinaryData.h"

OscillatorComponent::OscillatorComponent() :
    spreadKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.0),   // Izquierda (como estaba)
    octKnob(BinaryData::knoboct_png, BinaryData::knoboct_pngSize, 300.0f, 0.5),      // En medio
    fineKnob(BinaryData::knoboct_png, BinaryData::knoboct_pngSize, 300.0f, 0.5),     // En medio
    pitchKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),    // En medio
    detuneKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),   // Izquierda (como estaba)
    panKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5),      // En medio (L/R)
    positionKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.0), // Izquierda (como estaba)
    gainKnob(BinaryData::knobosc_png, BinaryData::knobosc_pngSize, 300.0f, 0.5)      // En medio (50%)
{
    addAndMakeVisible(oscSection);
    addAndMakeVisible(waveDisplay);
    addAndMakeVisible(octKnob);
    addAndMakeVisible(fineKnob);
    addAndMakeVisible(pitchKnob);
    addAndMakeVisible(detuneKnob);
    addAndMakeVisible(spreadKnob);
    addAndMakeVisible(panKnob);
    addAndMakeVisible(positionKnob);
    addAndMakeVisible(gainKnob);
}

OscillatorComponent::~OscillatorComponent() {}

void OscillatorComponent::paint(juce::Graphics& g) {}

void OscillatorComponent::resized()
{
    // Las coordenadas son relativas al a de este componente.
    const int knobSize = 55;
    const int margin = 5;

    // --- Columna Izquierda (Waveform y Selector) ---
    oscSection.setBounds(23, 38, 150, 22);
    waveDisplay.setBounds(23, 71, 195, 98);

    // --- Columna Central (Octave y Fine) ---
    // Estos son los knobs negros ms pequeos.
    const int smallKnobSize = 45;
    spreadKnob.setBounds(174, 16, knobSize, knobSize);
    octKnob.setBounds(219, 20, smallKnobSize, smallKnobSize);
    fineKnob.setBounds(257, 20, smallKnobSize, smallKnobSize);

    // --- Columna Derecha (Grid de knobs rojos) ---
    // Fila Superior
    pitchKnob.setBounds(293, 13, knobSize, knobSize);
    detuneKnob.setBounds(232, 66, knobSize, knobSize);
    panKnob.setBounds(293, 66, knobSize, knobSize);

    // Fila Inferior
    positionKnob.setBounds(231, 124, knobSize, knobSize);
    gainKnob.setBounds(292, 126, knobSize, knobSize);
}