// PluginProcessor.cpp

#include "PluginProcessor.h"
#include "PluginEditor.h"

// DEFINICIÓN de setParameters(...) (va en el .cpp, no en el .h)
void SynthVoice::setParameters(juce::ADSR::Parameters& adsr,
    int* nf1, juce::AudioBuffer<float>* wavetable1, float* wavePos1, float* gain1, double* pitch1, float* pan1, float* spread1, double* detune1,
    int* nf2, juce::AudioBuffer<float>* wavetable2, float* wavePos2, float* gain2, double* pitch2, float* pan2, float* spread2, double* detune2,
    int* nf3, juce::AudioBuffer<float>* wavetable3, float* wavePos3, float* gain3, double* pitch3, float* pan3, float* spread3, double* detune3,
    double* cutoffHzPtr, double* qPtr, double* envAmtPtr, bool* keyTrackPtr, float* fmAmountPtr, float* lfoSpeedPtr, float* lfoAmountPtr, double sr)
{
    env.setParameters(adsr);

    numFrames1 = nf1; numFrames2 = nf2; numFrames3 = nf3;

    wt1 = wavetable1; wavePosition1 = wavePos1; oscGain1 = gain1; pitchShift1 = pitch1; panOsc1 = pan1; spreadOsc1 = spread1; detuneOsc1 = detune1;
    wt2 = wavetable2; wavePosition2 = wavePos2; oscGain2 = gain2; pitchShift2 = pitch2; panOsc2 = pan2; spreadOsc2 = spread2; detuneOsc2 = detune2;
    wt3 = wavetable3; wavePosition3 = wavePos3; oscGain3 = gain3; pitchShift3 = pitch3; panOsc3 = pan3; spreadOsc3 = spread3; detuneOsc3 = detune3;

    pCutoff = cutoffHzPtr;
    pQ = qPtr;
    pEnvAmt = envAmtPtr;
    pKeyTrack = keyTrackPtr;
    pFmAmount = fmAmountPtr;
    pLfoSpeed = lfoSpeedPtr;
    pLfoAmount = lfoAmountPtr;

    sampleRateHz = sr;
}

