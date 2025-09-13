#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h"

ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor)
    : audioProcessor(processor)
{
    // === EDITOR DE PROMPT ===
    addAndMakeVisible(promptLabel);
    promptLabel.setText("Escribe tu prompt aqui (ej: 'C minor', 'triste en Am')", juce::dontSendNotification);
    addAndMakeVisible(promptEditor);
    promptEditor.setMultiLine(true);

    // === MENÚ DE GÉNERO ===
    addAndMakeVisible(genreLabel);
    genreLabel.setText("Genero", juce::dontSendNotification);
    addAndMakeVisible(genreComboBox);
    genreComboBox.addItem("Detectar desde prompt", 1);
    juce::StringArray availableGenres = audioProcessor.pythonManager->getAvailableGenres();
    for (int i = 0; i < availableGenres.size(); ++i)
    {
        juce::String genre = availableGenres[i];
        juce::String capitalizedGenre = genre.substring(0, 1).toUpperCase() + genre.substring(1);
        genreComboBox.addItem(capitalizedGenre, i + 2);
    }
    genreComboBox.setSelectedId(1);

    // === SLIDER DE BPM ===
    addAndMakeVisible(bpmSlider);
    bpmSlider.setSliderStyle(juce::Slider::SliderStyle::LinearHorizontal);
    bpmSlider.setTextBoxStyle(juce::Slider::TextBoxRight, false, 50, 20);
    bpmSlider.setRange(40.0, 220.0, 1.0);
    bpmSlider.setValue(120.0);
    addAndMakeVisible(bpmLabel);
    bpmLabel.setText("BPM", juce::dontSendNotification);
    bpmLabel.attachToComponent(&bpmSlider, true);

    // === BOTONES DE GENERACIÓN Y TRANSPOSICIÓN ===
    addAndMakeVisible(generateChordsButton);
    generateChordsButton.setButtonText("1. Generar Acordes");
    addAndMakeVisible(generateMelodyButton);
    generateMelodyButton.setButtonText("2. Generar Melodia");
    generateMelodyButton.setEnabled(false);

    addAndMakeVisible(transposeUpButton);
    transposeUpButton.setButtonText("+1 Semitono");
    transposeUpButton.setEnabled(false);

    addAndMakeVisible(transposeDownButton);
    transposeDownButton.setButtonText("-1 Semitono");
    transposeDownButton.setEnabled(false);

    // === BOTONES DE CONTROL Y EXPORTACIÓN ===
    addAndMakeVisible(playButton);
    playButton.setButtonText("Reproducir");
    addAndMakeVisible(stopButton);
    stopButton.setButtonText("Pausar");
    addAndMakeVisible(exportChordsButton);
    exportChordsButton.setButtonText("Exportar Acordes");
    addAndMakeVisible(exportMelodyButton);
    exportMelodyButton.setButtonText("Exportar Melodia");
    exportMelodyButton.setEnabled(false);

    // === PIANO ROLL ===
    addAndMakeVisible(pianoRollComponent);

    // === LÓGICA DE LOS BOTONES ===
    generateChordsButton.onClick = [this]
        {
            juce::String userPrompt = promptEditor.getText();
            if (userPrompt.isEmpty()) return;

            juce::String selectedGenre = genreComboBox.getText();
            juce::String finalPrompt = userPrompt;

            if (genreComboBox.getSelectedId() != 1 && !userPrompt.containsIgnoreCase(selectedGenre))
            {
                finalPrompt = selectedGenre + " " + userPrompt;
            }

            DBG("Prompt final enviado a Python: " + finalPrompt);
            lastGeneratedChordsData = audioProcessor.pythonManager->generateMusicData(finalPrompt);

            if (lastGeneratedChordsData.empty() || (lastGeneratedChordsData.contains("error") && !lastGeneratedChordsData["error"].cast<std::string>().empty()))
            {
                std::string errorMessage = lastGeneratedChordsData.contains("error") ? lastGeneratedChordsData["error"].cast<std::string>() : "Diccionario vacio";
                DBG("!!! Error desde Python: " + juce::String(errorMessage));
                return;
            }

            DBG("Acordes generados desde Python con exito!");

            if (lastGeneratedChordsData.contains("bpm"))
            {
                int suggestedBpm = lastGeneratedChordsData["bpm"].cast<int>();
                bpmSlider.setValue(suggestedBpm, juce::sendNotification);
            }

            pianoRollComponent.setMusicData(lastGeneratedChordsData);
            generateMelodyButton.setEnabled(true);
            exportMelodyButton.setEnabled(false);
            transposeUpButton.setEnabled(true);
            transposeDownButton.setEnabled(true);
            repaint();
        };

    generateMelodyButton.onClick = [this]
        {
            if (lastGeneratedChordsData.empty() || !lastGeneratedChordsData.contains("acordes"))
            {
                DBG("Error: No hay acordes generados para crear una melodia.");
                return;
            }

            DBG("Enviando datos a Python para generar melodia...");

            py::list chords = lastGeneratedChordsData["acordes"];
            py::list rhythm = lastGeneratedChordsData["ritmo"];
            std::string root = lastGeneratedChordsData["raiz"].cast<std::string>();
            std::string mode = lastGeneratedChordsData["modo"].cast<std::string>();
            int bpm = (int)bpmSlider.getValue();
            auto melodyData = audioProcessor.pythonManager->generateMelodyData(chords, rhythm, root, mode, bpm);

            if (melodyData.empty() || (melodyData.contains("error") && !melodyData["error"].cast<std::string>().empty()))
            {
                std::string errorMessage = melodyData.contains("error") ? melodyData["error"].cast<std::string>() : "Diccionario vacio";
                DBG("!!! Error al generar la melodia desde Python: " + juce::String(errorMessage));
                return;
            }

            DBG("Melodia generada con exito!");

            lastGeneratedChordsData["melodia"] = melodyData["melodia"];
            pianoRollComponent.setMusicData(lastGeneratedChordsData);
            exportMelodyButton.setEnabled(true);
            repaint();
        };

    playButton.onClick = [this]
        {
            if (isPlaying || lastGeneratedChordsData.empty()) return;

            isPlaying = true;
            nextEventIndex = 0;
            playbackEvents.clear();

            // 1. Recopilar todas las notas (acordes y melodía)
            auto notesToPlay = pianoRollComponent.getNotes(); // Necesitaremos añadir esta función pública
            int currentBpm = (int)bpmSlider.getValue();

            // 2. Convertir nuestras notas en eventos MIDI temporizados
            for (const auto& note : notesToPlay)
            {
                // Evento de Nota Encendida (Note On)
                playbackEvents.add({ note.startTime, juce::MidiMessage::noteOn(1, note.midiNote, (juce::uint8)100), });
                // Evento de Nota Apagada (Note Off)
                playbackEvents.add({ note.startTime + note.duration, juce::MidiMessage::noteOff(1, note.midiNote), });
            }

            // 3. Ordenar todos los eventos por su tiempo de inicio
            std::sort(playbackEvents.begin(), playbackEvents.end());

            // 4. Iniciar el temporizador
            startTime = juce::Time::getMillisecondCounterHiRes() / 1000.0; // Tiempo de inicio en segundos
            startTimerHz(100); // Llamar a timerCallback 100 veces por segundo
        };

    stopButton.onClick = [this]
        {
            if (!isPlaying) return;

            stopTimer();
            isPlaying = false;
            // Envía un mensaje "All Notes Off" para silenciar cualquier nota que se haya quedado sonando
            audioProcessor.addMidiMessageToQueue(juce::MidiMessage::allNotesOff(1));
        };

    transposeUpButton.onClick = [this] { transpose(1); };
    transposeDownButton.onClick = [this] { transpose(-1); };

    exportChordsButton.onClick = [this]
        {
            int currentBpm = (int)bpmSlider.getValue();
            juce::String result = audioProcessor.pythonManager->exportChords(lastGeneratedChordsData, currentBpm);
            juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::InfoIcon, "Exportar Acordes", result);
            DBG(result);
        };

    exportMelodyButton.onClick = [this]
        {
            int currentBpm = (int)bpmSlider.getValue();
            juce::String result = audioProcessor.pythonManager->exportMelody(lastGeneratedChordsData, currentBpm);
            juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::InfoIcon, "Exportar Melodia", result);
            DBG(result);
        };
}

