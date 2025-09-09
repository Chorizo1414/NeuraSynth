// WaveformDisplay.h
#pragma once
#include <JuceHeader.h>

class WaveformDisplay : public juce::Component
{
public:
    WaveformDisplay() {}
    ~WaveformDisplay() override {}

    void setAudioBuffer(const juce::AudioBuffer<float>& buffer, int newNumFrames)
    {
        audioBuffer.makeCopyOf(buffer);
        numFrames = newNumFrames;
        if (numFrames > 0)
            frameSize = audioBuffer.getNumSamples() / numFrames;

        recalcPath();
    }

    void setDisplayPosition(float newPosition)
    {
        currentPosition = newPosition;
        recalcPath();
    }

    void paint(juce::Graphics& g) override
    {
        g.fillAll(juce::Colours::black);
        g.setColour(juce::Colours::white);
        g.strokePath(waveformPath, juce::PathStrokeType(1.0f));
    }

    void resized() override
    {
        recalcPath();
    }

private:
    juce::Path waveformPath;
    juce::AudioBuffer<float> audioBuffer; // Buffer almacenado

    float currentPosition = 0.0f;
    int numFrames = 256;
    int frameSize = 0;

    void recalcPath()
    {
        waveformPath.clear();
        if (audioBuffer.getNumSamples() == 0 || getWidth() <= 0 || getHeight() <= 0 || frameSize <= 0)
        {
            repaint();
            return;
        }

        // --- LICA MODIFICADA ---
        // 1. Calcular qu	 frame dibujar
        float frameFloat = currentPosition * (numFrames - 1);
        int frameIndex = static_cast<int>(std::floor(frameFloat));

        // 2. Encontrar el punto de inicio de ese frame en el buffer
        int startSample = frameIndex * frameSize;

        // 3. Asegurarnos de no salirnos del buffer
        if (startSample + frameSize > audioBuffer.getNumSamples())
        {
            repaint();
            return;
        }

        auto* readPtr = audioBuffer.getReadPointer(0, startSample);
        int numSamplesToShow = frameSize;

        // 1) Hallar amplitud mxima en ese rango
        float maxAmp = 0.0f;
        for (int i = 0; i < numSamplesToShow; ++i)
            maxAmp = std::max(maxAmp, std::abs(readPtr[i]));

        if (maxAmp < 1e-9f) maxAmp = 1.0f;
        // 2) Factor de escala vertical (menos de 1.0 para dejar margen)
        float scaleFactor = 0.8f;  // Ajusta a tu gusto

        waveformPath.startNewSubPath(0.0f, getHeight() * 0.5f);

        for (int i = 0; i < numSamplesToShow; ++i)
        {
            float x = juce::jmap<float>((float)i, 0.0f, (float)(numSamplesToShow - 1),
                0.0f, (float)getWidth());

            // Normalizamos la muestra
            float sample = readPtr[i] / maxAmp;

            // 3) Aplicar factor de escala para no ocupar el 100% de la altura
            float y = getHeight() * 0.5f - sample * (getHeight() * 0.5f * scaleFactor);

            waveformPath.lineTo(x, y);
        }
        repaint();
    }




    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(WaveformDisplay)
};
