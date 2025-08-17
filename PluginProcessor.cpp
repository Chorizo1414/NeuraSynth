// PluginProcessor.cpp

#include "PluginProcessor.h"
#include "PluginEditor.h"

// DEFINICIÓN de setParameters(...) (va en el .cpp, no en el .h)
void SynthVoice::setParameters(juce::ADSR::Parameters& adsr,
    int* nf1, juce::AudioBuffer<float>* wavetable1, float* wavePos1, float* gain1, double* pitch1, float* pan1, float* spread1, double* detune1,
    int* nf2, juce::AudioBuffer<float>* wavetable2, float* wavePos2, float* gain2, double* pitch2, float* pan2, float* spread2, double* detune2,
    int* nf3, juce::AudioBuffer<float>* wavetable3, float* wavePos3, float* gain3, double* pitch3, float* pan3, float* spread3, double* detune3,
    double* cutoffHzPtr, double* qPtr, double* envAmtPtr, bool* keyTrackPtr, float* fmAmountPtr, double sr)
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

    sampleRateHz = sr;
}

// Render de la voz con filtro SVF TPT y modulación de cutoff (ENV + KeyTrack)
void SynthVoice::renderNextBlock(juce::AudioBuffer<float>& outputBuffer, int startSample, int numSamples)
{
    if (!isVoiceActive() || pitchShift1 == nullptr) return;

    // Calculamos el incremento base para OSC3 (OSC1 y OSC2 se calculan por muestra)
    double baseIncrement3 = (wt3 && wt3->getNumSamples() > 0) ? (frequency * std::pow(2.0, *pitchShift3)) / getSampleRate() * 2048.0 : 0.0;

    float gainCorrection = 1.0f / std::sqrt((float)numUnisonVoices);

    // Bucle principal muestra por muestra
    for (int sample = startSample; sample < startSample + numSamples; ++sample)
    {
        float envVal = env.getNextSample();
        float finalLeft = 0.0f;
        float finalRight = 0.0f;

        // --- PASO 1: Calcular la señal del MODULADOR (OSC 2) ---
        float modulatorSignal = 0.0f;
        double baseIncrement2 = (wt2 && wt2->getNumSamples() > 0) ? (frequency * std::pow(2.0, *pitchShift2)) / getSampleRate() * 2048.0 : 0.0;

        if (wt2 && wt2->getNumSamples() > 0 && *oscGain2 > 0.0f)
        {
            // Para FM, usamos solo la voz central del modulador para un efecto más claro
            auto& v = unisonVoices[0];
            double voiceIncrement = baseIncrement2;

            float frameFloat = *wavePosition2 * (*numFrames2 > 1 ? *numFrames2 - 1 : 0);
            int frameIndex = static_cast<int>(std::floor(frameFloat));
            float frameFrac = frameFloat - frameIndex;

            auto getSample = [&](juce::AudioBuffer<float>* wt, int frame, double readPos) {
                int pos0 = static_cast<int>(readPos);
                float frac = readPos - pos0;
                float s0 = wt->getSample(0, (frame * 2048 + pos0) % wt->getNumSamples());
                float s1 = wt->getSample(0, (frame * 2048 + ((pos0 + 1) % 2048)) % wt->getNumSamples());
                return (1.0f - frac) * s0 + frac * s1;
                };
            float sampleFrame0 = getSample(wt2, frameIndex, v.readPosOsc2);
            float sampleFrame1 = getSample(wt2, frameIndex + 1, v.readPosOsc2);
            modulatorSignal = (1.0f - frameFrac) * sampleFrame0 + frameFrac * sampleFrame1;

            // Avanzamos la fase de todas las voces de OSC2 para mantener consistencia
            for (auto& unisonVoice : unisonVoices)
            {
                unisonVoice.readPosOsc2 += baseIncrement2 * std::pow(2.0, (unisonVoice.pitchOffset / 1200.0));
                if (unisonVoice.readPosOsc2 >= 2048.0) unisonVoice.readPosOsc2 -= 2048.0;
            }
        }

        // --- PASO 2: Aplicar la modulación a la frecuencia de OSC 1 ---
        const float fmModulationIndex = 1000.0f; // <-- ¡Ajusta esta intensidad!
        float fmAmount = (pFmAmount ? *pFmAmount : 0.0f);
        double modulatedFrequency = frequency + (modulatorSignal * fmAmount * fmModulationIndex);
        if (modulatedFrequency < 0) modulatedFrequency = 0;

        // Recalculamos el incremento de OSC1 (Portador) DENTRO del bucle con la nueva frecuencia
        double baseIncrement1 = (wt1 && wt1->getNumSamples() > 0) ? (modulatedFrequency * std::pow(2.0, *pitchShift1)) / getSampleRate() * 2048.0 : 0.0;

        // --- PASO 3: Generar la señal del PORTADOR (OSC 1) ---
        if (wt1 && wt1->getNumSamples() > 0 && *oscGain1 > 0.0f)
        {
            for (int i = 0; i < numUnisonVoices; ++i)
            {
                auto& v = unisonVoices[i];
                float offset = ((float)i / (float)(numUnisonVoices - 1) - 0.5f) * 2.0f;
                float pitchOffset = offset * *detuneOsc1;
                float pan = *panOsc1 + offset * (*spreadOsc1 * 0.5f);

                double voiceIncrement = baseIncrement1 * std::pow(2.0, pitchOffset / 1200.0);
                float frameFloat = *wavePosition1 * (*numFrames1 > 1 ? *numFrames1 - 1 : 0);
                int frameIndex = static_cast<int>(std::floor(frameFloat));
                float frameFrac = frameFloat - frameIndex;
                auto getSample = [&](juce::AudioBuffer<float>* wt, int frame, double readPos) {
                    int pos0 = static_cast<int>(readPos);
                    float frac = readPos - pos0;
                    float s0 = wt->getSample(0, (frame * 2048 + pos0) % wt->getNumSamples());
                    float s1 = wt->getSample(0, (frame * 2048 + ((pos0 + 1) % 2048)) % wt->getNumSamples());
                    return (1.0f - frac) * s0 + frac * s1;
                    };
                float sampleFrame0 = getSample(wt1, frameIndex, v.readPosOsc1);
                float sampleFrame1 = getSample(wt1, frameIndex + 1, v.readPosOsc1);
                float voiceSample = (1.0f - frameFrac) * sampleFrame0 + frameFrac * sampleFrame1;
                float panAngle = pan * juce::MathConstants<float>::halfPi;

                finalLeft += voiceSample * std::cos(panAngle) * *oscGain1;
                finalRight += voiceSample * std::sin(panAngle) * *oscGain1;

                v.readPosOsc1 += voiceIncrement;
                if (v.readPosOsc1 >= 2048.0) v.readPosOsc1 -= 2048.0;
            }
        }

        // --- OSC 3 (funciona de forma independiente) ---
        if (wt3 && wt3->getNumSamples() > 0 && *oscGain3 > 0.0f)
        {
            for (int i = 0; i < numUnisonVoices; ++i)
            {
                auto& v = unisonVoices[i];
                float offset = ((float)i / (float)(numUnisonVoices - 1) - 0.5f) * 2.0f;
                float pitchOffset = offset * *detuneOsc3;
                float pan = *panOsc3 + offset * (*spreadOsc3 * 0.5f);
                double voiceIncrement = baseIncrement3 * std::pow(2.0, pitchOffset / 1200.0);
                // ... (el resto del código de generación de OSC 3 que ya tenías)
                float frameFloat = *wavePosition3 * (*numFrames3 > 1 ? *numFrames3 - 1 : 0);
                int frameIndex = static_cast<int>(std::floor(frameFloat));
                float frameFrac = frameFloat - frameIndex;
                auto getSample = [&](juce::AudioBuffer<float>* wt, int frame, double readPos) {
                    int pos0 = static_cast<int>(readPos);
                    float frac = readPos - pos0;
                    float s0 = wt->getSample(0, (frame * 2048 + pos0) % wt->getNumSamples());
                    float s1 = wt->getSample(0, (frame * 2048 + ((pos0 + 1) % 2048)) % wt->getNumSamples());
                    return (1.0f - frac) * s0 + frac * s1;
                    };
                float sampleFrame0 = getSample(wt3, frameIndex, v.readPosOsc3);
                float sampleFrame1 = getSample(wt3, frameIndex + 1, v.readPosOsc3);
                float voiceSample = (1.0f - frameFrac) * sampleFrame0 + frameFrac * sampleFrame1;
                float panAngle = pan * juce::MathConstants<float>::halfPi;
                finalLeft += voiceSample * std::cos(panAngle) * *oscGain3;
                finalRight += voiceSample * std::sin(panAngle) * *oscGain3;
                v.readPosOsc3 += voiceIncrement;
                if (v.readPosOsc3 >= 2048.0) v.readPosOsc3 -= 2048.0;
            }
        }

        // --- CÁLCULO DE CUTOFF MODULADO ---
        double baseCutoff = (pCutoff ? *pCutoff : 1000.0);
        if (pKeyTrack && *pKeyTrack)
            baseCutoff *= std::pow(2.0, (currentMidiNote - 60) / 12.0);
        const double envModulationDepth = 5.0;
        double modulationOctaves = (pEnvAmt ? *pEnvAmt : 0.0) * envVal * envModulationDepth;
        double fc = baseCutoff * std::pow(2.0, modulationOctaves);
        fc = juce::jlimit(20.0, 20000.0, fc);
        const double qUi = pQ ? juce::jlimit(0.0, 1.0, *pQ) : 0.7;
        const double q = (qUi <= 0.0 ? 1e-6 : qUi);

        // --- Filtrado y Salida ---
        float fl = processSVFLP(finalLeft, (float)fc, (float)q, svfL);
        float fr = processSVFLP(finalRight, (float)fc, (float)q, svfR);

        // **NOTA IMPORTANTE**: OSC 2 ya no se suma a la salida. Solo actúa como modulador.
        outputBuffer.addSample(0, sample, fl * gainCorrection * envVal);
        outputBuffer.addSample(1, sample, fr * gainCorrection * envVal);

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
                &filterCutoffHz, &filterQ, &filterEnvAmt, &keyTrack, &fmAmount, getSampleRate()
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