// Render de la voz con filtro SVF TPT y modulación de cutoff (ENV + KeyTrack)
void SynthVoice::renderNextBlock(juce::AudioBuffer<float>& outputBuffer, int startSample, int numSamples)
{
    if (!isVoiceActive()) return;

    // --- Bucle principal muestra por muestra ---
    for (int sample = startSample; sample < startSample + numSamples; ++sample)
    {
        float envVal = env.getNextSample();

        // --- LÓGICA DEL LFO ---
        // 1. Generar la onda del LFO (seno)
        float lfoSample = std::sin(lfoPhase);
        lfoPhase += (*pLfoSpeed / sampleRateHz) * juce::MathConstants<float>::twoPi;
        if (lfoPhase >= juce::MathConstants<float>::twoPi)
            lfoPhase -= juce::MathConstants<float>::twoPi;

        // 2. Calcular cuánto afectará al tono (en semitonos)
        // El Amount va de 0 a 1. Lo escalamos para que en su máximo, module +/- 2 semitonos.
        // ¡Puedes cambiar el '2.0f' para un vibrato más sutil o más extremo!
        float pitchModulation = lfoSample * *pLfoAmount * 2.0f;

        // --- PASO 1: Calcular la señal del MODULADOR de FM dedicado ---
        float fmAmount = (pFmAmount ? *pFmAmount : 0.0f);
        float modulatorSample = 0.0f;

        if (fmAmount != 0.0f)
        {
            // La frecuencia del modulador se basa en la frecuencia de OSC 1
            double osc1Freq = frequency * std::pow(2.0, *pitchShift1);
            double modulatorFreq;

            if (fmAmount > 0.0f) // Derecha -> Brillante (una octava arriba)
            {
                modulatorFreq = osc1Freq * 2.0;
            }
            else // Izquierda -> Oscuro (una octava abajo)
            {
                modulatorFreq = osc1Freq * 0.5;
            }

            // Generamos la muestra del modulador (seno puro)
            modulatorSample = std::sin(fmModulatorPhase);
            fmModulatorPhase += (modulatorFreq / sampleRateHz) * juce::MathConstants<float>::twoPi;
            if (fmModulatorPhase >= juce::MathConstants<float>::twoPi)
                fmModulatorPhase -= juce::MathConstants<float>::twoPi;
        }

        // --- PASO 2: Calcular la PROFUNDIDAD de la modulación (la sutileza) ---
        // ¡ESTE VALOR ES LA CLAVE DE LA SUTILEZA!
        // Si el efecto sigue siendo muy brusco, reduce este número (p. ej. a 100.0, 50.0...)
        const float fmDepthScale = 200.0f;
        float modulationDepth = modulatorSample * std::abs(fmAmount) * fmDepthScale;

        // --- PASO 3: Generar los osciladores principales con sus frecuencias ya moduladas ---
        float finalLeft = 0.0f;
        float finalRight = 0.0f;

        // Convertimos la modulación de semitonos a un factor de frecuencia
        double lfoPitchFactor = std::pow(2.0, pitchModulation / 12.0);

        // Frecuencias base de cada oscilador
        double baseFreq1 = frequency * std::pow(2.0, *pitchShift1) * lfoPitchFactor; 
        double baseFreq2 = frequency * std::pow(2.0, *pitchShift2) * lfoPitchFactor; 
        double baseFreq3 = frequency * std::pow(2.0, *pitchShift3) * lfoPitchFactor; 

        // Aplicamos la modulación a cada uno
        double modulatedFreq1 = baseFreq1 + modulationDepth;
        double modulatedFreq2 = baseFreq2 + modulationDepth;
        double modulatedFreq3 = baseFreq3 + modulationDepth;

        // Calculamos los incrementos DENTRO del bucle
        double increment1 = (wt1 && modulatedFreq1 > 0) ? (modulatedFreq1 / getSampleRate()) * 2048.0 : 0.0;
        double increment2 = (wt2 && modulatedFreq2 > 0) ? (modulatedFreq2 / getSampleRate()) * 2048.0 : 0.0;
        double increment3 = (wt3 && modulatedFreq3 > 0) ? (modulatedFreq3 / getSampleRate()) * 2048.0 : 0.0;

        // Función para generar el audio (simplificada)
        auto getOscSample = [&](juce::AudioBuffer<float>* wt, int numFrames, float wavePosition, double& readPos, double increment, float gain, float pan) -> std::pair<float, float> {
            if (!wt || wt->getNumSamples() == 0 || gain <= 0.0f) return { 0.0f, 0.0f };
            float frameFloat = wavePosition * (numFrames > 1 ? numFrames - 1 : 0);
            int frameIndex = static_cast<int>(std::floor(frameFloat));
            float frameFrac = frameFloat - frameIndex;
            auto getSample = [&](int frame, double rPos) {
                int pos0 = static_cast<int>(rPos); float frac = rPos - pos0;
                float s0 = wt->getSample(0, (frame * 2048 + pos0) % wt->getNumSamples());
                float s1 = wt->getSample(0, (frame * 2048 + ((pos0 + 1) % 2048)) % wt->getNumSamples());
                return (1.0f - frac) * s0 + frac * s1;
                };
            float voiceSample = (1.0f - frameFrac) * getSample(frameIndex, readPos) + frameFrac * getSample(frameIndex + 1, readPos);
            float panAngle = pan * juce::MathConstants<float>::halfPi;
            readPos += increment;
            if (readPos >= 2048.0) readPos -= 2048.0;
            return { voiceSample * std::cos(panAngle) * gain, voiceSample * std::sin(panAngle) * gain };
            };

        auto osc1_out = getOscSample(wt1, *numFrames1, *wavePosition1, unisonVoices[0].readPosOsc1, increment1, *oscGain1, *panOsc1);
        finalLeft += osc1_out.first; finalRight += osc1_out.second;

        auto osc2_out = getOscSample(wt2, *numFrames2, *wavePosition2, unisonVoices[0].readPosOsc2, increment2, *oscGain2, *panOsc2);
        finalLeft += osc2_out.first; finalRight += osc2_out.second;

        auto osc3_out = getOscSample(wt3, *numFrames3, *wavePosition3, unisonVoices[0].readPosOsc3, increment3, *oscGain3, *panOsc3);
        finalLeft += osc3_out.first; finalRight += osc3_out.second;

        // --- PASO 4: Filtrado y Salida ---
        double baseCutoff = (pCutoff ? *pCutoff : 20000.0);
        // ... (resto del código del filtro y envolvente sin cambios)
        if (pKeyTrack && *pKeyTrack)
            baseCutoff *= std::pow(2.0, (currentMidiNote - 60) / 12.0);
        double modulationOctaves = (pEnvAmt ? *pEnvAmt : 0.0) * envVal * 5.0;
        double fc = baseCutoff * std::pow(2.0, modulationOctaves);
        fc = juce::jlimit(20.0, 20000.0, fc);
        const double q = (pQ ? juce::jlimit(0.1, 1.0, *pQ) : 0.707);

        float fl = processSVFLP(finalLeft, (float)fc, (float)q, svfL);
        float fr = processSVFLP(finalRight, (float)fc, (float)q, svfR);

        outputBuffer.addSample(0, sample, fl * envVal);
        outputBuffer.addSample(1, sample, fr * envVal);

        if (!env.isActive())
        {
            clearCurrentNote();
            break;
        }
    }
}


