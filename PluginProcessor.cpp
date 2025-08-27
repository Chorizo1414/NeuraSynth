// PluginProcessor.cpp

#include "PluginProcessor.h"
#include "PluginEditor.h"

// Inicializamos la frecuencia estática a 0
double SynthVoice::lastNoteFrequency = 0.0;

// DEFINICIÓN de setParameters(...) (va en el .cpp, no en el .h)
void SynthVoice::setParameters(juce::ADSR::Parameters& adsr,
    int* nf1, juce::AudioBuffer<float>* wavetable1, float* wavePos1, float* gain1, double* pitch1, float* pan1, float* spread1, double* detune1,
    int* nf2, juce::AudioBuffer<float>* wavetable2, float* wavePos2, float* gain2, double* pitch2, float* pan2, float* spread2, double* detune2,
    int* nf3, juce::AudioBuffer<float>* wavetable3, float* wavePos3, float* gain3, double* pitch3, float* pan3, float* spread3, double* detune3,
    double* cutoffHzPtr, double* qPtr, double* envAmtPtr, bool* keyTrackPtr, float* fmAmountPtr, float* lfoSpeedPtr, float* lfoAmountPtr,
    float* glideSecondsPtr, double sr)
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
    pGlideSeconds = glideSecondsPtr;

    sampleRateHz = sr;
}

