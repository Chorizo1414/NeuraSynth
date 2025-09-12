#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h"

ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor)
    : audioProcessor(processor)
{
    // === EDITOR DE PROMPT ===
    addAndMakeVisible(promptLabel);
    promptLabel.setText("Escribe tu prompt aqui (ej: 'pop en C mayor', 'lofi triste en Am')", juce::dontSendNotification);

    addAndMakeVisible(promptEditor);
    promptEditor.setMultiLine(true);

    // === MENÚ DE GÉNERO ===
    addAndMakeVisible(genreLabel);
    genreLabel.setText("Genero (Opcional, si no se especifica en el prompt)", juce::dontSendNotification);

    addAndMakeVisible(genreComboBox);
    // Llenamos con los géneros de tu archivo generos.py
    genreComboBox.addItemList({ "Pop", "Rock", "Jazz", "Lofi", "Reggaeton", "Techno", "R&B", "Vals" }, 1);
    genreComboBox.setSelectedId(0); // Ninguno por defecto

    // === BOTONES DE GENERACIÓN ===
    addAndMakeVisible(generateChordsButton);
    generateChordsButton.setButtonText("1. Generar Acordes");

    addAndMakeVisible(generateMelodyButton);
    generateMelodyButton.setButtonText("2. Generar Melodia");
    generateMelodyButton.setEnabled(false); // Deshabilitado hasta que haya acordes

    // === BOTONES DE CONTROL ===
    addAndMakeVisible(playButton);
    playButton.setButtonText("Reproducir");
    addAndMakeVisible(stopButton);
    stopButton.setButtonText("Pausar");
    addAndMakeVisible(exportButton);
    exportButton.setButtonText("Exportar MIDI");

    // === PIANO ROLL ===
    addAndMakeVisible(pianoRollComponent);

    // === LÓGICA DE LOS BOTONES ===
    generateChordsButton.onClick = [this]
        {
            juce::String prompt = promptEditor.getText();
            if (prompt.isEmpty()) return;

            // Llamamos a la función de Python
            lastGeneratedChordsData = audioProcessor.pythonManager->generateMusicData(prompt);

            // --- LÓGICA DE VERIFICACIÓN MEJORADA ---
            if (lastGeneratedChordsData.empty())
            {
                DBG("Error: Python devolvio un diccionario vacio.");
                return;
            }

            // Verificamos si la clave "error" existe y si su contenido no está vacío
            if (lastGeneratedChordsData.contains("error"))
            {
                std::string errorMessage = lastGeneratedChordsData["error"].cast<std::string>();
                if (!errorMessage.empty())
                {
                    // Si hay un mensaje de error, lo mostramos en la consola de JUCE
                    DBG("!!! Error desde Python: " + juce::String(errorMessage));
                    return; // Detenemos la ejecución
                }
            }

            // Si llegamos aquí, todo salió bien
            DBG("Acordes generados desde Python con exito!");
            pianoRollComponent.setMusicData(lastGeneratedChordsData);
            generateMelodyButton.setEnabled(true);

            // Forzamos un redibujado de este componente y todos sus hijos (incluyendo el piano roll)
            repaint();
        };

    generateMelodyButton.onClick = [this]
        {
            if (lastGeneratedChordsData.empty()) return;

            // Extraemos los datos necesarios del diccionario de acordes
            py::list chords = lastGeneratedChordsData["acordes"];
            py::list rhythm = lastGeneratedChordsData["ritmo"];
            juce::String root = lastGeneratedChordsData["raiz"].cast<std::string>();
            juce::String mode = lastGeneratedChordsData["modo"].cast<std::string>();

            // Llamamos a la función de Python para generar la melodía
            auto melodyData = audioProcessor.pythonManager->generateMelodyData(chords, rhythm, root, mode);

            if (!melodyData.empty() && !melodyData.contains("error"))
            {
                // Combinamos los datos de acordes y melodía y los enviamos al piano roll
                py::dict combinedData;
                combinedData["acordes"] = lastGeneratedChordsData["acordes"];
                combinedData["melodia"] = melodyData["melodia"];

                pianoRollComponent.setMusicData(combinedData);
                DBG("Melodia generada y visualizada!");
            }
            else {
                DBG("Error al generar la melodia desde Python.");
            }
        };
}

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff282c34));
}

void ChordMelodyTabComponent::resized()
{
    auto bounds = getLocalBounds().reduced(20);

    auto topArea = bounds.removeFromTop(100);
    auto promptArea = topArea.removeFromLeft(topArea.getWidth() * 0.7);
    promptLabel.setBounds(promptArea.removeFromTop(20));
    promptEditor.setBounds(promptArea);

    topArea.removeFromLeft(20);
    auto controlsArea = topArea;
    genreLabel.setBounds(controlsArea.removeFromTop(40));
    genreComboBox.setBounds(controlsArea.removeFromTop(30));

    bounds.removeFromTop(10);
    auto generationButtonsArea = bounds.removeFromTop(40);
    generateChordsButton.setBounds(generationButtonsArea.removeFromLeft(generationButtonsArea.getWidth() / 2).reduced(5, 0));
    generateMelodyButton.setBounds(generationButtonsArea.reduced(5, 0));

    bounds.removeFromTop(10);
    pianoRollComponent.setBounds(bounds.removeFromTop(bounds.getHeight() - 60));

    bounds.removeFromTop(10);
    auto bottomButtonsArea = bounds.removeFromBottom(40);
    playButton.setBounds(bottomButtonsArea.removeFromLeft(bottomButtonsArea.getWidth() / 3).reduced(5, 0));
    stopButton.setBounds(bottomButtonsArea.removeFromLeft(bottomButtonsArea.getWidth() / 2).reduced(5, 0));
    exportButton.setBounds(bottomButtonsArea.reduced(5, 0));
}