// PluginProcessor.h

#pragma once

#include <JuceHeader.h>
#include <juce_dsp/juce_dsp.h>
#include <vector>

// ==============================================================================
// 1. CLASE "SOUND": Simplemente le dice al sinte qué tipo de sonidos puede tocar.
// ==============================================================================
class SynthSound : public juce::SynthesiserSound
{
public:
    bool appliesToNote(int /*midiNoteNumber*/) override { return true; }
    bool appliesToChannel(int /*midiChannel*/) override { return true; }
};


// ==============================================================================
// 2. CLASE "VOICE": El corazón de nuestro nuevo motor. Contiene la lógica para
//    generar el sonido de UNA SOLA NOTA.
// ==============================================================================
class SynthVoice : public juce::SynthesiserVoice
{
public:
    SynthVoice() {}

    void setSampleRate(double sr) { env.setSampleRate(sr); sampleRateHz = sr; }

    // Asigna los parámetros globales del sintetizador a esta voz (DECLARACIÓN)
    void setParameters(juce::ADSR::Parameters& adsr,
        int* nf1, juce::AudioBuffer<float>* wavetable1, float* wavePos1, float* gain1, double* pitch1, float* pan1, float* spread1, double* detune1,
        int* nf2, juce::AudioBuffer<float>* wavetable2, float* wavePos2, float* gain2, double* pitch2, float* pan2, float* spread2, double* detune2,
        int* nf3, juce::AudioBuffer<float>* wavetable3, float* wavePos3, float* gain3, double* pitch3, float* pan3, float* spread3, double* detune3,
        double* cutoffHzPtr, double* qPtr, double* envAmtPtr, bool* keyTrackPtr, float* fmAmountPtr, float* lfoSpeedPtr, float* lfoAmountPtr, 
        float* glideSecondsPtr, double sr);

    bool canPlaySound(juce::SynthesiserSound* sound) override
    {
        return dynamic_cast<SynthSound*> (sound) != nullptr;
    }

    void startNote(int midiNoteNumber, float /*velocity*/, juce::SynthesiserSound*, int) override
    {
        // Ya no asignamos 'frequency' directamente, ahora es nuestro objetivo
        targetFrequency = juce::MidiMessage::getMidiNoteInHertz(midiNoteNumber);
        
        // Si el glide está desactivado o es la primera nota, empezamos en el tono final
        if (*pGlideSeconds <= 0.0f || lastNoteFrequency == 0.0)
        {
        currentFrequency = targetFrequency;
        }
        else // Si hay que deslizar, empezamos desde el tono de la última nota
        {
        currentFrequency = lastNoteFrequency;
        }

        env.noteOn();
        for (auto& v : unisonVoices) { v.readPosOsc1 = v.readPosOsc2 = v.readPosOsc3 = 0.0; }
        svfL = {}; svfR = {}; // reset filtro
    }

    void stopNote(float, bool allowTailOff) override
    {
        // "Recordamos" la frecuencia de esta nota para la siguiente que se toque
        lastNoteFrequency = targetFrequency;
        env.noteOff();
        if (!allowTailOff)
        {
            clearCurrentNote();
            env.reset();
        }
    }

    void pitchWheelMoved(int) override {}
    void controllerMoved(int, int) override {}

    void renderNextBlock(juce::AudioBuffer<float>& outputBuffer, int startSample, int numSamples) override;

private:
    juce::ADSR env;
    double currentFrequency = 0.0; // Frecuencia actual, que se deslizará
    double targetFrequency = 0.0;  // Frecuencia objetivo de la nota pulsada
    static double lastNoteFrequency; // Frecuencia de la última nota tocada (compartida entre todas las voces)

    int* numFrames1 = nullptr, * numFrames2 = nullptr, * numFrames3 = nullptr;

    // Punteros inicializados a nullptr para seguridad
    juce::AudioBuffer<float>* wt1 = nullptr, * wt2 = nullptr, * wt3 = nullptr;
    float* wavePosition1 = nullptr, * wavePosition2 = nullptr, * wavePosition3 = nullptr;
    float* oscGain1 = nullptr, * oscGain2 = nullptr, * oscGain3 = nullptr;
    double* pitchShift1 = nullptr, * pitchShift2 = nullptr, * pitchShift3 = nullptr;
    float* panOsc1 = nullptr, * panOsc2 = nullptr, * panOsc3 = nullptr;
    float* spreadOsc1 = nullptr, * spreadOsc2 = nullptr, * spreadOsc3 = nullptr;
    double* detuneOsc1 = nullptr, * detuneOsc2 = nullptr, * detuneOsc3 = nullptr;

