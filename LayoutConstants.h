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
    const int DESIGN_WIDTH = 2048;
    const int DESIGN_HEIGHT = 1360; // Altura total con el teclado
    const int KEYBOARD_HEIGHT = 180; // Altura del teclado en el diseño original
    
    // --- Tamaños de Componentes (según tus medidas de Photoshop) ---
    const juce::Point<int> KNOB_LARGE = { 99, 104 };
    const juce::Point<int> KNOB_MEDIUM = { 71, 74 };
    const juce::Point<int> KNOB_SMALL = { 43, 45 };
    const juce::Point<int> BUTTON = { 52, 20 };

    // --- Posiciones de las Secciones Principales ---
    const juce::Rectangle<int> MASTER_SECTION   = { 40, 100, 580, 270 };
    const juce::Rectangle<int> REVERB_SECTION   = { 40, 490, 580, 270 };
    const juce::Rectangle<int> DELAY_SECTION    = { 40, 847, 580, 270 };
    
    const juce::Rectangle<int> UNISON_1_SECTION = { 670, 40, 230, 340 };
    const juce::Rectangle<int> UNISON_2_SECTION = { 670, 424, 230, 340 };
    const juce::Rectangle<int> UNISON_3_SECTION = { 670, 807, 230, 340 };

    const juce::Rectangle<int> OSC_1_SECTION    = { 850, 40, 600, 340 };
    const juce::Rectangle<int> OSC_2_SECTION    = { 850, 424, 600, 340 };
    const juce::Rectangle<int> OSC_3_SECTION    = { 850, 807, 600, 340 };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<int> FILTER_SECTION   = { 1508, 68, 500, 245 };
    const juce::Rectangle<int> LFO_FM_SECTION   = { 1510, 412, 500, 200 };
    const juce::Rectangle<int> ENVELOPE_SECTION = { 1510, 713, 500, 460 };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<int> MASTER_GAIN_KNOB = { 92, 52, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> GLIDE_KNOB       = { 238, 24, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DRIVE_KNOB       = { 380, 24, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DARK_KNOB        = { 238, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> BRIGHT_KNOB      = { 380, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CHORUS_BUTTON    = { 496, 96, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<int> DRY_KNOB = { 122, 22, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WET_KNOB = { 264, 22, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIZE_KNOB = { 406, 22, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PRE_DELAY_KNOB = { 52, 114, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DIFFUSION_KNOB = { 194, 114, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DAMP_KNOB = { 336, 114, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 476, 114, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<int> DRY_KNOB = { 28, 56, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_VOL_KNOB = { 140, 56, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIDE_VOL_KNOB = { 252, 56, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> HP_KNOB = { 364, 56, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LP_KNOB = { 476, 56, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LEFT_KNOB = { 28, 182, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_KNOB = { 140, 182, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RIGHT_KNOB = { 252, 182, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WOW_KNOB = { 364, 182, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<int> FEEDBACK_KNOB = { 474, 182, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<int> WAVE_SELECT = { 42, 68, 337, 40 };
        const juce::Rectangle<int> WAVE_DISPLAY = { 42, 125, 337, 150 };
        const juce::Rectangle<int> OCT_KNOB = { 380, 46, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> FINE_KNOB = { 444, 46, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> PITCH_KNOB = { 513, 36, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SPREAD_KNOB = { 400, 122, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PAN_KNOB = { 513, 122, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> POSITION_KNOB = { 402, 238, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> GAIN_KNOB = { 510, 238, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<int> CUTOFF_KNOB = { 30, 16, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> RES_KNOB    = { 204, 16, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> ENV_KNOB    = { 376, 18, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> KEY_BUTTON  = { 228, 210, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<int> LFO_SPEED_KNOB = { 42, 40, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LFO_AMOUNT_KNOB = { 180, 40, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> FM_KNOB = { 372, 26, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<int> DISPLAY = { 25, 40, 450, 200 };
        const juce::Rectangle<int> ATTACK_KNOB = { 72, 284, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 168, 282, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SUSTAIN_KNOB = { 262, 284, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RELEASE_KNOB = { 356, 282, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Unison
    {
        // Coordenadas relativas al área del Unison
        const juce::Rectangle<int> VOICES_SLIDER = { 10, 90, 50, 40 };
        const juce::Rectangle<int> BALANCE_SLIDER = { 70, 90,  65, 40 };
        const juce::Rectangle<int> DETUNE_SLIDER = { 146, 90,  73, 40 };
        const juce::Rectangle<int> VISUALIZER = { 10, 150, 210, 120 };
    }
}