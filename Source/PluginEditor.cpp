#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "LayoutConstants.h"

namespace
{
    constexpr int tabBarDesignHeight = 60; // Altura del área de pestañas en el diseño original
    constexpr int designInterfaceHeight = LayoutConstants::DESIGN_HEIGHT - LayoutConstants::KEYBOARD_HEIGHT;
    constexpr int designKeyboardSpace = LayoutConstants::KEYBOARD_HEIGHT + LayoutConstants::KEYBOARD_BOTTOM_MARGIN;
    constexpr int totalDesignHeight = designInterfaceHeight + designKeyboardSpace + tabBarDesignHeight;
}

NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p), audioProcessor(p),
    tabbedComponent(juce::TabbedButtonBar::Orientation::TabsAtTop),
    synthTab(p),
    chordMelodyTab(p),
    keyboardComponent(p.keyboardState, juce::MidiKeyboardComponent::horizontalKeyboard)
{
    addAndMakeVisible(tabbedComponent);
    addAndMakeVisible(keyboardComponent);

    tabbedComponent.addTab("Synthesizer", juce::Colours::black, &synthTab, false);
    tabbedComponent.addTab("Chord/Melody Generator", juce::Colours::black, &chordMelodyTab, false);

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
            float finalScale = 0.5f;
            const int choice = sizeComboBox.getSelectedId();
            if (choice == 1) finalScale = 0.375f;
            if (choice == 2) finalScale = 0.5f;

            const int newWidth = juce::roundToInt(LayoutConstants::DESIGN_WIDTH * finalScale);
            const int newHeight = juce::roundToInt(totalDesignHeight * finalScale);

            if (constrainer != nullptr)
                constrainer->setMinimumSize(newWidth, newHeight);
            if (auto* parent = getTopLevelComponent())
                parent->setSize(newWidth, newHeight);

            setSize(newWidth, newHeight);
        };

    const double aspectRatio = (double)LayoutConstants::DESIGN_WIDTH /
        (double)totalDesignHeight;

    const float defaultScale = 0.5f;
    const int defaultWidth = juce::roundToInt(LayoutConstants::DESIGN_WIDTH * defaultScale);
    const int defaultHeight = juce::roundToInt(totalDesignHeight * defaultScale);

    setSize(defaultWidth, defaultHeight);

    constrainer = std::make_unique<juce::ComponentBoundsConstrainer>();
    constrainer->setFixedAspectRatio(aspectRatio);
    constrainer->setMinimumSize(defaultWidth, defaultHeight);
    setConstrainer(constrainer.get());

    setResizable(true, true);
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

void NeuraSynthAudioProcessorEditor::resized()
{
    juce::Rectangle<int> totalArea = getLocalBounds();

    // 1. El teclado se posiciona abajo, como siempre
    const float currentScale = static_cast<float>(getWidth()) / LayoutConstants::DESIGN_WIDTH;
    const int keyboardHeight = juce::roundToInt(LayoutConstants::KEYBOARD_HEIGHT * currentScale);
    const int keyboardSpace = juce::roundToInt(designKeyboardSpace * currentScale);
    const int tabBarHeight = juce::roundToInt(tabBarDesignHeight * currentScale);
    auto keyboardSpaceArea = totalArea.removeFromBottom(keyboardSpace);
    auto keyboardArea = keyboardSpaceArea.removeFromBottom(keyboardHeight);
    keyboardComponent.setBounds(keyboardArea);

    tabbedComponent.setBounds(totalArea);

    const int sizeControlsWidth = 130;
    auto sizeControlsArea = totalArea.removeFromTop(tabBarHeight).removeFromRight(sizeControlsWidth);

    // 5. Reducimos el área un poco para que quede centrado y con márgenes.
    sizeControlsArea.reduce(8, 4); // <-- Reducimos un poco el margen horizontal

    // 6. Posicionamos nuestros controles dentro de esa área.
    sizeLabel.setBounds(sizeControlsArea.removeFromLeft(45)); // Damos un poco más al label
    sizeComboBox.setBounds(sizeControlsArea); // El ComboBox recibe el espacio extra

    // 7. (MUY IMPORTANTE) Traemos los controles al frente.
    sizeLabel.toFront(false);
    sizeComboBox.toFront(false);
}