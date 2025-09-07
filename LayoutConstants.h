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
    const juce::Rectangle<int> MASTER_SECTION   = { 35, 169, 560, 250 };
    const juce::Rectangle<int> REVERB_SECTION   = { 35, 496, 560, 255 };
    const juce::Rectangle<int> DELAY_SECTION    = { 35, 827, 560, 255 };
    
    const juce::Rectangle<int> UNISON_1_SECTION = { 666, 125, 230, 325 };
    const juce::Rectangle<int> UNISON_2_SECTION = { 666, 459, 230, 325 };
    const juce::Rectangle<int> UNISON_3_SECTION = { 666, 794, 230, 325 };

    const juce::Rectangle<int> OSC_1_SECTION    = { 897, 125, 650, 325 };
    const juce::Rectangle<int> OSC_2_SECTION    = { 897, 459, 650, 325 };
    const juce::Rectangle<int> OSC_3_SECTION    = { 897, 794, 650, 325 };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<int> FILTER_SECTION   = { 1626, 174, 475, 225 };
    const juce::Rectangle<int> LFO_FM_SECTION   = { 1626, 502, 475, 225 };
    const juce::Rectangle<int> ENVELOPE_SECTION = { 1626, 700, 475, 420 };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<int> MASTER_GAIN_KNOB = { 88, 68, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> GLIDE_KNOB       = { 222, 44, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DRIVE_KNOB       = { 350, 44, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DARK_KNOB        = { 222, 128, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> BRIGHT_KNOB      = { 350, 128, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CHORUS_BUTTON    = { 458, 114, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<int> DRY_KNOB = { 112, 48, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WET_KNOB = { 242, 48, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIZE_KNOB = { 370, 48, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PRE_DELAY_KNOB = { 46, 132, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DIFFUSION_KNOB = { 176, 132, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DAMP_KNOB = { 304, 132, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 434, 132, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<int> DRY_KNOB = { 34, 46, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_VOL_KNOB = { 132, 46, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIDE_VOL_KNOB = { 234, 46, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> HP_KNOB = { 340, 46, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LP_KNOB = { 440, 46, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LEFT_KNOB = { 32, 160, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_KNOB = { 132, 160, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RIGHT_KNOB = { 234, 160, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WOW_KNOB = { 338, 160, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<int> FEEDBACK_KNOB = { 440, 160, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<int> WAVE_SELECT = { 40, 50, 337, 42 };
        const juce::Rectangle<int> WAVE_DISPLAY = { 42, 125, 337, 150 };
        const juce::Rectangle<int> OCT_KNOB = { 402, 50, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> FINE_KNOB = { 462, 50, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> PITCH_KNOB = { 521, 34, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SPREAD_KNOB = { 420, 118, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PAN_KNOB = { 521, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> POSITION_KNOB = { 420, 220, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> GAIN_KNOB = { 521, 222, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<int> CUTOFF_KNOB = { 24, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> RES_KNOB    = { 180, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> ENV_KNOB    = { 338, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> KEY_BUTTON  = { 206, 188, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<int> LFO_SPEED_KNOB = { 26, 28, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LFO_AMOUNT_KNOB = { 150, 28, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> FM_KNOB = { 324, 14, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<int> DISPLAY = { 10, 24, 430, 200 };
        const juce::Rectangle<int> ATTACK_KNOB = { 72, 250, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 158, 250, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SUSTAIN_KNOB = { 244, 250, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RELEASE_KNOB = { 330, 250, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Unison
    {
        // Coordenadas relativas al área del Unison
        const juce::Rectangle<int> VOICES_SLIDER = { 10, 90, 50, 40 };
        const juce::Rectangle<int> BALANCE_SLIDER = { 70, 90,  65, 40 };
        const juce::Rectangle<int> DETUNE_SLIDER = { 148, 90,  74, 40 };
        const juce::Rectangle<int> VISUALIZER = { 10, 150, 210, 120 };
    }
}