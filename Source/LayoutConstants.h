#pragma once
#include <JuceHeader.h>

// ====================================================================================
// PLANO DE DISEÑO DE NEURASYNTH
// Todas las coordenadas y tamaños se basan en el diseño original de 2048x1360px.
// Si necesitas ajustar la posición de un knob, ¡SOLO TIENES QUE EDITARLO AQUÍ!
// ====================================================================================
namespace LayoutConstants
{
    // --- Dimensiones Globales del Diseño ---
    const int TAB_BAR_HEIGHT = 60; 
    const int DESIGN_WIDTH = 2340;    // El ancho de tu imagen de fondo
    const int DESIGN_SYNTH_HEIGHT = 1360;        // La ALTURA DEL ÁREA DEL SINTETIZADOR (imagen del sinte)
    const int KEYBOARD_HEIGHT = 120; // Altura que ocupa el teclado MIDI   
    const int DESIGN_HEIGHT = DESIGN_SYNTH_HEIGHT + KEYBOARD_HEIGHT + 35;// Altura TOTAL de la ventana del plugin, incluyendo la barra de pestañas y el teclado
    
    // --- Tamaños de Componentes (según tus medidas de Photoshop) ---
    const juce::Point<float> KNOB_LARGE = { 96.5f, 96.5f };
    const juce::Point<float> KNOB_MEDIUM = { 71.0f, 71.0f };
    const juce::Point<float> KNOB_SMALL = { 44.0f, 44.0f };
    const juce::Point<float> BUTTON = { 85.0f, 50.0f };

    // --- Posiciones de las Secciones Principales ---
    static const juce::Rectangle<float> PROMPT_SECTION{ 370.0f, 20.0f, 510.0f, 45.0f };
    const juce::Rectangle<float> MASTER_SECTION = { 64.1096f, 240.411f, 580.0f, 272.0f };
    const juce::Rectangle<float> REVERB_SECTION = { 64.1096f, 627.072f, 580.0f, 242.0f };
    const juce::Rectangle<float> DELAY_SECTION = { 64.1096f, 973.664f, 580.0f, 290.0f };
    
    const juce::Rectangle<float> UNISON_1_SECTION = { 723.236f, 200.342f, 270.0f, 345.0f };
    const juce::Rectangle<float> UNISON_2_SECTION = { 723.236f, 560.959f, 270.0f, 345.0f };
    const juce::Rectangle<float> UNISON_3_SECTION = { 723.236f, 921.575f, 270.0f, 347.0f };

