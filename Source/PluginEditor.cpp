#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "LayoutConstants.h"

#include <array>

NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p),
    tabbedComponent(juce::TabbedButtonBar::Orientation::TabsAtTop),
    synthTab(p),
    chordMelodyTab(p)
{
    tabbedComponent.setLookAndFeel(&customLookAndFeel);
    addAndMakeVisible(tabbedComponent);

    tabbedComponent.addTab("Synthesizer", juce::Colours::transparentBlack, &synthTab, false);
    tabbedComponent.addTab("Chord/Melody Generator", juce::Colours::transparentBlack, &chordMelodyTab, false);

    addAndMakeVisible(sizeLabel);
    sizeLabel.setText("Size:", juce::dontSendNotification);
    sizeLabel.setJustificationType(juce::Justification::centredRight);
    sizeLabel.setColour(juce::Label::textColourId, juce::Colours::lightgrey);

    addAndMakeVisible(sizeComboBox);

    struct ScaleOption
    {
        int id;
        juce::String label;
        int width;
        int height;
    };

    const std::array<ScaleOption, 3> scaleOptions{ {
        { 1, "75%", 900, 560 },
        { 2, "100%", 1000, 650 },
        { 3, "125%", 1200, 700 },
    } };

    for (const auto& option : scaleOptions)
        sizeComboBox.addItem(option.label, option.id);

    sizeComboBox.setSelectedId(2, juce::dontSendNotification);
    sizeComboBox.setTooltip("Escala la interfaz del sintetizador");
    sizeComboBox.setJustificationType(juce::Justification::centred);

    const double aspectRatio = (double)scaleOptions[1].width / scaleOptions[1].height;
    constrainer = std::make_unique<juce::ComponentBoundsConstrainer>();
    constrainer->setFixedAspectRatio(aspectRatio);
    setConstrainer(constrainer.get());

    setResizable(true, false);

    auto applyScale = [this, scaleOptions](int selectedId)
        {
            const ScaleOption* chosen = &scaleOptions[1];

            for (const auto& option : scaleOptions)
            {
                if (option.id == selectedId)
                {
                    chosen = &option;
                    break;
                }
            }

            const int newWidth = chosen->width;
            const int newHeight = chosen->height;

            // setResizeLimits() asserts in the JUCE debug runtime when there's no
            // host-managed resizer, so we clamp via the shared constrainer instead.
            if (constrainer != nullptr)
                constrainer->setSizeLimits(newWidth, newHeight, newWidth, newHeight);

            setSize(newWidth, newHeight);

            if (auto* parent = getTopLevelComponent())
            {
                if (parent != this)
                    parent->setSize(newWidth, newHeight);
            }
        };

    sizeComboBox.onChange = [this, applyScale]
        {
            applyScale(sizeComboBox.getSelectedId());
        };

    applyScale(sizeComboBox.getSelectedId());
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
    tabbedComponent.setLookAndFeel(nullptr);
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

void NeuraSynthAudioProcessorEditor::resized()
{
    // El TabbedComponent ocupa TODA la ventana.
    tabbedComponent.setBounds(getLocalBounds());

    // Posicionamos los controles de tamaño manualmente sobre la barra de pestañas.
    const int tabBarHeight = 35;
    const int sizeControlsWidth = 130;
    auto topArea = getLocalBounds();
    auto sizeControlsArea = topArea.removeFromTop(tabBarHeight).removeFromRight(sizeControlsWidth);

    sizeControlsArea.reduce(8, 4);
    sizeLabel.setBounds(sizeControlsArea.removeFromLeft(45));
    sizeComboBox.setBounds(sizeControlsArea);

    sizeLabel.toFront(false);
    sizeComboBox.toFront(false);
}