ChordMelodyTabComponent::~ChordMelodyTabComponent()
{
    stopTimer(); // Buena práctica para detener el timer al cerrar
}

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

    controlsArea.removeFromTop(10); // Un pequeño espacio
    bpmSlider.setBounds(controlsArea.removeFromTop(30));

    bounds.removeFromTop(10);
    auto generationButtonsArea = bounds.removeFromTop(40);
    auto leftButtons = generationButtonsArea.removeFromLeft(generationButtonsArea.getWidth() * 0.7);
    generateChordsButton.setBounds(leftButtons.removeFromLeft(leftButtons.getWidth() / 2).reduced(5, 0));
    generateMelodyButton.setBounds(leftButtons.reduced(5, 0));

    auto transposeArea = generationButtonsArea;
    transposeDownButton.setBounds(transposeArea.removeFromLeft(transposeArea.getWidth() / 2).reduced(5, 0));
    transposeUpButton.setBounds(transposeArea.reduced(5, 0));

    bounds.removeFromTop(10);
    pianoRollComponent.setBounds(bounds.removeFromTop(bounds.getHeight() - 60));

    bounds.removeFromTop(10);
    auto bottomButtonsArea = bounds.removeFromBottom(40);
    playButton.setBounds(bottomButtonsArea.removeFromLeft(bottomButtonsArea.getWidth() / 4).reduced(5, 0));
    stopButton.setBounds(bottomButtonsArea.removeFromLeft(bottomButtonsArea.getWidth() / 3).reduced(5, 0));
    exportChordsButton.setBounds(bottomButtonsArea.removeFromLeft(bottomButtonsArea.getWidth() / 2).reduced(5, 0));
    exportMelodyButton.setBounds(bottomButtonsArea.reduced(5, 0));
}

