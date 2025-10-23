#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "LayoutConstants.h"

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
    sizeComboBox.addItem("75%", 1);
    sizeComboBox.addItem("100%", 2);
    sizeComboBox.setSelectedId(2, juce::dontSendNotification);
    sizeComboBox.setTooltip("Escala la interfaz del sintetizador");
    sizeComboBox.setJustificationType(juce::Justification::centred);

    const double aspectRatio = (double)LayoutConstants::DESIGN_WIDTH / LayoutConstants::DESIGN_HEIGHT;
    constrainer = std::make_unique<juce::ComponentBoundsConstrainer>();
    constrainer->setFixedAspectRatio(aspectRatio);
    setConstrainer(constrainer.get());

    setResizable(true, false);

    constexpr float baseScale = 0.5f;
    auto applyScale = [this, baseScale](float multiplier)
        {
            const float finalScale = baseScale * multiplier;
            const int newWidth = juce::roundToInt(LayoutConstants::DESIGN_WIDTH * finalScale);
            const int newHeight = juce::roundToInt(LayoutConstants::DESIGN_HEIGHT * finalScale);

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
            float multiplier = 1.0f;
            switch (sizeComboBox.getSelectedId())
            {
            case 1: multiplier = 0.75f; break;
            case 2: default: multiplier = 1.0f; break;
            }

            applyScale(multiplier);
        };

    applyScale(sizeComboBox.getSelectedId() == 1 ? 0.75f : 1.0f);
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