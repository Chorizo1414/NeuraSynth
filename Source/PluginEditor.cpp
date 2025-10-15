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
    sizeComboBox.setSelectedId(2);
    sizeComboBox.setTooltip("Escala la interfaz del sintetizador");
    sizeComboBox.setJustificationType(juce::Justification::centred);

    sizeComboBox.onChange = [this]
        {
            if (auto* parent = getTopLevelComponent())
            {
                float finalScale = 0.5f;
                int choice = sizeComboBox.getSelectedId();
                if (choice == 1) finalScale = 0.375f;
                if (choice == 2) finalScale = 0.5f;

                const int newWidth = LayoutConstants::DESIGN_WIDTH * finalScale;
                const int newHeight = LayoutConstants::DESIGN_HEIGHT * finalScale;

                constrainer->setMinimumSize(newWidth, newHeight);
                parent->setSize(newWidth, newHeight);
            }
        };

    const double aspectRatio = (double)LayoutConstants::DESIGN_WIDTH / LayoutConstants::DESIGN_HEIGHT;
    setSize(LayoutConstants::DESIGN_WIDTH * 0.5, LayoutConstants::DESIGN_HEIGHT * 0.5);

    constrainer = std::make_unique<juce::ComponentBoundsConstrainer>();
    constrainer->setFixedAspectRatio(aspectRatio);
    setConstrainer(constrainer.get());

    setResizable(true, true);
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