void ChordMelodyTabComponent::timerCallback()
{
    if (!isPlaying)
    {
        stopTimer();
        return;
    }

    double currentTimeSeconds = (juce::Time::getMillisecondCounterHiRes() / 1000.0) - startTime;
    double currentBeat = currentTimeSeconds * (bpmSlider.getValue() / 60.0);

    // Revisa los eventos MIDI que deben dispararse
    while (nextEventIndex < playbackEvents.size() && playbackEvents[nextEventIndex].timeInBeats <= currentBeat)
    {
        // Envía el mensaje MIDI al procesador de audio
        audioProcessor.addMidiMessageToQueue(playbackEvents[nextEventIndex].message);
        nextEventIndex++;
    }

    // Si ya no hay más eventos, detener la reproducción
    if (nextEventIndex >= playbackEvents.size())
    {
        stopTimer();
        isPlaying = false;
    }
}

void ChordMelodyTabComponent::transpose(int semitones)
{
    if (lastGeneratedChordsData.empty()) return;

    DBG("Transponiendo por " + juce::String(semitones) + " semitonos...");
    auto transposedData = audioProcessor.pythonManager->transposeMusic(lastGeneratedChordsData, semitones);

    // Revisa si Python devolvió un error
    if (transposedData.contains("error") && !transposedData["error"].cast<std::string>().empty())
    {
        auto errorMessage = transposedData["error"].cast<std::string>();
        DBG("!!! Error al transponer desde Python: " + juce::String(errorMessage));
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Error de Transposicion", errorMessage);
        return;
    }

    // Actualiza los datos y la interfaz
    lastGeneratedChordsData = transposedData;
    pianoRollComponent.setMusicData(lastGeneratedChordsData);
    repaint();
}