    // ===== Filtro TPT SVF por canal =====
    struct SVFState { float ic1eq = 0.0f, ic2eq = 0.0f; };
    SVFState svfL, svfR;

    // Guardar nota para keytrack
    int currentMidiNote = 60;

    // Punteros a parámetros globales de filtro
    double* pCutoff = nullptr;   // Hz
    double* pQ = nullptr;        // Q
    double* pEnvAmt = nullptr;   // -1..1
    bool* pKeyTrack = nullptr;
    float* pFmAmount = nullptr;
    float* pLfoSpeed = nullptr;
    float* pLfoAmount = nullptr;
    float* pGlideSeconds = nullptr;
    float fmEffectLfoPhase = 0.0f;
    float fmModulatorPhase = 0.0f;
    float lfoPhase = 0.0f;

    double sampleRateHz = 48000.0;

    // Helper: procesa un sample por canal con SVF TPT (low-pass)
    inline float processSVFLP(float in, float cutoffHz, float Q, SVFState& s) noexcept
    {
        // --- MEJORA: Etapa de Saturación (Drive) ---
        // A medida que la resonancia (Q) aumenta, el drive también lo hace.
        // Un Q de 0.0 da un drive de 1.0 (sin efecto). Un Q de 1.0 da un drive de 6.0.
        const float drive = 1.0f + (Q * 5.0f);
        // std::tanh es una función de "clipping" suave, perfecta para simular saturación analógica.
        const float saturatedIn = std::tanh(in * drive);
        // ------------------------------------------

        const float g = std::tan(juce::MathConstants<float>::pi * cutoffHz / sampleRateHz);
        const float R = 1.0f / (2.0f * Q);
        const float a1 = 1.0f / (1.0f + 2.0f * R * g + g * g);

        // Ahora usamos la señal SATURADA ('saturatedIn') en lugar de la original ('in')
        const float v1 = a1 * (s.ic1eq + g * (saturatedIn - s.ic2eq));
        const float v2 = s.ic2eq + g * v1;

        // Actualizamos los integradores del filtro
        s.ic1eq = 2.0f * v1 - s.ic1eq;
        s.ic2eq = 2.0f * v2 - s.ic2eq;

        return v2; // Devolvemos la salida low-pass
    }

    static const int numUnisonVoices = 7;
    struct UnisonVoice
    {
        double readPosOsc1 = 0.0, readPosOsc2 = 0.0, readPosOsc3 = 0.0;
        float pan = 0.5f, pitchOffset = 0.0f;
    };
    std::vector<UnisonVoice> unisonVoices{ numUnisonVoices };
};


// ==============================================================================
// 3. CLASE PRINCIPAL DEL PROCESADOR: Ahora gestiona el sintetizador polifónico.
// ==============================================================================
class NeuraSynthAudioProcessor : public juce::AudioProcessor
{
public:
    NeuraSynthAudioProcessor();
    ~NeuraSynthAudioProcessor() override;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;
    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;
    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram(int index) override;
    const juce::String getProgramName(int index) override;
    void changeProgramName(int index, const juce::String& newName) override;
    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    // --- Setters de Wavetable ---
    void setWavetable1(const juce::AudioBuffer<float>& newWavetable);
    void setWavetable2(const juce::AudioBuffer<float>& newWavetable);
    void setWavetable3(const juce::AudioBuffer<float>& newWavetable);
    int getNumFrames1() const { return numFrames1; }
    int getNumFrames2() const { return numFrames2; }
    int getNumFrames3() const { return numFrames3; }

    // --- Setters de Master y Posición ---
    void setMasterGain(float newGain) { masterGain = newGain; }
    void setWavePosition1(float newPos);
    void setWavePosition2(float newPos);
    void setWavePosition3(float newPos);

    // --- Setters de Osciladores ---
    void setOsc1Gain(float newGain);
    void setOsc1Octave(int newOctave);
    void setOsc1Pitch(int newPitch);
    void setOsc1FineTune(double newFineTune);
    void setOsc1Detune(double newDetune);
    void setOsc1Spread(float newSpread);
    void setOsc1Pan(float newPan);
    void setOsc2Gain(float newGain);
    void setOsc2Octave(int newOctave);
    void setOsc2Pitch(int newPitch);
    void setOsc2FineTune(double newFineTune);
    void setOsc2Detune(double newDetune);
    void setOsc2Spread(float newSpread);
    void setOsc2Pan(float newPan);
    void setOsc3Gain(float newGain);
    void setOsc3Octave(int newOctave);
    void setOsc3Pitch(int newPitch);
    void setOsc3FineTune(double newFineTune);
    void setOsc3Detune(double newDetune);
    void setOsc3Spread(float newSpread);
    void setOsc3Pan(float newPan);

