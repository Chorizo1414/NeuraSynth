#pragma once

#include <JuceHeader.h>
#include "PluginProcessor.h"
#include "SynthTabComponent.h"
#include "ChordMelodyTabComponent.h"
#include "CustomLookAndFeel.h"

#include <array>

class NeuraSynthAudioProcessorEditor : public juce::AudioProcessorEditor
{
public:
    NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor&);
    ~NeuraSynthAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;
	void globalScaleFactorChanged() override;

private:
    NeuraSynthAudioProcessor& audioProcessor;

    juce::TabbedComponent tabbedComponent;
    SynthTabComponent synthTab;
    ChordMelodyTabComponent chordMelodyTab;

    juce::Label sizeLabel;
    juce::ComboBox sizeComboBox;

    std::unique_ptr<juce::ComponentBoundsConstrainer> constrainer;
    CustomLookAndFeel customLookAndFeel;

    struct ScaleOption
    {
        int id{};
        juce::String label;
        int width{};
    };

    static const std::array<ScaleOption, 3> scaleOptions;

    ScaleOption currentScaleOption{};
    bool isApplyingStoredSize = false;

    void initialiseEditorSizeFromProcessor();
    void applyScaleOption(int optionId, bool updateComboBoxSelection);
    const ScaleOption* findScaleOptionById(int optionId) const;
    juce::Rectangle<int> calculateEditorBoundsForOption(const ScaleOption& option) const;
    void refreshParentConstraints(const juce::Rectangle<int>& targetBounds);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(NeuraSynthAudioProcessorEditor)
};
