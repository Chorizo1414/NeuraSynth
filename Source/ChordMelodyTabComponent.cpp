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

    addAndMakeVisible(chordCountComboBox);
    chordCountComboBox.addItem(juce::String::fromUTF8("Sin l\xC3\xADmite"), 1);
    chordCountComboBox.addItem("4", 2);
    chordCountComboBox.addItem("6", 3);
    chordCountComboBox.addItem("8", 4);
    chordCountComboBox.setSelectedId(1);
    addAndMakeVisible(chordCountLabel);
    chordCountLabel.setText(juce::String::fromUTF8("N\xC2\xB0 Acordes:"), juce::dontSendNotification);
    chordCountLabel.attachToComponent(&chordCountComboBox, true);


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

            int chordLimit = -1;
            switch (chordCountComboBox.getSelectedId())
            {
            case 2: chordLimit = 4; break;
            case 3: chordLimit = 6; break;
            case 4: chordLimit = 8; break;
            default: break;
            }

            lastGeneratedChordsData = audioProcessor.pythonManager->generateMusicData(finalPrompt, chordLimit);

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
            if (audioProcessor.isPlayingSequence())
            {
                audioProcessor.stopPlayback();
                playButton.setButtonText("Reproducir");
            }
            else
            {
                // Verificamos que haya notas usando nuestro nuevo getter
                if (!pianoRollComponent.getMusicData().empty())
                {
                    prepareAndPlaySequence();
                    playButton.setButtonText("Detener");
                }
            }
        };

    stopButton.onClick = [this]
        {
            audioProcessor.stopPlayback();
            playButton.setButtonText("Reproducir");
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

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::grey);
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
    chordCountComboBox.setBounds(controlsArea.removeFromTop(30));

    controlsArea.removeFromTop(10);
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

void ChordMelodyTabComponent::prepareAndPlaySequence()
{
    double sampleRate = audioProcessor.getSampleRate();
    if (sampleRate <= 0) return;

    double bpm = bpmSlider.getValue();
    double secondsPerBeat = 60.0 / bpm;

    struct MidiEventInfo
    {
        int samplePosition;
        juce::MidiMessage message;
    };
    std::vector<MidiEventInfo> eventList;

    // Usamos el getter para acceder a las notas de forma segura
    for (const auto& noteInfo : pianoRollComponent.getMusicData())
    {
        double startTimeSecs = noteInfo.startTime * secondsPerBeat;
        double endTimeSecs = startTimeSecs + (noteInfo.duration * secondsPerBeat);
        int startSample = static_cast<int>(startTimeSecs * sampleRate);
        int endSample = static_cast<int>(endTimeSecs * sampleRate);

        auto createEventsForNote = [&](int midiNote)
            {
                if (midiNote > 0 && endSample > startSample) {
                    eventList.push_back({ startSample, juce::MidiMessage::noteOn(1, midiNote, (juce::uint8)100) });
                    eventList.push_back({ endSample,   juce::MidiMessage::noteOff(1, midiNote) });
                }
            };

        if (noteInfo.isMelody)
        {
            createEventsForNote(noteInfo.midiValue);
        }
        else
        {
            for (int chordNoteMidi : noteInfo.chordMidiValues)
            {
                createEventsForNote(chordNoteMidi);
            }
        }
    }

    std::sort(eventList.begin(), eventList.end(), [](const MidiEventInfo& a, const MidiEventInfo& b) {
        return a.samplePosition < b.samplePosition;
        });

    juce::MidiBuffer midiSequence;
    for (const auto& event : eventList)
    {
        midiSequence.addEvent(event.message, event.samplePosition);
    }

    audioProcessor.startPlaybackWithSequence(midiSequence);
}