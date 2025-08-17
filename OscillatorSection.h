#pragma once
#include <JuceHeader.h>
#include "WaveformDisplay.h"

class OscillatorSection : public juce::Component
{
public:
    std::function<void(const juce::AudioBuffer<float>&)> onWaveLoaded;

    OscillatorSection()
    {
        addAndMakeVisible(waveSelector);
        waveSelector.setWantsKeyboardFocus(false);
        waveSelector.onChange = [this]() { waveSelectorChanged(); };
    }

    void loadWavetablesFromFolder(const juce::String& folderPath)
    {
        waveSelector.clear();
        waveFiles.clear();

        juce::File waveFolder(folderPath);
        if (waveFolder.exists() && waveFolder.isDirectory())
        {
            auto foundFiles = waveFolder.findChildFiles(juce::File::TypesOfFileToFind::findFiles, false, "*.wav");
            int itemId = 1;
            for (auto& f : foundFiles)
            {
                waveFiles.push_back(f);
                auto waveName = f.getFileNameWithoutExtension();
                waveSelector.addItem(waveName, itemId++);
            }
            if (!waveFiles.empty())
                waveSelector.setSelectedId(1);
        }
        else
        {
            DBG("No se encontró la carpeta wavetables o está vacía: " << folderPath);
        }
    }

    void resized() override
    {
        waveSelector.setBounds(getLocalBounds());
    }

private:
    juce::ComboBox waveSelector;
    std::vector<juce::File> waveFiles;

    void waveSelectorChanged()
    {
        int selectedIndex = waveSelector.getSelectedItemIndex();
        if (selectedIndex >= 0 && selectedIndex < (int)waveFiles.size())
        {
            auto file = waveFiles[selectedIndex];
            DBG("Oscillator wave changed to: " << file.getFullPathName());

            juce::WavAudioFormat wavFormat;
            auto inputStream = file.createInputStream();
            if (inputStream != nullptr)
            {
                std::unique_ptr<juce::AudioFormatReader> reader(wavFormat.createReaderFor(inputStream.release(), true));
                if (reader != nullptr)
                {
                    juce::AudioBuffer<float> wavetableBuffer;
                    wavetableBuffer.setSize((int)reader->numChannels, (int)reader->lengthInSamples);
                    reader->read(&wavetableBuffer, 0, (int)reader->lengthInSamples, 0, true, true);

                    if (onWaveLoaded)
                        onWaveLoaded(wavetableBuffer);
                }
            }
        }
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(OscillatorSection)
};