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
    const int DESIGN_WIDTH = 2340;
    const int DESIGN_HEIGHT = 1360; // Altura total con el teclado
    const int KEYBOARD_HEIGHT = 120; // Altura del teclado en el diseño original
    
    // --- Tamaños de Componentes (según tus medidas de Photoshop) ---
    const juce::Point<float> KNOB_LARGE = { 100.0f, 101.0f };
    const juce::Point<float> KNOB_MEDIUM = { 75.0f, 75.0f };
    const juce::Point<float> KNOB_SMALL = { 47.0f, 47.0f };
    const juce::Point<float> BUTTON = { 83.0f, 30.0f };

    // --- Posiciones de las Secciones Principales ---
    static const juce::Rectangle<float> PROMPT_SECTION{ 370.0f, 20.0f, 510.0f, 45.0f };
    const juce::Rectangle<float> MASTER_SECTION = { 68.0f, 159.0f, 580.0f, 272.0f };
    const juce::Rectangle<float> REVERB_SECTION = { 68.0f, 550.0f, 580.0f, 242.0f };
    const juce::Rectangle<float> DELAY_SECTION = { 68.0f, 909.0f, 580.0f, 290.0f };
    
    const juce::Rectangle<float> UNISON_1_SECTION = { 729.0f, 120.0f, 270.0f, 345.0f };
    const juce::Rectangle<float> UNISON_2_SECTION = { 729.0f, 488.0f, 270.0f, 340.0f };
    const juce::Rectangle<float> UNISON_3_SECTION = { 729.0f, 855.0f, 270.0f, 347.0f };

    const juce::Rectangle<float> OSC_1_SECTION = { 994.0f, 120.0f, 685.0f, 345.0f };
    const juce::Rectangle<float> OSC_2_SECTION = { 994.0f, 488.0f, 685.0f, 340.0f };
    const juce::Rectangle<float> OSC_3_SECTION = { 994.0f, 855.0f, 685.0f, 347.0f };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<float> FILTER_SECTION = { 1765.0f, 158.0f, 520.0f, 272.0f };
    const juce::Rectangle<float> LFO_FM_SECTION = { 1765.0f, 552.0f, 520.0f, 200.0f };
    const juce::Rectangle<float> ENVELOPE_SECTION = { 1765.0f, 871.0f, 520.0f, 340.0f };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<float> MASTER_GAIN_KNOB = { 88.3777f, 74.0f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> GLIDE_KNOB = { 239.021f, 40.1717f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DRIVE_KNOB = { 377.614f, 40.1717f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DARK_KNOB = { 239.021f, 135.0f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> BRIGHT_KNOB = { 377.614f, 134.575f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> CHORUS_BUTTON = { 482.06f, 112.481f, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<float> DRY_KNOB = { 114.489f, 38.1631f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> WET_KNOB = { 257.099f, 38.1631f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SIZE_KNOB = { 399.708f, 38.1631f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> PRE_DELAY_KNOB = { 44.1888f, 128.549f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DIFFUSION_KNOB = { 186.798f, 128.549f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DAMP_KNOB = { 327.399f, 130.558f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DECAY_KNOB = { 472.017f, 128.549f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<float> DRY_KNOB = { 26.1116f, 48.206f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> CENTER_VOL_KNOB = { 138.592f, 48.206f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SIDE_VOL_KNOB = { 251.073f, 48.206f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> HP_KNOB = { 363.554f, 48.206f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> LP_KNOB = { 476.034f, 48.206f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> LEFT_KNOB = { 28.1202f, 170.73f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> CENTER_KNOB = { 138.592f, 170.73f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> RIGHT_KNOB = { 253.082f, 170.73f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> WOW_KNOB = { 363.554f, 170.73f, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<float> FEEDBACK_KNOB = { 476.034f, 170.73f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<float> WAVE_SELECT = { 25.0f, 65.0f, 372.0f, 55.0f };
        const juce::Rectangle<float> WAVE_DISPLAY = { 20.0858f, 150.644f, 380.0f, 152.0f };
        const juce::Rectangle<float> OCT_KNOB = { 992.24f, 60.2575f, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<float> FINE_KNOB = { 530.266f, 42.1803f, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<float> PITCH_KNOB = { 592.532f, 24.103f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SPREAD_KNOB = { 482.06f, 114.489f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> PAN_KNOB = { 592.532f, 116.498f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> POSITION_KNOB = { 482.06f, 232.996f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> GAIN_KNOB = { 592.532f, 232.996f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<float> CUTOFF_KNOB = { 32.1373f, 24.103f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> RES_KNOB = { 196.841f, 24.103f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> ENV_KNOB = { 361.545f, 24.103f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> KEY_BUTTON = { 206.884f, 210.901f, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<float> LFO_SPEED_KNOB = { 34.1459f, 16.0687f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> LFO_AMOUNT_KNOB = { 198.85f, 16.0687f, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<float> FM_KNOB = { 363.554f, 18.0773f, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<float> DISPLAY = { 42.1803f, 14.0601f, 430.0f, 166.712f };
        const juce::Rectangle<float> ATTACK_KNOB = { 46.1974f, 188.807f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> DECAY_KNOB = { 156.67f, 188.807f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> SUSTAIN_KNOB = { 267.142f, 188.807f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<float> RELEASE_KNOB = { 377.614f, 188.807f, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Unison
    {
        // Coordenadas relativas al área del Unison
        const juce::Rectangle<float> VOICES_SLIDER = { 29.0f, 90.0f, 50.0f, 40.0f };
        const juce::Rectangle<float> BALANCE_SLIDER = { 106.0f, 90.0f,  65.0f, 40.0f };
        const juce::Rectangle<float> DETUNE_SLIDER = { 190.0f, 90.0f,  74.0f, 40.0f };
        const juce::Rectangle<float> VISUALIZER = { 27.0f, 160.0f, 230.0f, 150.0f };
    }

}