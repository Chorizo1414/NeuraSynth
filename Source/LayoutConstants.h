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
    const juce::Point<int> KNOB_LARGE = { 95, 96 };
    const juce::Point<int> KNOB_MEDIUM = { 72, 72 };
    const juce::Point<int> KNOB_SMALL = { 60, 63 };
    const juce::Point<int> BUTTON = { 52, 20 };

    // --- Posiciones de las Secciones Principales ---
    const juce::Rectangle<int> MASTER_SECTION   = { 32, 164, 558, 240 };
    const juce::Rectangle<int> REVERB_SECTION   = { 32, 474, 558, 240 };
    const juce::Rectangle<int> DELAY_SECTION    = { 32, 793, 558, 250 };
    
    const juce::Rectangle<int> UNISON_1_SECTION = { 637, 120, 230, 300 };
    const juce::Rectangle<int> UNISON_2_SECTION = { 637, 436, 230, 300 };
    const juce::Rectangle<int> UNISON_3_SECTION = { 637, 757, 230, 300 };

    const juce::Rectangle<int> OSC_1_SECTION    = { 867, 120, 635, 300 };
    const juce::Rectangle<int> OSC_2_SECTION    = { 867, 436, 635, 300 };
    const juce::Rectangle<int> OSC_3_SECTION    = { 867, 757, 635, 300 };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<int> FILTER_SECTION   = { 1551, 148, 480, 210 };
    const juce::Rectangle<int> LFO_FM_SECTION   = { 1551, 432, 480, 210 };
    const juce::Rectangle<int> ENVELOPE_SECTION = { 1551, 679, 480, 400 };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<int> MASTER_GAIN_KNOB = { 84, 58, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> GLIDE_KNOB       = { 222, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DRIVE_KNOB       = { 350, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DARK_KNOB        = { 222, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> BRIGHT_KNOB      = { 352, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CHORUS_BUTTON    = { 458, 102, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<int> DRY_KNOB = { 112, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WET_KNOB = { 244, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIZE_KNOB = { 368, 42, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PRE_DELAY_KNOB = { 50, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DIFFUSION_KNOB = { 178, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DAMP_KNOB = { 304, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 438, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<int> DRY_KNOB = { 32, 36, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_VOL_KNOB = { 136, 36, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIDE_VOL_KNOB = { 236, 36, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> HP_KNOB = { 340, 36, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LP_KNOB = { 442, 36, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LEFT_KNOB = { 32, 138, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_KNOB = { 132, 138, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RIGHT_KNOB = { 236, 136, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WOW_KNOB = { 336, 140, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<int> FEEDBACK_KNOB = { 440, 138, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<int> WAVE_SELECT = { 40, 50, 337, 42 };
        const juce::Rectangle<int> WAVE_DISPLAY = { 42, 125, 337, 150 };
        const juce::Rectangle<int> OCT_KNOB = { 402, 40, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> FINE_KNOB = { 462, 40, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> PITCH_KNOB = { 521, 26, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SPREAD_KNOB = { 420, 100, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PAN_KNOB = { 521, 102, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> POSITION_KNOB = { 420, 194, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> GAIN_KNOB = { 521, 196, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<int> CUTOFF_KNOB = { 25, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> RES_KNOB    = { 180, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> ENV_KNOB    = { 338, 8, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> KEY_BUTTON  = { 206, 170, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<int> LFO_SPEED_KNOB = { 29, 26, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LFO_AMOUNT_KNOB = { 152, 26, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> FM_KNOB = { 328, 4, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<int> DISPLAY = { 23, 29, 430, 200 };
        const juce::Rectangle<int> ATTACK_KNOB = { 72, 222, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 158, 222, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SUSTAIN_KNOB = { 244, 222, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RELEASE_KNOB = { 332, 222, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
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