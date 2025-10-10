#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "LayoutConstants.h"

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
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

void NeuraSynthAudioProcessorEditor::resized()
{
    juce::Rectangle<int> totalArea = getLocalBounds();

    // 1. El teclado se posiciona abajo, como siempre
    const double designKeyboardHeight = 120.0;
    const double totalDesignHeight = LayoutConstants::DESIGN_HEIGHT;
    int keyboardHeight = static_cast<int>(getHeight() * (designKeyboardHeight / totalDesignHeight));
    auto keyboardArea = totalArea.removeFromBottom(keyboardHeight);
    keyboardComponent.setBounds(keyboardArea);

    // 2. El TabbedComponent ocupa TODO el espacio superior restante
    tabbedComponent.setBounds(totalArea);

    // 3. Posicionamos los controles MANUALMENTE sobre la barra de pestañas
    const int tabBarHeight = 30;

    // 4. Creamos un área en la esquina superior derecha.
    //    Le damos un poco más de ancho total.
    const int sizeControlsWidth = 130; // <-- Aumentamos de 120 a 130
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