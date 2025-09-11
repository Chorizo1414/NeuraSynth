#include <JuceHeader.h>
#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h" // <--- ¡AÑADE ESTA LÍNEA IMPORTANTE!

//==============================================================================
ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& p)
    : audioProcessor(p)
{
    // --- Botones principales ---
    addAndMakeVisible(createChordsButton);
    createChordsButton.onClick = [this] { createChords(); };

    addAndMakeVisible(generateMelodyButton);
    generateMelodyButton.onClick = [this] { generateMelody(); };

    // --- ComboBox para número de acordes ---
    addAndMakeVisible(chordCountCombo);
    chordCountCombo.addItem("Sin límite", 1);
    for (int i = 1; i <= 8; ++i)
        chordCountCombo.addItem(juce::String(i), i + 1);
    chordCountCombo.setSelectedId(1);

    // --- Botones de ritmo ---
    addAndMakeVisible(newRhythmButton);
    addAndMakeVisible(pauseButton);

    // --- Control de BPM ---
    addAndMakeVisible(bpmSlider);
    bpmSlider.setRange(40.0, 240.0, 1.0);
    bpmSlider.setValue(120.0);

    // --- Transposición ---
    addAndMakeVisible(transposeUpButton);
    transposeUpButton.onClick = [this]
        {
            ++transposition;
            transposeLabel.setText("Transposición: " + juce::String(transposition), juce::dontSendNotification);
        };

    addAndMakeVisible(transposeDownButton);
    transposeDownButton.onClick = [this]
        {
            --transposition;
            transposeLabel.setText("Transposición: " + juce::String(transposition), juce::dontSendNotification);
        };

    addAndMakeVisible(transposeLabel);
    transposeLabel.setText("Transposición: 0", juce::dontSendNotification);
    transposeLabel.setJustificationType(juce::Justification::centred);

    // --- Botones de reproducción ---
    addAndMakeVisible(playAllButton);
    addAndMakeVisible(playMelodyButton);

    // --- Etiqueta de resultados ---
    addAndMakeVisible(resultsLabel);
    resultsLabel.setFont(juce::Font(16.0f));
    resultsLabel.setJustificationType(juce::Justification::centredTop);
    resultsLabel.setColour(juce::Label::textColourId, juce::Colours::white);
}

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

void ChordMelodyTabComponent::resized()
{
    auto bounds = getLocalBounds().reduced(20);
    promptEditor.setBounds(bounds.removeFromTop(30));

    bounds.removeFromTop(10);

    auto createGenerateRow = bounds.removeFromTop(30);
    createChordsButton.setBounds(createGenerateRow.removeFromLeft(createGenerateRow.getWidth() / 2));
    generateMelodyButton.setBounds(createGenerateRow);
    bounds.removeFromTop(10);

    chordCountCombo.setBounds(bounds.removeFromTop(30));
    bounds.removeFromTop(10);

    auto rhythmRow = bounds.removeFromTop(30);
    newRhythmButton.setBounds(rhythmRow.removeFromLeft(rhythmRow.getWidth() / 2));
    pauseButton.setBounds(rhythmRow);
    bounds.removeFromTop(10);

    bpmSlider.setBounds(bounds.removeFromTop(40));
    bounds.removeFromTop(10);

    auto transposeRow = bounds.removeFromTop(30);
    transposeDownButton.setBounds(transposeRow.removeFromLeft(140));
    transposeUpButton.setBounds(transposeRow.removeFromRight(140));
    transposeLabel.setBounds(transposeRow);
    bounds.removeFromTop(10);

    auto playRow = bounds.removeFromTop(30);
    playAllButton.setBounds(playRow.removeFromLeft(playRow.getWidth() / 2));
    playMelodyButton.setBounds(playRow);
    bounds.removeFromTop(10);

    resultsLabel.setBounds(bounds);
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
    juce::String prompt = promptEditor.getText();
    if (prompt.isEmpty())
    {
        resultsLabel.setText("Please enter a prompt.", juce::dontSendNotification);
        return;
    }

    resultsLabel.setText("Generating melody...", juce::dontSendNotification);
    audioProcessor.pythonManager->generateMusicData(prompt);
    resultsLabel.setText("Melody generated.", juce::dontSendNotification);
}