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
    const juce::Point<int> KNOB_LARGE = { 100, 101 };
    const juce::Point<int> KNOB_MEDIUM = { 75, 75 };
    const juce::Point<int> KNOB_SMALL = { 47, 47 };
    const juce::Point<int> BUTTON = { 83, 30 };

    // --- Posiciones de las Secciones Principales ---
    static const juce::Rectangle<int> PROMPT_SECTION{ 370, 20, 510, 45 };
    const juce::Rectangle<int> MASTER_SECTION   = { 68, 159, 580, 272 };
    const juce::Rectangle<int> REVERB_SECTION   = { 68, 550, 580, 242 };
    const juce::Rectangle<int> DELAY_SECTION    = { 68, 909, 580, 290 };
    
    const juce::Rectangle<int> UNISON_1_SECTION = { 729, 120, 270, 345 };
    const juce::Rectangle<int> UNISON_2_SECTION = { 729, 490, 270, 345 };
    const juce::Rectangle<int> UNISON_3_SECTION = { 729, 859, 270, 345 };

    const juce::Rectangle<int> OSC_1_SECTION    = { 994, 120, 685, 345 };
    const juce::Rectangle<int> OSC_2_SECTION    = { 994, 490, 685, 345 };
    const juce::Rectangle<int> OSC_3_SECTION    = { 994, 859, 685, 345 };
    // Nota: El Unison lo integraremos dentro del layout del oscilador.

    const juce::Rectangle<int> FILTER_SECTION   = { 1765, 158, 520, 272 };
    const juce::Rectangle<int> LFO_FM_SECTION   = { 1765, 552, 520, 200 };
    const juce::Rectangle<int> ENVELOPE_SECTION = { 1765, 871, 520, 340 };

    // --- Posiciones de los Knobs y Botones DENTRO de sus secciones ---
    
    namespace Master
    {
        // Coordenadas relativas a la esquina superior izquierda de la sección MASTER (40, 100)
        const juce::Rectangle<int> MASTER_GAIN_KNOB = { 90, 74, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> GLIDE_KNOB       = { 240, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DRIVE_KNOB       = { 380, 43, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DARK_KNOB        = { 240, 135, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> BRIGHT_KNOB      = { 380, 135, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CHORUS_BUTTON    = { 485, 117, BUTTON.x, BUTTON.y };
    }

    namespace Reverb
    {
        const juce::Rectangle<int> DRY_KNOB = { 118, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WET_KNOB = { 260, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIZE_KNOB = { 402, 41, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PRE_DELAY_KNOB = { 47, 130, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DIFFUSION_KNOB = { 189, 130, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DAMP_KNOB = { 330, 130, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 475, 130, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Delay
    {
        const juce::Rectangle<int> DRY_KNOB = { 31, 49, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_VOL_KNOB = { 141, 49, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SIDE_VOL_KNOB = { 254, 49, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> HP_KNOB = { 366, 49, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LP_KNOB = { 479, 49, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> LEFT_KNOB = { 32, 172, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> CENTER_KNOB = { 141, 172, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RIGHT_KNOB = { 256, 172, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> WOW_KNOB = { 366, 172, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
        const juce::Rectangle<int> FEEDBACK_KNOB = { 479, 172, KNOB_MEDIUM.x, KNOB_MEDIUM.y }; // Extra, lo centramos abajo
    }

    namespace Oscillator
    {
        // Layout para los 3 osciladores, es el mismo
        const juce::Rectangle<int> WAVE_SELECT = { 25, 65, 372, 55 };
        const juce::Rectangle<int> WAVE_DISPLAY = { 36, 158, 360, 150 };
        const juce::Rectangle<int> OCT_KNOB = { 465, 44, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> FINE_KNOB = { 532, 44, KNOB_SMALL.x, KNOB_SMALL.y };
        const juce::Rectangle<int> PITCH_KNOB = { 595, 30, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SPREAD_KNOB = { 486, 116, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> PAN_KNOB = { 595, 119, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> POSITION_KNOB = { 486, 235, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> GAIN_KNOB = { 594, 236, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Filter
    {
        // Coordenadas relativas a la sección FILTER
        const juce::Rectangle<int> CUTOFF_KNOB = { 37, 27, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> RES_KNOB    = { 199, 27, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> ENV_KNOB    = { 366, 27, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> KEY_BUTTON  = { 210, 212, BUTTON.x, BUTTON.y };
    }

    namespace LFO_FM
    {
        const juce::Rectangle<int> LFO_SPEED_KNOB = { 37, 22, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> LFO_AMOUNT_KNOB = { 201, 22, KNOB_LARGE.x, KNOB_LARGE.y };
        const juce::Rectangle<int> FM_KNOB = { 366, 22, KNOB_LARGE.x, KNOB_LARGE.y };
    }

    namespace Envelope
    {
        const juce::Rectangle<int> DISPLAY = { 44, 20, 430, 167 };
        const juce::Rectangle<int> ATTACK_KNOB = { 48, 190, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> DECAY_KNOB = { 158, 190, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> SUSTAIN_KNOB = { 269, 190, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
        const juce::Rectangle<int> RELEASE_KNOB = { 379, 190, KNOB_MEDIUM.x, KNOB_MEDIUM.y };
    }

    namespace Unison
    {
        // Coordenadas relativas al área del Unison
        const juce::Rectangle<int> VOICES_SLIDER = { 29, 90, 50, 40 };
        const juce::Rectangle<int> BALANCE_SLIDER = { 106, 90,  65, 40 };
        const juce::Rectangle<int> DETUNE_SLIDER = { 190, 90,  74, 40 };
        const juce::Rectangle<int> VISUALIZER = { 28, 160, 230, 150 };
    }

}