// --- IMPLEMENTACIÓN DEL PROCESADOR PRINCIPAL (NeuraSynthAudioProcessor) ---

NeuraSynthAudioProcessor::NeuraSynthAudioProcessor()
{
    const int numVoices = 16;
    for (int i = 0; i < numVoices; ++i)
        synth.addVoice(new SynthVoice());
    synth.addSound(new SynthSound());
}

NeuraSynthAudioProcessor::~NeuraSynthAudioProcessor() {}

void NeuraSynthAudioProcessor::prepareToPlay(double sampleRate, int /*samplesPerBlock*/)
{
    synth.setCurrentPlaybackSampleRate(sampleRate);
    for (int i = 0; i < synth.getNumVoices(); ++i)
        if (auto* voice = dynamic_cast<SynthVoice*>(synth.getVoice(i)))
            voice->setSampleRate(sampleRate);

    updateAllVoices();
}

void NeuraSynthAudioProcessor::releaseResources() {}

void NeuraSynthAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages)
{
    buffer.clear();
    keyboardState.processNextMidiBuffer(midiMessages, 0, buffer.getNumSamples(), true);
    synth.renderNextBlock(buffer, midiMessages, 0, buffer.getNumSamples());
    buffer.applyGain(masterGain);
}

void NeuraSynthAudioProcessor::updateAllVoices()
{
    for (int i = 0; i < synth.getNumVoices(); ++i)
        if (auto* voice = dynamic_cast<SynthVoice*>(synth.getVoice(i)))
            voice->setParameters(adsrParams,
                &numFrames1, &wavetable1, &wavePosition1, &osc1Gain, &pitchShift1, &osc1Pan, &osc1Spread, &osc1DetuneCents,
                &numFrames2, &wavetable2, &wavePosition2, &osc2Gain, &pitchShift2, &osc2Pan, &osc2Spread, &osc2DetuneCents,
                &numFrames3, &wavetable3, &wavePosition3, &osc3Gain, &pitchShift3, &osc3Pan, &osc3Spread, &osc3DetuneCents,
                &filterCutoffHz, &filterQ, &filterEnvAmt, &keyTrack, &fmAmount, &lfoSpeedHz, &lfoAmount, getSampleRate()
            );
}

// Función auxiliar para calcular el desplazamiento de pitch total
auto calculatePitchShift = [](int oct, int pitch, double fine)
    {
        return (double)oct + (pitch / 12.0) + (fine / 1200.0);
    };

// Setters de Wavetable
void NeuraSynthAudioProcessor::setWavetable1(const juce::AudioBuffer<float>& b) { wavetable1.makeCopyOf(b); numFrames1 = b.getNumSamples() / 2048; }
void NeuraSynthAudioProcessor::setWavetable2(const juce::AudioBuffer<float>& b) { wavetable2.makeCopyOf(b); numFrames2 = b.getNumSamples() / 2048; }
void NeuraSynthAudioProcessor::setWavetable3(const juce::AudioBuffer<float>& b) { wavetable3.makeCopyOf(b); numFrames3 = b.getNumSamples() / 2048; }

// Setters de Posición
void NeuraSynthAudioProcessor::setWavePosition1(float p) { wavePosition1 = p; }
void NeuraSynthAudioProcessor::setWavePosition2(float p) { wavePosition2 = p; }
void NeuraSynthAudioProcessor::setWavePosition3(float p) { wavePosition3 = p; }

