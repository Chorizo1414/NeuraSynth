#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h" // Necesario para acceder a NeuraSynthAudioProcessor

//==============================================================================
// El constructor ahora usa 'NeuraSynthAudioProcessor&' y lo inicializa
ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor)
    : audioProcessor(processor) // Inicializamos la referencia al procesador
{
    // === CONFIGURACIÓN DEL EDITOR DE PROMPT ===
    promptLabel.setText("Escribe tu prompt aqui...", juce::dontSendNotification);
    promptLabel.setJustificationType(juce::Justification::topLeft);
    promptLabel.setColour(juce::Label::textColourId, juce::Colours::lightgrey);
    addAndMakeVisible(promptLabel);

    promptEditor.setMultiLine(true);
    promptEditor.setReturnKeyStartsNewLine(true);
    promptEditor.setColour(juce::TextEditor::backgroundColourId, juce::Colours::darkgrey.darker(0.8f));
    promptEditor.setColour(juce::TextEditor::textColourId, juce::Colours::white);
    promptEditor.setColour(juce::TextEditor::outlineColourId, juce::Colours::transparentBlack);
    addAndMakeVisible(promptEditor);

    // === CONFIGURACIÓN DE MENÚS DESPLEGABLES (COMBO BOX) ===
    genreLabel.setText("Genero", juce::dontSendNotification);
    genreLabel.setJustificationType(juce::Justification::centredLeft);
    genreLabel.setColour(juce::Label::textColourId, juce::Colours::lightgrey);
    addAndMakeVisible(genreLabel);

    addAndMakeVisible(genreComboBox);
    genreComboBox.addItemList({ "Pop", "Rock", "Jazz", "Lofi", "Reggaeton", "Techno" }, 1);
    genreComboBox.setSelectedId(1); // Pop por defecto
    genreComboBox.setColour(juce::ComboBox::backgroundColourId, juce::Colours::darkgrey);
    genreComboBox.setColour(juce::ComboBox::outlineColourId, juce::Colours::transparentBlack);

    sentimentLabel.setText("Sentimiento", juce::dontSendNotification);
    sentimentLabel.setJustificationType(juce::Justification::centredLeft);
    sentimentLabel.setColour(juce::Label::textColourId, juce::Colours::lightgrey);
    addAndMakeVisible(sentimentLabel);

    addAndMakeVisible(sentimentComboBox);
    sentimentComboBox.addItemList({ "Feliz", "Triste", "Energetico", "Relajado" }, 1);
    sentimentComboBox.setSelectedId(1); // Feliz por defecto
    sentimentComboBox.setColour(juce::ComboBox::backgroundColourId, juce::Colours::darkgrey);
    sentimentComboBox.setColour(juce::ComboBox::outlineColourId, juce::Colours::transparentBlack);

    // === CONFIGURACIÓN DE BOTONES ===
    auto setupButton = [&](juce::TextButton& button, const juce::String& text, const juce::Colour& colour)
        {
            button.setButtonText(text);
            button.setColour(juce::TextButton::buttonColourId, colour);
            button.setColour(juce::TextButton::textColourOnId, juce::Colours::white);
            button.setColour(juce::TextButton::buttonOnColourId, colour.brighter(0.2f));
            addAndMakeVisible(button);
        };

    setupButton(generateButton, "Generar", juce::Colour(0xff8a2be2)); // Azul violeta
    setupButton(playButton, "Reproducir", juce::Colour(0xff4c2a75));
    setupButton(stopButton, "Pausar", juce::Colour(0xff4c2a75));
    setupButton(exportButton, "Exportar MIDI", juce::Colour(0xff4c2a75));

    // === CONFIGURACIÓN DEL PIANO ROLL (VISUAL) ===
    addAndMakeVisible(pianoRollComponent);

    // Conectar el botón de generar a la funcionalidad
    generateButton.onClick = [this] {
        juce::String prompt = promptEditor.getText();
        juce::String genre = genreComboBox.getText();
        juce::String sentiment = sentimentComboBox.getText();

        // Usamos audioProcessor para acceder al pythonManager
        juce::StringArray generatedChords = audioProcessor.pythonManager->generateChordProgression(prompt, genre, sentiment);

        DBG("Acordes generados: " + generatedChords.joinIntoString(", "));
        };
}

ChordMelodyTabComponent::~ChordMelodyTabComponent()
{
}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    // Fondo oscuro, similar al de tu app de Python
    g.fillAll(juce::Colour(0xff282c34));

    // Dibuja un borde alrededor del piano roll para visualizarlo
    g.setColour(juce::Colours::darkgrey);
    g.drawRect(pianoRollComponent.getBounds(), 1.0f);
}

void ChordMelodyTabComponent::resized()
{
    auto bounds = getLocalBounds().reduced(20);

    // === ÁREA SUPERIOR: PROMPT Y CONTROLES DE GENERACIÓN ===
    auto topArea = bounds.removeFromTop(120);
    promptLabel.setBounds(topArea.removeFromTop(25));

    auto promptArea = topArea.removeFromLeft(topArea.getWidth() * 0.6);
    promptEditor.setBounds(promptArea.reduced(0, 5));

    topArea.removeFromLeft(20);

    auto controlsArea = topArea;
    genreLabel.setBounds(controlsArea.removeFromTop(20));
    genreComboBox.setBounds(controlsArea.removeFromTop(30));
    controlsArea.removeFromTop(10);
    sentimentLabel.setBounds(controlsArea.removeFromTop(20));
    sentimentComboBox.setBounds(controlsArea.removeFromTop(30));

    // === BOTÓN DE GENERAR ===
    bounds.removeFromTop(20);
    generateButton.setBounds(bounds.removeFromTop(40).reduced(getWidth() * 0.2, 0));

    // === ÁREA DEL PIANO ROLL ===
    bounds.removeFromTop(20);
    auto pianoRollArea = bounds.removeFromTop(bounds.getHeight() - 60);
    pianoRollComponent.setBounds(pianoRollArea);

    // === BOTONES INFERIORES ===
    bounds.removeFromTop(20);
    auto bottomButtonsArea = bounds.removeFromBottom(40);

    auto buttonWidth = bottomButtonsArea.getWidth() / 3;
    playButton.setBounds(bottomButtonsArea.removeFromLeft(buttonWidth).reduced(5, 0));
    stopButton.setBounds(bottomButtonsArea.removeFromLeft(buttonWidth).reduced(5, 0));
    exportButton.setBounds(bottomButtonsArea.removeFromLeft(buttonWidth).reduced(5, 0));
}