// Render de la voz con filtro SVF TPT y modulación de cutoff (ENV + KeyTrack)
void SynthVoice::renderNextBlock(juce::AudioBuffer<float>& outputBuffer, int startSample, int numSamples)
{
    if (!isVoiceActive()) return;

    // --- Bucle principal muestra por muestra ---
    for (int sample = startSample; sample < startSample + numSamples; ++sample)
    {
        // --- LÓGICA DE GLIDE ---
        // Si la frecuencia actual no es la objetivo, la movemos un poco
        if (currentFrequency != targetFrequency)
        {
            // Calculamos cuánto movernos en este sample. Usamos un coeficiente para un slide suave.
            // Un valor más pequeño (ej. 0.0005f) da un glide más lento.
            const float glideCoefficient = 0.001f / (*pGlideSeconds + 0.001f);
            currentFrequency += (targetFrequency - currentFrequency) * glideCoefficient;
            
            // Si estamos muy cerca, simplemente saltamos al final para evitar errores de precisión
            if (std::abs(targetFrequency - currentFrequency) < 0.01)
            {
                currentFrequency = targetFrequency;
            }
        }

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
            double osc1Freq = currentFrequency * std::pow(2.0, *pitchShift1);
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

        // Frecuencias base de cada oscilador (¡AHORA USAN 'currentFrequency'!)
        double baseFreq1 = currentFrequency * std::pow(2.0, *pitchShift1) * lfoPitchFactor;
        double baseFreq2 = currentFrequency * std::pow(2.0, *pitchShift2) * lfoPitchFactor;
        double baseFreq3 = currentFrequency * std::pow(2.0, *pitchShift3) * lfoPitchFactor;

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

void NeuraSynthAudioProcessor::prepareToPlay(double sampleRate, int samplesPerBlock)
{
    // Guardamos las especificaciones del playback
    spec.sampleRate = sampleRate;
    spec.maximumBlockSize = samplesPerBlock;
    spec.numChannels = 2; // Estéreo
    
    // Preparamos nuestras cadenas de filtros con estas especificaciones
    leftTone.prepare(spec);
    rightTone.prepare(spec);

    // Preparamos el chorus
    chorus.prepare(spec);
    // Configuramos sus parámetros por defecto para un sonido clásico
    chorus.setRate(1.0f);      // Velocidad del LFO del chorus
    chorus.setDepth(0.25f);    // Profundidad de la modulación
    chorus.setCentreDelay(7.0f); // Retraso base en milisegundos
    chorus.setFeedback(0.2f);    // Retroalimentación para un sonido más denso
    chorus.setMix(0.0f);       // El efecto empieza apagado

    // Preparamos la reverb
    reverb.prepare(spec);
    reverb.setParameters(reverbParams);

    // Preparamos nuestros nuevos componentes
    preDelay.prepare(spec);
    leftReverbFilter.prepare(spec);
    rightReverbFilter.prepare(spec);
    
    // Coeficientes iniciales para los filtros (sonido vintage)
    // Cortamos graves debajo de 200Hz y agudos por encima de 5000Hz
    leftReverbFilter.get<0>().coefficients = juce::dsp::IIR::Coefficients<float>::makeHighPass(sampleRate, 200.0f);
    rightReverbFilter.get<0>().coefficients = juce::dsp::IIR::Coefficients<float>::makeHighPass(sampleRate, 200.0f);
    leftReverbFilter.get<1>().coefficients = juce::dsp::IIR::Coefficients<float>::makeLowPass(sampleRate, 5000.0f);
    rightReverbFilter.get<1>().coefficients = juce::dsp::IIR::Coefficients<float>::makeLowPass(sampleRate, 5000.0f);
    
    // Preparamos los componentes del Delay
    leftDelay.prepare(spec);
    rightDelay.prepare(spec);
    leftFeedbackFilter.prepare(spec);
    rightFeedbackFilter.prepare(spec);
    lfo.prepare(spec);
    lfo.setFrequency(0.5f); // Frecuencia lenta para el "wow"

    synth.setCurrentPlaybackSampleRate(sampleRate);
    for (int i = 0; i < synth.getNumVoices(); ++i)
        if (auto* voice = dynamic_cast<SynthVoice*>(synth.getVoice(i)))
            voice->setSampleRate(sampleRate);

    updateAllVoices();
}

void NeuraSynthAudioProcessor::releaseResources()
{
    reverb.reset();
}

void NeuraSynthAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages)
{
    buffer.clear();
    keyboardState.processNextMidiBuffer(midiMessages, 0, buffer.getNumSamples(), true);
    synth.renderNextBlock(buffer, midiMessages, 0, buffer.getNumSamples());

    // --- CADENA DE EFECTOS MASTER ---

    // --- 1. EFECTO DRIVE ---
    if (driveAmount > 0.0f)
    {
        float driveGain = juce::jmap(driveAmount, 0.0f, 1.0f, 1.0f, 3.0f);
        for (int channel = 0; channel < buffer.getNumChannels(); ++channel)
        {
            auto* channelData = buffer.getWritePointer(channel);
            for (int sample = 0; sample < buffer.getNumSamples(); ++sample)
            {
                float inputSample = channelData[sample] * driveGain;
                float distortedSample = std::tanh(inputSample);
                channelData[sample] = distortedSample * (1.0f / driveGain);
            }
        }
    }

    // --- 2. EFECTOS DE TONO (DARK/BRIGHT) ---
    juce::dsp::AudioBlock<float> block(buffer);
    auto leftBlock = block.getSingleChannelBlock(0);
    auto rightBlock = block.getSingleChannelBlock(1);
    juce::dsp::ProcessContextReplacing<float> leftContext(leftBlock);
    juce::dsp::ProcessContextReplacing<float> rightContext(rightBlock);
    leftTone.process(leftContext);
    rightTone.process(rightContext);

    // --- 3. EFECTO CHORUS ---
    juce::dsp::ProcessContextReplacing<float> chorusContext(block);
    chorus.process(chorusContext); // <-- Usamos el 'chorusContext', no el 'block' directamente.

    // --- 4. PROCESADO DE DELAY (SEMI-PARALELO CON FEEDBACK) ---
    juce::AudioBuffer<float> delayInputBuffer;
    delayInputBuffer.makeCopyOf(buffer);
    
    auto * leftChannel = buffer.getWritePointer(0);
    auto * rightChannel = buffer.getWritePointer(1);
    auto * leftDelayInput = delayInputBuffer.getReadPointer(0);
    auto * rightDelayInput = delayInputBuffer.getReadPointer(1);
    
       for (int sample = 0; sample < buffer.getNumSamples(); ++sample)
       {
           // Efecto Wow: modular el tiempo de delay con el LFO
           float lfoSample = lfo.processSample(0.0f);
           float wowEffect = lfoSample * delayWowDepth * 5.0f; // 5.0 = sensibilidad
           leftDelay.setDelay((delayTimeLeftMs + wowEffect) * getSampleRate() / 1000.0f);
           rightDelay.setDelay((delayTimeRightMs + wowEffect) * getSampleRate() / 1000.0f);
        
           // Leer la salida del delay
           float leftDelayed = leftDelay.popSample(0);
           float rightDelayed = rightDelay.popSample(1);
        
           // Señal de feedback: entrada actual + salida con feedback
           float leftFeedback = leftDelayInput[sample] + leftDelayed * delayFeedback;
           float rightFeedback = rightDelayInput[sample] + rightDelayed * delayFeedback;
        
           // Filtrar la señal de feedback
           // Procesamos la muestra a través de cada filtro de la cadena, uno por uno
           float leftFilteredFb = leftFeedbackFilter.get<1>().processSample(leftFeedbackFilter.get<0>().processSample(leftFeedback));
           float rightFilteredFb = rightFeedbackFilter.get<1>().processSample(rightFeedbackFilter.get<0>().processSample(rightFeedback));
        
           // Escribir la señal de feedback de vuelta en el delay
           leftDelay.pushSample(0, leftFilteredFb);
           rightDelay.pushSample(1, rightFilteredFb);
        
           // Mezcla final: Dry (entrada original) + Wet (salida del delay)
           leftChannel[sample] = leftDelayInput[sample] * delayDry + leftDelayed * delayWet;
           rightChannel[sample] = rightDelayInput[sample] * delayDry + rightDelayed * delayWet;
       }

    // --- 5. PROCESADO DE REVERB (EN PARALELO) ---
    // Creamos un buffer separado para la señal "wet" (procesada)
    juce::AudioBuffer<float> wetBuffer;
    wetBuffer.makeCopyOf(buffer);
    juce::dsp::AudioBlock<float> wetBlock(wetBuffer);
    
    // Procesamos el buffer "wet" con toda la cadena de reverb
    preDelay.process(juce::dsp::ProcessContextReplacing<float>(wetBlock));
    reverb.process(juce::dsp::ProcessContextReplacing<float>(wetBlock));
    
    auto leftWetBlock = wetBlock.getSingleChannelBlock(0);
    auto rightWetBlock = wetBlock.getSingleChannelBlock(1);
    leftReverbFilter.process(juce::dsp::ProcessContextReplacing<float>(leftWetBlock));
    rightReverbFilter.process(juce::dsp::ProcessContextReplacing<float>(rightWetBlock));
    
    // --- 6. MEZCLA DRY/WET Y MASTER GAIN ---
    // Aplicamos ganancia Dry al buffer original y Wet al procesado, y luego los sumamos.
    buffer.applyGain(reverbParams.dryLevel);
    buffer.addFrom(0, 0, wetBuffer, 0, 0, buffer.getNumSamples(), reverbParams.wetLevel);
    buffer.addFrom(1, 0, wetBuffer, 1, 0, buffer.getNumSamples(), reverbParams.wetLevel);
    
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
                &filterCutoffHz, &filterQ, &filterEnvAmt, &keyTrack, &fmAmount, &lfoSpeedHz, &lfoAmount, &glideSeconds, getSampleRate()
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

void NeuraSynthAudioProcessor::setGlide(float seconds)
{
    glideSeconds = seconds;
    updateAllVoices();
}

void NeuraSynthAudioProcessor::setDark(float amount)
{
    darkAmount = amount;
    // 'Dark' es un Low Shelf que CORTA agudos.
    // Mapeamos el knob (0 a 1) a una ganancia en decibelios (0dB a -6dB).
    auto gainDb = juce::jmap(darkAmount, 0.0f, 1.0f, 0.0f, 15.0f);

    // Calculamos los coeficientes del filtro y los actualizamos en nuestras cadenas.
    // Usamos una frecuencia fija (ej. 300 Hz) y un Q suave (0.7)
    leftTone.get<0>().coefficients = *juce::dsp::IIR::Coefficients<float>::makeLowShelf(spec.sampleRate, 300.0f, 0.7f, juce::Decibels::decibelsToGain(gainDb));
    rightTone.get<0>().coefficients = *leftTone.get<0>().coefficients;
}

void NeuraSynthAudioProcessor::setBright(float amount)
{
    brightAmount = amount;
    // 'Bright' es un High Shelf que AUMENTA agudos.
    // Mapeamos el knob (0 a 1) a una ganancia en decibelios (0dB a +6dB).
    auto gainDb = juce::jmap(brightAmount, 0.0f, 1.0f, 0.0f, 9.0f);

    // Calculamos los coeficientes del filtro y los actualizamos.
    // Usamos una frecuencia fija (ej. 4000 Hz) y un Q suave.
    leftTone.get<1>().coefficients = *juce::dsp::IIR::Coefficients<float>::makeHighShelf(spec.sampleRate, 4000.0f, 0.7f, juce::Decibels::decibelsToGain(gainDb));
    rightTone.get<1>().coefficients = *leftTone.get<1>().coefficients;
}

void NeuraSynthAudioProcessor::setDrive(float amount)
{
    driveAmount = amount;
    // Esto controlará una etapa de saturación en processBlock.
}

void NeuraSynthAudioProcessor::setChorus(bool isOn)
{
    chorusOn = isOn;
    // Cambiamos el nivel de mezcla del efecto
    // 0.0 = totalmente seco (apagado), 0.5 = mezcla 50/50
    chorus.setMix(isOn ? 0.5f : 0.0f);
}

void NeuraSynthAudioProcessor::setReverbDryLevel(float level) { reverbParams.dryLevel = level; reverb.setParameters(reverbParams); }
void NeuraSynthAudioProcessor::setReverbWetLevel(float level) { reverbParams.wetLevel = level; reverb.setParameters(reverbParams); }
void NeuraSynthAudioProcessor::setReverbRoomSize(float size) { reverbParams.roomSize = size; reverb.setParameters(reverbParams); }
void NeuraSynthAudioProcessor::setReverbDamping(float damping) { reverbParams.damping = damping; reverb.setParameters(reverbParams); }

void NeuraSynthAudioProcessor::setReverbPreDelay(float delay)
{
    // Mapeamos el valor del knob (0-1) a un rango de ms (0-500)
    float delayMs = juce::jmap(delay, 0.0f, 1.0f, 0.0f, 500.0f);
    preDelay.setDelay(getSampleRate() * delayMs / 1000.0f);
}

void NeuraSynthAudioProcessor::setReverbDiffusion(float diffusion)
{
    // Mapeamos "Diffusion" al parámetro "width" de la reverb. Es una buena aproximación.
    reverbParams.width = diffusion;
    reverb.setParameters(reverbParams);
}

void NeuraSynthAudioProcessor::setReverbDecay(float decay)
{
    // Mapeamos "Decay" al parámetro "roomSize", que controla el tiempo de la cola.
    reverbParams.roomSize = decay;
    reverb.setParameters(reverbParams);
}

// --- Setters de Delay ---
void NeuraSynthAudioProcessor::setDelayDry(float level) { delayDry = level; }
void NeuraSynthAudioProcessor::setDelayWet(float level) { delayWet = level; }
void NeuraSynthAudioProcessor::setDelayTimeLeft(float time) { delayTimeLeftMs = juce::jmap(time, 0.0f, 1.0f, 0.0f, 2000.0f); }
void NeuraSynthAudioProcessor::setDelayTimeRight(float time) { delayTimeRightMs = juce::jmap(time, 0.0f, 1.0f, 0.0f, 2000.0f); }
void NeuraSynthAudioProcessor::setDelayFeedback(float fb) { delayFeedback = juce::jlimit(0.0f, 0.98f, fb); } // Evitar auto-oscilación

void NeuraSynthAudioProcessor::setDelayLPFreq(float freq)
{
    delayLPFreq = juce::jmap(freq, 0.0f, 1.0f, 200.0f, 20000.0f);
    leftFeedbackFilter.get<1>().coefficients = juce::dsp::IIR::Coefficients<float>::makeLowPass(getSampleRate(), delayLPFreq);
    rightFeedbackFilter.get<1>().coefficients = juce::dsp::IIR::Coefficients<float>::makeLowPass(getSampleRate(), delayLPFreq);
}

void NeuraSynthAudioProcessor::setDelayHPFreq(float freq)
{
    delayHPFreq = juce::jmap(freq, 0.0f, 1.0f, 20.0f, 5000.0f);
    leftFeedbackFilter.get<0>().coefficients = juce::dsp::IIR::Coefficients<float>::makeHighPass(getSampleRate(), delayHPFreq);
    rightFeedbackFilter.get<0>().coefficients = juce::dsp::IIR::Coefficients<float>::makeHighPass(getSampleRate(), delayHPFreq);
}

void NeuraSynthAudioProcessor::setDelayWow(float depth) { delayWowDepth = depth; }


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