// --- Setters Oscilador 1 ---
void NeuraSynthAudioProcessor::setOsc1Gain(float g) { osc1Gain = g; }
void NeuraSynthAudioProcessor::setOsc1Octave(int v) { osc1Octave = v; pitchShift1 = calculatePitchShift(osc1Octave, osc1PitchSemitones, osc1FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc1Pitch(int v) { osc1PitchSemitones = v; pitchShift1 = calculatePitchShift(osc1Octave, osc1PitchSemitones, osc1FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc1FineTune(double v) { osc1FineTuneCents = v; pitchShift1 = calculatePitchShift(osc1Octave, osc1PitchSemitones, osc1FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc1Detune(double d) { osc1DetuneCents = d; updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc1Spread(float s) { osc1Spread = s; updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc1Pan(float p) { osc1Pan = p; updateAllVoices(); }

// --- Setters Oscilador 2 ---
void NeuraSynthAudioProcessor::setOsc2Gain(float g) { osc2Gain = g; }
void NeuraSynthAudioProcessor::setOsc2Octave(int v) { osc2Octave = v; pitchShift2 = calculatePitchShift(osc2Octave, osc2PitchSemitones, osc2FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc2Pitch(int v) { osc2PitchSemitones = v; pitchShift2 = calculatePitchShift(osc2Octave, osc2PitchSemitones, osc2FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc2FineTune(double v) { osc2FineTuneCents = v; pitchShift2 = calculatePitchShift(osc2Octave, osc2PitchSemitones, osc2FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc2Detune(double d) { osc2DetuneCents = d; updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc2Spread(float s) { osc2Spread = s; updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc2Pan(float p) { osc2Pan = p; updateAllVoices(); }

// --- Setters Oscilador 3 ---
void NeuraSynthAudioProcessor::setOsc3Gain(float g) { osc3Gain = g; }
void NeuraSynthAudioProcessor::setOsc3Octave(int v) { osc3Octave = v; pitchShift3 = calculatePitchShift(osc3Octave, osc3PitchSemitones, osc3FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc3Pitch(int v) { osc3PitchSemitones = v; pitchShift3 = calculatePitchShift(osc3Octave, osc3PitchSemitones, osc3FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc3FineTune(double v) { osc3FineTuneCents = v; pitchShift3 = calculatePitchShift(osc3Octave, osc3PitchSemitones, osc3FineTuneCents); updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc3Detune(double d) { osc3DetuneCents = d; updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc3Spread(float s) { osc3Spread = s; updateAllVoices(); }
void NeuraSynthAudioProcessor::setOsc3Pan(float p) { osc3Pan = p; updateAllVoices(); }

// Setters para ADSR
void NeuraSynthAudioProcessor::setAttack(float a) { adsrParams.attack = a; updateAllVoices(); }
void NeuraSynthAudioProcessor::setDecay(float d) { adsrParams.decay = d; updateAllVoices(); }
void NeuraSynthAudioProcessor::setSustain(float s) { adsrParams.sustain = s; updateAllVoices(); }
void NeuraSynthAudioProcessor::setRelease(float r) { adsrParams.release = r; updateAllVoices(); }

// --- Resto de funciones estándar de JUCE ---
juce::AudioProcessorEditor* NeuraSynthAudioProcessor::createEditor() { return new NeuraSynthAudioProcessorEditor(*this); }
bool NeuraSynthAudioProcessor::hasEditor() const { return true; }
const juce::String NeuraSynthAudioProcessor::getName() const { return JucePlugin_Name; }
bool NeuraSynthAudioProcessor::acceptsMidi() const { return true; }
bool NeuraSynthAudioProcessor::producesMidi() const { return false; }
bool NeuraSynthAudioProcessor::isMidiEffect() const { return false; }
double NeuraSynthAudioProcessor::getTailLengthSeconds() const { return 0.0; }
int NeuraSynthAudioProcessor::getNumPrograms() { return 1; }
int NeuraSynthAudioProcessor::getCurrentProgram() { return 0; }
void NeuraSynthAudioProcessor::setCurrentProgram(int /*index*/) {}
const juce::String NeuraSynthAudioProcessor::getProgramName(int /*index*/) { return {}; }
void NeuraSynthAudioProcessor::changeProgramName(int /*index*/, const juce::String& /*newName*/) {}
void NeuraSynthAudioProcessor::getStateInformation(juce::MemoryBlock& /*destData*/) {}
void NeuraSynthAudioProcessor::setStateInformation(const void* /*data*/, int /*sizeInBytes*/) {}
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new NeuraSynthAudioProcessor(); }
