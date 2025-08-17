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
    if (!isVoiceActive()) return;

    // --- PASO 1: Generar el audio de los 3 osciladores de forma INDEPENDIENTE ---

    // Pre-calculamos los incrementos base para cada oscilador
    double baseIncrement1 = (wt1 && wt1->getNumSamples() > 0) ? (frequency * std::pow(2.0, *pitchShift1)) / getSampleRate() * 2048.0 : 0.0;
    double baseIncrement2 = (wt2 && wt2->getNumSamples() > 0) ? (frequency * std::pow(2.0, *pitchShift2)) / getSampleRate() * 2048.0 : 0.0;
    double baseIncrement3 = (wt3 && wt3->getNumSamples() > 0) ? (frequency * std::pow(2.0, *pitchShift3)) / getSampleRate() * 2048.0 : 0.0;

    float gainCorrection = 1.0f / std::sqrt((float)numUnisonVoices);

    for (int sample = startSample; sample < startSample + numSamples; ++sample)
    {
        float envVal = env.getNextSample();
        float drySignalLeft = 0.0f;
        float drySignalRight = 0.0f;

        // Función genérica para obtener la muestra de un oscilador
        auto getOscSample = [&](juce::AudioBuffer<float>* wt, int numFrames, float wavePosition, double& readPos, double baseIncrement,
            float detune, float pan, float spread, float gain) -> std::pair<float, float>
            {
                if (!wt || wt->getNumSamples() == 0 || gain <= 0.0f) return { 0.0f, 0.0f };

                float oscLeft = 0.0f, oscRight = 0.0f;
                for (int i = 0; i < numUnisonVoices; ++i)
                {
                    auto& v = unisonVoices[i];
                    // Simulación simplificada para el ejemplo: usa la fase principal para todas las voces de unison
                    // una implementación completa requeriría fases separadas.
                }
                // Para simplificar, generamos una sola voz (mono) que luego paneamos
                float frameFloat = wavePosition * (numFrames > 1 ? numFrames - 1 : 0);
                int frameIndex = static_cast<int>(std::floor(frameFloat));
                float frameFrac = frameFloat - frameIndex;
                auto getSample = [&](int frame, double rPos) {
                    int pos0 = static_cast<int>(rPos); float frac = rPos - pos0;
                    float s0 = wt->getSample(0, (frame * 2048 + pos0) % wt->getNumSamples());
                    float s1 = wt->getSample(0, (frame * 2048 + ((pos0 + 1) % 2048)) % wt->getNumSamples());
                    return (1.0f - frac) * s0 + frac * s1;
                    };
                float sampleFrame0 = getSample(frameIndex, readPos);
                float sampleFrame1 = getSample(frameIndex + 1, readPos);
                float voiceSample = (1.0f - frameFrac) * sampleFrame0 + frameFrac * sampleFrame1;

                float panAngle = pan * juce::MathConstants<float>::halfPi;
                oscLeft = voiceSample * std::cos(panAngle) * gain;
                oscRight = voiceSample * std::sin(panAngle) * gain;

                readPos += baseIncrement;
                if (readPos >= 2048.0) readPos -= 2048.0;

                return { oscLeft, oscRight };
            };

        // Generar y sumar OSC 1
        auto osc1_out = getOscSample(wt1, *numFrames1, *wavePosition1, unisonVoices[0].readPosOsc1, baseIncrement1, *detuneOsc1, *panOsc1, *spreadOsc1, *oscGain1);
        drySignalLeft += osc1_out.first;
        drySignalRight += osc1_out.second;

        // Generar y sumar OSC 2
        auto osc2_out = getOscSample(wt2, *numFrames2, *wavePosition2, unisonVoices[0].readPosOsc2, baseIncrement2, *detuneOsc2, *panOsc2, *spreadOsc2, *oscGain2);
        drySignalLeft += osc2_out.first;
        drySignalRight += osc2_out.second;

        // Generar y sumar OSC 3
        auto osc3_out = getOscSample(wt3, *numFrames3, *wavePosition3, unisonVoices[0].readPosOsc3, baseIncrement3, *detuneOsc3, *panOsc3, *spreadOsc3, *oscGain3);
        drySignalLeft += osc3_out.first;
        drySignalRight += osc3_out.second;


        // --- PASO 2: Aplicar el EFECTO FM (Ring Modulation) a la señal mezclada ---
        float fmAmount = (pFmAmount ? *pFmAmount : 0.0f);
        float wetSignalLeft = 0.0f;
        float wetSignalRight = 0.0f;

        if (fmAmount != 0.0f)
        {
            // Usamos un LFO de seno simple como modulador. Su frecuencia podría ser un parámetro.
            // Por ahora, la atamos a la frecuencia de la nota para un efecto más musical.
            float lfoFreq = frequency * 2.0f; // Prueba a cambiar este multiplicador
            float lfoSample = std::sin(fmEffectLfoPhase);
            fmEffectLfoPhase += (lfoFreq / sampleRateHz) * juce::MathConstants<float>::twoPi;
            if (fmEffectLfoPhase >= juce::MathConstants<float>::twoPi) fmEffectLfoPhase -= juce::MathConstants<float>::twoPi;

            // Ring Modulation: multiplicamos la señal seca por la del LFO
            wetSignalLeft = drySignalLeft * lfoSample;
            wetSignalRight = drySignalRight * lfoSample;
        }

        // Mezclamos la señal seca y la procesada según el knob de FM
        // El knob ahora actúa como un control Dry/Wet
        float mixedSignalLeft = (drySignalLeft * (1.0f - std::abs(fmAmount))) + (wetSignalLeft * std::abs(fmAmount));
        float mixedSignalRight = (drySignalRight * (1.0f - std::abs(fmAmount))) + (wetSignalRight * std::abs(fmAmount));


        // --- PASO 3: La señal ya procesada pasa por el Filtro y la Envolvente ---
        double baseCutoff = (pCutoff ? *pCutoff : 20000.0);
        if (pKeyTrack && *pKeyTrack)
            baseCutoff *= std::pow(2.0, (currentMidiNote - 60) / 12.0);
        double modulationOctaves = (pEnvAmt ? *pEnvAmt : 0.0) * envVal * 5.0;
        double fc = baseCutoff * std::pow(2.0, modulationOctaves);
        fc = juce::jlimit(20.0, 20000.0, fc);
        const double q = (pQ ? juce::jlimit(0.1, 1.0, *pQ) : 0.707);

        float fl = processSVFLP(mixedSignalLeft, (float)fc, (float)q, svfL);
        float fr = processSVFLP(mixedSignalRight, (float)fc, (float)q, svfR);

        outputBuffer.addSample(0, sample, fl * envVal); // Corrección: gainCorrection ya no es necesario aquí
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
