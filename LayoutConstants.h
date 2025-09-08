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
    const juce::Rectangle<int> MASTER_SECTION   = { -15, 170, 565, 248 };
    const juce::Rectangle<int> REVERB_SECTION   = { -15, 495, 565, 250 };
    const juce::Rectangle<int> DELAY_SECTION    = { -15, 826, 565, 260 };
    
    const juce::Rectangle<int> UNISON_1_SECTION = { 619, 125, 230, 315 };
    const juce::Rectangle<int> UNISON_2_SECTION = { 619, 459, 230, 315 };
    const juce::Rectangle<int> UNISON_3_SECTION = { 619, 794, 230, 315 };

    const juce::Rectangle<int> OSC_1_SECTION    = { 847, 125, 660, 315 };
    const juce::Rectangle<int> OSC_2_SECTION    = { 847, 459, 660, 315 };
    const juce::Rectangle<int> OSC_3_SECTION    = { 847, 794, 660, 315 };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<int> FILTER_SECTION   = { 1575, 156, 490, 200 };
    const juce::Rectangle<int> LFO_FM_SECTION   = { 1575, 451, 490, 200 };
    const juce::Rectangle<int> ENVELOPE_SECTION = { 1575, 703, 490, 415 };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<int> MASTER_GAIN_KNOB = { 92, 62, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> GLIDE_KNOB       = { 234, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DRIVE_KNOB       = { 370, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DARK_KNOB        = { 234, 123, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> BRIGHT_KNOB      = { 370, 123, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CHORUS_BUTTON    = { 483, 108, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<int> DRY_KNOB = { 117, 44, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WET_KNOB = { 255, 44, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIZE_KNOB = { 389, 44, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PRE_DELAY_KNOB = { 50, 123, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DIFFUSION_KNOB = { 188, 123, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DAMP_KNOB = { 320, 123, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 459, 123, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<int> DRY_KNOB = { 37, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_VOL_KNOB = { 142, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIDE_VOL_KNOB = { 251, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> HP_KNOB = { 358, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LP_KNOB = { 465, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LEFT_KNOB = { 37, 154, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_KNOB = { 142, 154, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RIGHT_KNOB = { 249, 154, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WOW_KNOB = { 356, 154, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<int> FEEDBACK_KNOB = { 463, 154, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<int> WAVE_SELECT = { 40, 50, 337, 42 };
        const juce::Rectangle<int> WAVE_DISPLAY = { 42, 125, 337, 150 };
        const juce::Rectangle<int> OCT_KNOB = { 437, 45, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> FINE_KNOB = { 498, 45, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> PITCH_KNOB = { 560, 28, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SPREAD_KNOB = { 455, 105, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PAN_KNOB = { 559, 105, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> POSITION_KNOB = { 452, 206, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> GAIN_KNOB = { 560, 206, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<int> CUTOFF_KNOB = { 25, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> RES_KNOB    = { 192, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> ENV_KNOB    = { 358, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> KEY_BUTTON  = { 170, 179, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<int> LFO_SPEED_KNOB = { 29, 26, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LFO_AMOUNT_KNOB = { 161, 26, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> FM_KNOB = { 345, 7, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<int> DISPLAY = { 23, 29, 430, 200 };
        const juce::Rectangle<int> ATTACK_KNOB = { 77, 245, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 167, 245, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SUSTAIN_KNOB = { 257, 245, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RELEASE_KNOB = { 347, 245, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
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