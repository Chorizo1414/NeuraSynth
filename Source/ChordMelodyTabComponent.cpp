#include <JuceHeader.h>
#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h" // <--- ¡AÑADE ESTA LÍNEA IMPORTANTE!

//==============================================================================
ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& p)
    : audioProcessor(p)
{
    // Prompt
    addAndMakeVisible(promptLabel);
    promptLabel.setText("Prompt:", juce::dontSendNotification);
    promptLabel.setColour(juce::Label::textColourId, juce::Colours::white);

    addAndMakeVisible(promptEditor);
    promptEditor.setText("reggaeton en Eb major");
    promptEditor.setMultiLine(false);
    promptEditor.setReturnKeyStartsNewLine(false);
    // Número de acordes
    addAndMakeVisible(numChordsLabel);
    // Evitar caracteres no ASCII para prevenir aserciones de JUCE
    numChordsLabel.setText("Num Acordes:", juce::dontSendNotification);
    numChordsLabel.setColour(juce::Label::textColourId, juce::Colours::white);

    addAndMakeVisible(numChordsBox);
    numChordsBox.addItem("Sin limite", 1);
    for (int i = 1; i <= 16; ++i)
        numChordsBox.addItem(juce::String(i), i + 1);
    numChordsBox.setSelectedId(1);

    // Botones de ritmo y pausa
    addAndMakeVisible(newRhythmButton);
    addAndMakeVisible(pauseButton);

    // Control de BPM
    addAndMakeVisible(bpmLabel);
    bpmLabel.setText("BPM:", juce::dontSendNotification);
    bpmLabel.setColour(juce::Label::textColourId, juce::Colours::white);

    addAndMakeVisible(bpmSlider);
    bpmSlider.setRange(40.0, 200.0, 1.0);
    bpmSlider.setValue(95.0);
    bpmSlider.setSliderStyle(juce::Slider::LinearHorizontal);
    bpmSlider.setTextBoxStyle(juce::Slider::TextBoxLeft, false, 50, 20);

    // Botones de acción
    addAndMakeVisible(createChordsButton);
    createChordsButton.onClick = [this] { createChords(); };

    addAndMakeVisible(generateMelodyButton);
    generateMelodyButton.onClick = [this] { generateMelody(); };

    addAndMakeVisible(playAllButton);
    playAllButton.onClick = [this] { playAll(); };

    addAndMakeVisible(transposeUpButton);
    transposeUpButton.onClick = [this] { transpose(true); };

    addAndMakeVisible(transposeDownButton);
    transposeDownButton.onClick = [this] { transpose(false); };

    addAndMakeVisible(playMelodyButton);
    playMelodyButton.onClick = [this] { playMelody(); };

    // Área de resultados
        
    // El marcador de posicion no pinta nada, asi que no debe ser opaco
    pianoRollPlaceholder.setOpaque(false);

    addAndMakeVisible(resultsLabel);
    resultsLabel.setColour(juce::Label::textColourId, juce::Colours::white);
    resultsLabel.setJustificationType(juce::Justification::centred);
}

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
    g.setColour(juce::Colours::darkgrey);
    g.drawRect(pianoRollPlaceholder.getBounds());
}

void ChordMelodyTabComponent::resized()
{
    auto area = getLocalBounds().reduced(10);

    auto topRow = area.removeFromTop(25);
    promptLabel.setBounds(topRow.removeFromLeft(60));
    promptEditor.setBounds(topRow.removeFromLeft(300));

    area.removeFromTop(5);
    auto controlRow = area.removeFromTop(40);
    numChordsLabel.setBounds(controlRow.removeFromLeft(90));
    numChordsBox.setBounds(controlRow.removeFromLeft(100));
    newRhythmButton.setBounds(controlRow.removeFromLeft(100));
    pauseButton.setBounds(controlRow.removeFromLeft(80));
    bpmLabel.setBounds(controlRow.removeFromLeft(40));
    bpmSlider.setBounds(controlRow.removeFromLeft(150));
    createChordsButton.setBounds(controlRow.removeFromLeft(110));
    generateMelodyButton.setBounds(controlRow.removeFromLeft(130));
    playAllButton.setBounds(controlRow.removeFromLeft(130));
    transposeUpButton.setBounds(controlRow.removeFromLeft(130));
    transposeDownButton.setBounds(controlRow.removeFromLeft(130));
    playMelodyButton.setBounds(controlRow.removeFromLeft(150));

    area.removeFromTop(10);
    pianoRollPlaceholder.setBounds(area);
    resultsLabel.setBounds(area);
}

void ChordMelodyTabComponent::createChords()
{
    juce::String prompt = promptEditor.getText();
    if (prompt.isEmpty())
    {
        resultsLabel.setText("Please enter a prompt.", juce::dontSendNotification);
        return;
    }
    
    resultsLabel.setText("Generating...", juce::dontSendNotification);
    juce::StringArray chords = audioProcessor.pythonManager->generateChordProgression(prompt);
    
    if (chords.isEmpty())
    
        resultsLabel.setText("Failed to generate chords.", juce::dontSendNotification);
    
    else
    
        resultsLabel.setText(chords.joinIntoString(" - "), juce::dontSendNotification);
    
}

void ChordMelodyTabComponent::generateMelody()
{
    // Stub: implementacion futura
    resultsLabel.setText(resultsLabel.getText() + "\n[Melodia pendiente]", juce::dontSendNotification);
}

void ChordMelodyTabComponent::playAll() {}

void ChordMelodyTabComponent::playMelody() {}

void ChordMelodyTabComponent::transpose(bool up)
{
    juce::String txt = up ? "Transponer +1" : "Transponer -1";
    DBG(txt);
}