    const juce::Rectangle<float> OSC_1_SECTION = { 994.0f, 200.342f, 685.0f, 345.0f };
    const juce::Rectangle<float> OSC_2_SECTION = { 994.0f, 560.959f, 685.0f, 345.0f };
    const juce::Rectangle<float> OSC_3_SECTION = { 994.0f, 921.575f, 685.0f, 347.0f };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<float> FILTER_SECTION = { 1763.01f, 238.408f, 520.0f, 272.0f };
    const juce::Rectangle<float> LFO_FM_SECTION = { 1763.01f, 625.068f, 520.0f, 200.0f };
    const juce::Rectangle<float> ENVELOPE_SECTION = { 1763.01f, 939.606f, 520.0f, 340.0f };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<float> MASTER_GAIN_KNOB = { 93.161f, 76.1301f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> GLIDE_KNOB = { 242.100f, 42.0719f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DRIVE_KNOB = { 382.654f, 42.0719f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DARK_KNOB = { 242.414f, 134.229f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> BRIGHT_KNOB = { 382.654f, 134.229f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> CHORUS_BUTTON = { 484.829f, 100.171f, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<float> DRY_KNOB = { 120.205f, 38.0651f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> WET_KNOB = { 262.449f, 38.0651f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SIZE_KNOB = { 404.692f, 38.0651f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> PRE_DELAY_KNOB = { 50.0856f, 126.216f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DIFFUSION_KNOB = { 190.325f, 126.216f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DAMP_KNOB = { 332.568f, 128.219f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DECAY_KNOB = { 476.815f, 126.216f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<float> DRY_KNOB = { 32.0548f, 54.0925f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> CENTER_VOL_KNOB = { 142.243f, 54.0925f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SIDE_VOL_KNOB = { 256.438f, 54.0925f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> HP_KNOB = { 368.63f, 54.0925f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> LP_KNOB = { 480.822f, 54.0925f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> LEFT_KNOB = { 34.0582f, 174.298f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> CENTER_KNOB = { 144.247f, 174.2983f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> RIGHT_KNOB = { 256.438f, 174.298f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> WOW_KNOB = { 368.63f, 174.298f, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<float> FEEDBACK_KNOB = { 480.822f, 174.298f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<float> WAVE_SELECT = { 21.0f, 68.0f, 372.0f, 55.0f };
        const juce::Rectangle<float> WAVE_DISPLAY = { 18.0308f, 154.264f, 380.0f, 152.0f };
        const juce::Rectangle<float> OCT_KNOB = { 464.795f, 46.0788f, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<float> FINE_KNOB = { 530.266f, 46.0788f, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<float> PITCH_KNOB = { 595.017f, 30.0514f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SPREAD_KNOB = { 484.829f, 120.205f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> PAN_KNOB = { 595.017f, 118.202f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> POSITION_KNOB = { 486.832f, 232.996f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> GAIN_KNOB = { 595.017f, 234.401f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };

        struct Layout
        {
            juce::Rectangle<float> waveSelect;
            juce::Rectangle<float> waveDisplay;
            juce::Rectangle<float> octKnob;
            juce::Rectangle<float> fineKnob;
            juce::Rectangle<float> pitchKnob;
            juce::Rectangle<float> spreadKnob;
            juce::Rectangle<float> panKnob;
            juce::Rectangle<float> positionKnob;
            juce::Rectangle<float> gainKnob;
        };

        inline Layout makeLayout(float offsetX, float offsetY)
        {
            Layout layout;
            layout.waveSelect = WAVE_SELECT.translated(offsetX, offsetY);
            layout.waveDisplay = WAVE_DISPLAY.translated(offsetX, offsetY);
            layout.octKnob = OCT_KNOB.translated(offsetX, offsetY);
            layout.fineKnob = FINE_KNOB.translated(offsetX, offsetY);
            layout.pitchKnob = PITCH_KNOB.translated(offsetX, offsetY);
            layout.spreadKnob = SPREAD_KNOB.translated(offsetX, offsetY);
            layout.panKnob = PAN_KNOB.translated(offsetX, offsetY);
            layout.positionKnob = POSITION_KNOB.translated(offsetX, offsetY);
            layout.gainKnob = GAIN_KNOB.translated(offsetX, offsetY);
            return layout;
        }

        namespace Offsets
        {
            // Ajustes verticales medidos para compensar los desfases de cada bloque de oscilador en el arte
            constexpr float OSC1_Y = 0.0f;
            constexpr float OSC2_Y = 1.0f;
            constexpr float OSC3_Y = 2.0f;
        }

        inline Layout getLayoutForVariant(int variant)
        {
            switch (variant)
            {
            case 2:
                return makeLayout(0.0f, Offsets::OSC2_Y);
            case 3:
                return makeLayout(0.0f, Offsets::OSC3_Y);
            default:
                return makeLayout(0.0f, Offsets::OSC1_Y);
            }
        }
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<float> CUTOFF_KNOB = { 36.0616f, 28.0479f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> RES_KNOB = { 202.346f, 28.0479f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> ENV_KNOB = { 366.627f, 28.0479f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> KEY_BUTTON = { 206.353f, 200.342f, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<float> LFO_SPEED_KNOB = { 38.0651f, 22.0377f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> LFO_AMOUNT_KNOB = { 202.346f, 22.0377f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> FM_KNOB = { 366.627f, 22.0377f, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<float> DISPLAY = { 42.1803f, 14.0601f, 430.0f, 166.712f };
        const juce::Rectangle<float> ATTACK_KNOB = { 50.0856f, 188.322f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DECAY_KNOB = { 160.274f, 188.322f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SUSTAIN_KNOB = { 270.462f, 188.322f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> RELEASE_KNOB = { 380.651f, 188.322f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Unison
    {
        // Coordenadas relativas al área del Unison
        const juce::Rectangle<float> VOICES_SLIDER = { 35.0f, 90.0f, 50.0f, 40.0f };
        const juce::Rectangle<float> BALANCE_SLIDER = { 100.0f, 90.0f, 97.0f, 40.0f };
        const juce::Rectangle<float> DETUNE_SLIDER = { 198.0f, 90.0f, 72.0f, 40.0f };
        const juce::Rectangle<float> VISUALIZER = { 32.0548f, 158.271f, 230.0f, 150.0f };
    }

}