    // --- Setters para ADSR ---
    void setAttack(float attack);
    void setDecay(float decay);
    void setSustain(float sustain);
    void setRelease(float release);

    // --- Setters de filtro globales ---
    void setFilterCutoff(double hz) { filterCutoffHz = juce::jlimit(0.0, 20000.0, hz); updateAllVoices(); }
    void setFilterResonance(double q) { filterQ = juce::jlimit(0.0, 1.0, q);      updateAllVoices(); }
    void setFilterEnvAmount(double amt) { filterEnvAmt = juce::jlimit(0.0, 1.0, amt);    updateAllVoices(); }
    void setKeyTrack(bool enabled) { keyTrack = enabled;                          updateAllVoices(); }
    void setFMAmount(float amount) { fmAmount = amount; updateAllVoices(); }

    // --- Setters de LFO ---
    void setLfoSpeed(float speed) { lfoSpeedHz = speed; updateAllVoices(); }
    void setLfoAmount(float amount) { lfoAmount = amount; updateAllVoices(); }

    // --- Setters de la Sección Master ---
    void setGlide(float glideSeconds);
    void setDark(float amount);
    void setBright(float amount);
    void setDrive(float amount);
    void setChorus(bool isOn);

    double getFilterCutoff()   const { return filterCutoffHz; }
    double getFilterQ()        const { return filterQ; }
    double getFilterEnvAmt()   const { return filterEnvAmt; }
    bool   getKeyTrack()       const { return keyTrack; }

    juce::MidiKeyboardState keyboardState;

private:
    void updateAllVoices(); // Nueva función para actualizar parámetros

    juce::Synthesiser synth;
    juce::ADSR::Parameters adsrParams;
    double pitchShift1 = 0.0, pitchShift2 = 0.0, pitchShift3 = 0.0;
    int osc1Octave = 0, osc2Octave = 0, osc3Octave = 0;
    int osc1PitchSemitones = 0, osc2PitchSemitones = 0, osc3PitchSemitones = 0;
    double osc1FineTuneCents = 0.0, osc2FineTuneCents = 0.0, osc3FineTuneCents = 0.0;
    float masterGain = 0.7f;
    float wavePosition1 = 0.0f, wavePosition2 = 0.0f, wavePosition3 = 0.0f;
    float osc1Gain = 0.7f, osc2Gain = 0.0f, osc3Gain = 0.0f;
    float osc1Pan = 0.5f, osc2Pan = 0.5f, osc3Pan = 0.5f;
    float osc1Spread = 0.0f, osc2Spread = 0.0f, osc3Spread = 0.0f;
    double osc1DetuneCents = 0.0, osc2DetuneCents = 0.0, osc3DetuneCents = 0.0;
    juce::AudioBuffer<float> wavetable1, wavetable2, wavetable3;
    int numFrames1 = 1, numFrames2 = 1, numFrames3 = 1;

    // --- Parámetros de filtro globales (aplicados por voz)
    double filterCutoffHz = 20000.0; // abierto por defecto
    double filterQ = 0.0;     // 0.0000000
    double filterEnvAmt = 0.0;     // 0.00
    bool   keyTrack = false;
    float fmAmount = 0.0f;

    // --- Parámetros de LFO globales ---
    float lfoSpeedHz = 0.1f;
    float lfoAmount = 0.0f;

    // --- Parámetros de la Sección Master ---
    float glideSeconds = 0.0f;
    float darkAmount = 0.0f;
    float brightAmount = 0.0f;
    float driveAmount = 0.0f;
    bool chorusOn = false;

    // --- OBJETOS DSP PARA EFECTOS MASTER ---
    // Usamos una "cadena de procesadores" para los filtros de tono.
    // Tendremos un filtro Low-Shelf (Dark) y un High-Shelf (Bright).
    using Filter = juce::dsp::IIR::Filter<float>;
    using FilterChain = juce::dsp::ProcessorChain<Filter, Filter>;
    
    // Necesitamos una cadena para cada canal (estéreo)
    FilterChain leftTone, rightTone;

    // Objeto para el efecto de Chorus
    juce::dsp::Chorus<float> chorus;
    
    // El 'spec' guarda información como la frecuencia de muestreo
    juce::dsp::ProcessSpec spec;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NeuraSynthAudioProcessor)
};
