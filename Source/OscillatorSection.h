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
        waveSelector.setLookAndFeel(&waveSelectorLookAndFeel);
        waveSelector.setJustificationType(juce::Justification::centredLeft);
        waveSelector.setColour(juce::ComboBox::backgroundColourId, juce::Colours::transparentBlack);
        waveSelector.setColour(juce::ComboBox::outlineColourId, juce::Colours::transparentBlack);
        waveSelector.setColour(juce::ComboBox::textColourId, juce::Colour::fromRGB(218, 222, 227));
        waveSelector.setColour(juce::ComboBox::arrowColourId, juce::Colour::fromRGB(218, 222, 227));
        waveSelector.setColour(juce::PopupMenu::backgroundColourId, juce::Colour::fromRGB(30, 33, 37));
        waveSelector.setColour(juce::PopupMenu::textColourId, juce::Colour::fromRGB(218, 222, 227));
        waveSelector.setColour(juce::PopupMenu::highlightedBackgroundColourId, juce::Colour::fromRGB(44, 48, 54));
        waveSelector.setColour(juce::PopupMenu::highlightedTextColourId, juce::Colour::fromRGB(218, 222, 227));
        waveSelector.onChange = [this]() { waveSelectorChanged(); };
    }

    ~OscillatorSection() override
    {
        waveSelector.setLookAndFeel(nullptr);
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
            DBG("No se encontro la carpeta wavetables o esta vacia: " << folderPath);
        }
    }

    void resized() override
    {
        waveSelector.setBounds(getLocalBounds());
    }

    bool selectWaveByFilename(const juce::String& fileNameWithExtension,
        juce::NotificationType notificationType = juce::sendNotificationSync)
    {
        for (size_t i = 0; i < waveFiles.size(); ++i)
        {
            const auto& file = waveFiles[i];
            if (file.getFileName().equalsIgnoreCase(fileNameWithExtension)
                || file.getFileNameWithoutExtension().equalsIgnoreCase(fileNameWithExtension))
            {
                waveSelector.setSelectedItemIndex((int)i, notificationType);
                return true;
            }
        }

        return false;
    }

private:
    struct MinimalComboBoxLookAndFeel : juce::LookAndFeel_V4
    {
        MinimalComboBoxLookAndFeel()
        {
            setColour(juce::PopupMenu::backgroundColourId, juce::Colour::fromRGB(30, 33, 37));
            setColour(juce::PopupMenu::textColourId, juce::Colour::fromRGB(218, 222, 227));
            setColour(juce::PopupMenu::highlightedBackgroundColourId, juce::Colour::fromRGB(52, 57, 64));
            setColour(juce::PopupMenu::highlightedTextColourId, juce::Colour::fromRGB(218, 222, 227));
        }

        void drawComboBox(juce::Graphics& g, int width, int height, bool /*isButtonDown*/,
            int buttonX, int buttonY, int buttonW, int buttonH, juce::ComboBox& box) override
        {
            juce::ignoreUnused(g, width, height, buttonX, buttonY, buttonW, buttonH, box);
        }

        void positionComboBoxText(juce::ComboBox& box, juce::Label& label) override
        {
            label.setBounds(box.getLocalBounds().withTrimmedLeft(6).withTrimmedRight(18));
            label.setJustificationType(juce::Justification::centredLeft);
            label.setColour(juce::Label::textColourId, box.findColour(juce::ComboBox::textColourId));
            label.setColour(juce::Label::backgroundColourId, juce::Colours::transparentBlack);
            label.setFont(juce::Font(15.0f));
        }

        juce::PopupMenu::Options getOptionsForComboBoxPopupMenu(juce::ComboBox& box, juce::Label& label) override
        {
            auto options = juce::LookAndFeel_V4::getOptionsForComboBoxPopupMenu(box, label);
            const auto scale = box.getApproximateScaleFactorForComponent(&box);
            const int boxWidth = juce::roundToInt(box.getWidth() * scale);
            const int boxHeight = juce::roundToInt(box.getHeight() * scale);
            const int targetWidth = juce::jlimit(70, 140, boxWidth > 0 ? boxWidth : juce::roundToInt(110 * scale));
            const int itemHeight = juce::jlimit(18, 28, boxHeight > 0 ? boxHeight : juce::roundToInt(24 * scale));
            const int numItems = box.getNumItems();

            options = options.withMinimumWidth(targetWidth)
                .withMaximumNumColumns(1)
                .withStandardItemHeight(itemHeight);

            if (numItems > 0)
            {
                const int desiredVisible = juce::jlimit(1, 10, numItems);
                auto screenBounds = box.getScreenBounds();
                auto popupArea = juce::Rectangle<int>(
                    screenBounds.getX(),
                    screenBounds.getBottom(),
                    targetWidth,
                    itemHeight * desiredVisible);

                if (auto* topLevel = box.getTopLevelComponent())
                {
                    auto pluginBounds = topLevel->getScreenBounds();
                    const int spaceBelow = juce::jmax(0, pluginBounds.getBottom() - screenBounds.getBottom());
                    const int spaceAbove = juce::jmax(0, screenBounds.getY() - pluginBounds.getY());
                    const int maxRowsBelow = itemHeight > 0 ? (spaceBelow / itemHeight) : desiredVisible;
                    const int maxRowsAbove = itemHeight > 0 ? (spaceAbove / itemHeight) : desiredVisible;

                    int visibleRows = desiredVisible;
                    bool openAbove = false;

                    if (maxRowsBelow >= desiredVisible)
                    {
                        visibleRows = desiredVisible;
                    }
                    else if (maxRowsBelow > 0 || maxRowsAbove > 0)
                    {
                        if (maxRowsAbove > maxRowsBelow)
                        {
                            openAbove = true;
                            visibleRows = juce::jlimit(1, desiredVisible, juce::jmax(1, maxRowsAbove));
                        }
                        else
                        {
                            visibleRows = juce::jlimit(1, desiredVisible, juce::jmax(1, maxRowsBelow));
                        }
                    }
                    else
                    {
                        visibleRows = 1;
                    }

                    popupArea.setHeight(itemHeight * visibleRows);
                    if (openAbove)
                        popupArea.setY(screenBounds.getY() - popupArea.getHeight());
                    else
                        popupArea.setY(screenBounds.getBottom());

                    popupArea.setX(juce::jlimit(pluginBounds.getX(), pluginBounds.getRight() - popupArea.getWidth(), popupArea.getX()));
                    popupArea.setY(juce::jlimit(pluginBounds.getY(), pluginBounds.getBottom() - popupArea.getHeight(), popupArea.getY()));
                    options = options.withParentComponent(topLevel);
                }

                options = options.withTargetScreenArea(popupArea);
            }
            return options;
        }
    };

    MinimalComboBoxLookAndFeel waveSelectorLookAndFeel;

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