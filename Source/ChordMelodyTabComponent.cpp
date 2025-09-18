// CÓDIGO LIMPIO PARA ChordMelodyTabComponent.cpp
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

    // === MENU DE GENERO ===
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
    chordCountComboBox.addItem(juce::String::fromUTF8("Sin límite"), 1);
    chordCountComboBox.addItem("4", 2);
    chordCountComboBox.addItem("6", 3);
    chordCountComboBox.addItem("8", 4);
    chordCountComboBox.setSelectedId(1);
    addAndMakeVisible(chordCountLabel);
    chordCountLabel.setText(juce::String::fromUTF8("N° Acordes:"), juce::dontSendNotification);
    chordCountLabel.attachToComponent(&chordCountComboBox, true);

    // === CONTROL DE BPM ===
    addAndMakeVisible(bpmLabel);
    bpmLabel.setText("BPM:", juce::dontSendNotification);

    addAndMakeVisible(bpmSlider);
    bpmSlider.setSliderStyle(juce::Slider::IncDecButtons);
    bpmSlider.setTextBoxStyle(juce::Slider::TextBoxLeft, false, 50, 20);
    bpmSlider.setRange(40.0, 220.0, 1.0);
    bpmLabel.attachToComponent(&bpmSlider, true);

    setBpmValue(120.0, juce::dontSendNotification);

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
    addAndMakeVisible(playAllButton);
    playAllButton.setButtonText("Reproducir Todo");
    addAndMakeVisible(playChordsButton);
    playChordsButton.setButtonText("Reproducir Acordes");
    addAndMakeVisible(playMelodyButton);
    playMelodyButton.setButtonText("Reproducir Melodia");
    addAndMakeVisible(stopButton);
    stopButton.setButtonText("Detener");
    addAndMakeVisible(exportChordsButton);
    exportChordsButton.setButtonText("Exportar Acordes");
    addAndMakeVisible(exportMelodyButton);
    exportMelodyButton.setButtonText("Exportar Melodia");
    exportMelodyButton.setEnabled(false);

    // === PIANO ROLL ===
    addAndMakeVisible(pianoRollComponent);

    // === LOGICA DE LOS BOTONES ===
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
                setBpmValue(suggestedBpm);
            }

            pianoRollComponent.setMusicData(lastGeneratedChordsData);
            updateUiForCurrentState();
            pushStateToHistory(lastGeneratedChordsData);
            repaint();
        };

    // Crear y configurar el botón "Me gusta"
    likeButton = std::make_unique<juce::ImageButton>();
    auto likeImg = juce::ImageCache::getFromMemory(BinaryData::corazon_png, BinaryData::corazon_pngSize);
    likeButton->setImages(true, true, true,
        likeImg, 1.0f, juce::Colours::transparentBlack, // Imagen normal
        likeImg, 0.8f, juce::Colours::transparentBlack, // Imagen al pasar el ratón
        likeImg, 0.5f, juce::Colours::transparentBlack); // Imagen al hacer clic
    likeButton->onClick = [this] {
        audioProcessor.pythonManager->like();
        showNotification("Feedback Positivo Enviado!");
        };
    addAndMakeVisible(*likeButton);

    // Crear y configurar el botón "No me gusta"
    dislikeButton = std::make_unique<juce::ImageButton>();
    auto dislikeImg = juce::ImageCache::getFromMemory(BinaryData::pulgar_abajo_png, BinaryData::pulgar_abajo_pngSize);
    dislikeButton->setImages(true, true, true,
        dislikeImg, 1.0f, juce::Colours::transparentBlack,
        dislikeImg, 0.8f, juce::Colours::transparentBlack,
        dislikeImg, 0.5f, juce::Colours::transparentBlack);
    dislikeButton->onClick = [this] {
        audioProcessor.pythonManager->dislike();
        showNotification("Feedback Negativo Enviado!");
        };
    addAndMakeVisible(*dislikeButton);

    addAndMakeVisible(undoButton);
    undoButton.setButtonText("Deshacer");
    undoButton.onClick = [this]
        {
            if (historyCurrentIndex > 0)
                applyStateFromHistory(historyCurrentIndex - 1);
        };

    addAndMakeVisible(redoButton);
    redoButton.setButtonText("Rehacer");
    redoButton.onClick = [this]
        {
            if (historyCurrentIndex >= 0 && historyCurrentIndex < (int)historyStates.size() - 1)
                applyStateFromHistory(historyCurrentIndex + 1);
        };

    addAndMakeVisible(notificationLabel);
    notificationLabel.setColour(juce::Label::backgroundColourId, juce::Colours::darkgrey.withAlpha(0.8f));
    notificationLabel.setColour(juce::Label::textColourId, juce::Colours::white);
    notificationLabel.setJustificationType(juce::Justification::centred);
    notificationLabel.setAlpha(0.0f);

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
            updateUiForCurrentState();
            pushStateToHistory(lastGeneratedChordsData);
            repaint();
        };

    auto configurePlaybackButton = [this](juce::TextButton& targetButton, bool includeChords, bool includeMelody)
        {
            auto* buttonPtr = &targetButton;
            targetButton.onClick = [this, includeChords, includeMelody, buttonPtr]()
                {
                    const bool isSameButton = (activePlaybackButton == buttonPtr);

                    if (audioProcessor.isPlayingSequence())
                    {
                        audioProcessor.stopPlayback();
                        resetPlaybackButtonStates();

                        if (isSameButton)
                            return;
                    }

                    if (prepareAndPlaySequence(includeChords, includeMelody))
                    {
                        activePlaybackButton = buttonPtr;
                        buttonPtr->setButtonText("Detener");
                    }
                };
        };

    configurePlaybackButton(playAllButton, true, true);
    configurePlaybackButton(playChordsButton, true, false);
    configurePlaybackButton(playMelodyButton, false, true);

    stopButton.onClick = [this]
        {
            audioProcessor.stopPlayback();
            resetPlaybackButtonStates();
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

    updateUiForCurrentState();
    updateUndoRedoButtonStates();
}

ChordMelodyTabComponent::~ChordMelodyTabComponent() {}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::grey);
}

// Source/ChordMelodyTabComponent.cpp
void ChordMelodyTabComponent::resized()
{
    juce::Rectangle<int> bounds = getLocalBounds().reduced(10);

    // --- 1. ÁREA INFERIOR: Botones de Playback y Exportación ---
    // Se define esta área primero, tomándola de la parte de abajo del plugin.
    auto bottomButtonsArea = bounds.removeFromBottom(90); // 40px para cada fila + 10px de espacio

    // Fila superior de este bloque (Playback)
    auto playbackRow = bottomButtonsArea.removeFromTop(40);

    // Fila inferior de este bloque (Exportar)
    auto exportRow = bottomButtonsArea.removeFromBottom(40);

    // Distribuimos los botones de Playback
    int playbackButtonWidth = playbackRow.getWidth() / 4;
    playAllButton.setBounds(playbackRow.removeFromLeft(playbackButtonWidth).reduced(5, 2));
    playChordsButton.setBounds(playbackRow.removeFromLeft(playbackButtonWidth).reduced(5, 2));
    playMelodyButton.setBounds(playbackRow.removeFromLeft(playbackButtonWidth).reduced(5, 2));
    stopButton.setBounds(playbackRow.reduced(5, 2));

    // Distribuimos los botones de Exportar
    int exportButtonWidth = exportRow.getWidth() / 2;
    exportChordsButton.setBounds(exportRow.removeFromLeft(exportButtonWidth).reduced(5, 2));
    exportMelodyButton.setBounds(exportRow.reduced(5, 2));


    // --- 2. ÁREA SUPERIOR: Prompt y todos los controles ---
    auto topArea = bounds.removeFromTop(180); // Altura para el prompt y los botones de abajo

    // Dividimos en columna izquierda y derecha
    auto rightColumn = topArea.removeFromRight(200); // Ancho fijo de 200px para la columna derecha
    auto leftColumn = topArea;


    // --- Lado Derecho: Columna de Controles ---
    rightColumn.reduce(5, 0); // Margen
    genreComboBox.setBounds(rightColumn.removeFromTop(25));
    rightColumn.removeFromTop(5);
    chordCountComboBox.setBounds(rightColumn.removeFromTop(25));
    rightColumn.removeFromTop(5);
    bpmSlider.setBounds(rightColumn.removeFromTop(25));
    rightColumn.removeFromTop(5);

    auto transposeArea = rightColumn.removeFromTop(25);
    transposeDownButton.setBounds(transposeArea.removeFromLeft(transposeArea.getWidth() / 2).reduced(2));
    transposeUpButton.setBounds(transposeArea.reduced(2));

    rightColumn.removeFromTop(5);

    auto feedbackArea = rightColumn.removeFromTop(25);
    likeButton->setBounds(feedbackArea.removeFromLeft(feedbackArea.getWidth() / 2).reduced(2));
    dislikeButton->setBounds(feedbackArea.reduced(2));

    rightColumn.removeFromTop(5);

    auto historyArea = rightColumn.removeFromTop(25);
    undoButton.setBounds(historyArea.removeFromLeft(historyArea.getWidth() / 2).reduced(2));
    redoButton.setBounds(historyArea.reduced(2));

    // --- Lado Izquierdo: Prompt y Botones de Generación ---
    leftColumn.removeFromRight(10); // Espacio entre columnas

    // El prompt ocupa la parte de arriba
    promptEditor.setBounds(leftColumn.removeFromTop(125));

    leftColumn.removeFromTop(10); // Espacio

    // Los botones de generar van debajo del prompt
    auto generationArea = leftColumn;
    generateChordsButton.setBounds(generationArea.removeFromLeft(generationArea.getWidth() / 2).reduced(5, 2));
    generateMelodyButton.setBounds(generationArea.reduced(5, 2));


    // --- 3. PIANO ROLL: Ocupa el espacio central restante ---
    bounds.removeFromTop(10); // Un último espacio antes del piano roll
    pianoRollComponent.setBounds(bounds);

    notificationLabel.setBounds(pianoRollComponent.getBounds().reduced(pianoRollComponent.getWidth() / 3,
        pianoRollComponent.getHeight() / 2.5));

    // Ocultamos las etiquetas que no necesitamos en este diseño
    promptLabel.setBounds({ 0,0,0,0 });
    genreLabel.setBounds({ 0,0,0,0 });
    chordCountLabel.setBounds({ 0,0,0,0 });
    bpmLabel.setBounds({ 0,0,0,0 });
}

void ChordMelodyTabComponent::transpose(int semitones)
{
    if (lastGeneratedChordsData.empty()) return;

    DBG("Transponiendo por " + juce::String(semitones) + " semitonos...");
    auto transposedData = audioProcessor.pythonManager->transposeMusic(lastGeneratedChordsData, semitones);

    if (transposedData.contains("error") && !transposedData["error"].cast<std::string>().empty())
    {
        auto errorMessage = transposedData["error"].cast<std::string>();
        DBG("!!! Error al transponer desde Python: " + juce::String(errorMessage));
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Error de Transposicion", errorMessage);
        return;
    }

    lastGeneratedChordsData = transposedData;
    pianoRollComponent.setMusicData(lastGeneratedChordsData);
    updateUiForCurrentState();
    pushStateToHistory(lastGeneratedChordsData);
    repaint();
}

bool ChordMelodyTabComponent::prepareAndPlaySequence(bool includeChords, bool includeMelody)
{
    if (!includeChords && !includeMelody)
        return false;

    const auto& musicData = pianoRollComponent.getMusicData();
    if (musicData.empty())
    {
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Reproduccion", "No hay datos para reproducir.");
        return false;
    }

    double sampleRate = audioProcessor.getSampleRate();
    if (sampleRate <= 0)
        return false;

    double bpm = bpmSlider.getValue();
    double secondsPerBeat = 60.0 / bpm;

    bool hasChordData = false;
    bool hasMelodyData = false;

    for (const auto& noteInfo : musicData)
    {
        if (noteInfo.isMelody)
            hasMelodyData = true;
        else
            hasChordData = true;
    }

    if (includeChords && !hasChordData)
    {
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Reproduccion", "No hay acordes generados para reproducir.");
        return false;
    }

    if (includeMelody && !hasMelodyData)
    {
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Reproduccion", "No hay melodia generada para reproducir.");
        return false;
    }

    struct MidiEventInfo
    {
        int samplePosition;
        juce::MidiMessage message;
    };
    std::vector<MidiEventInfo> eventList;

    for (const auto& noteInfo : musicData)
    {
        if ((noteInfo.isMelody && !includeMelody) || (!noteInfo.isMelody && !includeChords))
            continue;

        double startTimeSecs = noteInfo.startTime * secondsPerBeat;
        double endTimeSecs = startTimeSecs + (noteInfo.duration * secondsPerBeat);
        int startSample = static_cast<int>(startTimeSecs * sampleRate);
        int endSample = static_cast<int>(endTimeSecs * sampleRate);

        auto createEventsForNote = [&](int midiNote)
            {
                if (midiNote > 0 && endSample > startSample)
                {
                    eventList.push_back({ startSample, juce::MidiMessage::noteOn(1, midiNote, (juce::uint8)100) });
                    eventList.push_back({ endSample, juce::MidiMessage::noteOff(1, midiNote) });
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

    if (eventList.empty())
        return false;

    std::sort(eventList.begin(), eventList.end(), [](const MidiEventInfo& a, const MidiEventInfo& b)
        {
            return a.samplePosition < b.samplePosition;
        });

    juce::MidiBuffer midiSequence;
    for (const auto& event : eventList)
        midiSequence.addEvent(event.message, event.samplePosition);

    audioProcessor.startPlaybackWithSequence(midiSequence);
    return true;
}

void ChordMelodyTabComponent::resetPlaybackButtonStates()
{
    activePlaybackButton = nullptr;
    playAllButton.setButtonText("Reproducir Todo");
    playChordsButton.setButtonText("Reproducir Acordes");
    playMelodyButton.setButtonText("Reproducir Melodia");
}

void ChordMelodyTabComponent::setBpmValue(double newValue, juce::NotificationType notification)
{
    auto limitedValue = juce::jlimit(bpmSlider.getMinimum(), bpmSlider.getMaximum(), newValue);

    // Simplemente establece el valor. El slider se actualizará solo.
    bpmSlider.setValue(limitedValue, notification);
}

void ChordMelodyTabComponent::showNotification(const juce::String& message)
{
    notificationLabel.setText(message, juce::dontSendNotification);
    notificationLabel.setAlpha(1.0f); // Hacemos visible la etiqueta
    startTimer(2000); // Iniciamos un temporizador de 2 segundos (2000 ms)
}

void ChordMelodyTabComponent::timerCallback()
{
    notificationLabel.setAlpha(0.0f); // Ocultamos la etiqueta
    stopTimer(); // Detenemos el temporizador
}
void ChordMelodyTabComponent::updateUiForCurrentState()
{
    const bool hasData = !lastGeneratedChordsData.empty();
    const bool hasChords = hasData && lastGeneratedChordsData.contains("acordes");
    const bool hasMelody = hasData && lastGeneratedChordsData.contains("melodia");

    generateMelodyButton.setEnabled(hasChords);
    exportMelodyButton.setEnabled(hasMelody);
    transposeUpButton.setEnabled(hasData);
    transposeDownButton.setEnabled(hasData);
}

void ChordMelodyTabComponent::pushStateToHistory(const py::dict& data)
{
    if (data.empty())
        return;

    MusicState state;
    state.data = deepCopyMusicDict(data);
    state.bpm = bpmSlider.getValue();

    if (historyCurrentIndex + 1 < (int)historyStates.size())
        historyStates.erase(historyStates.begin() + historyCurrentIndex + 1, historyStates.end());

    historyStates.push_back(std::move(state));
    historyCurrentIndex = (int)historyStates.size() - 1;

    updateUndoRedoButtonStates();
}

void ChordMelodyTabComponent::applyStateFromHistory(int newIndex)
{
    if (newIndex < 0 || newIndex >= (int)historyStates.size())
        return;

    historyCurrentIndex = newIndex;

    lastGeneratedChordsData = deepCopyMusicDict(historyStates[historyCurrentIndex].data);
    pianoRollComponent.setMusicData(lastGeneratedChordsData);
    setBpmValue(historyStates[historyCurrentIndex].bpm);

    updateUiForCurrentState();
    repaint();
    updateUndoRedoButtonStates();
}

void ChordMelodyTabComponent::updateUndoRedoButtonStates()
{
    undoButton.setEnabled(historyCurrentIndex > 0);
    redoButton.setEnabled(historyCurrentIndex >= 0 && historyCurrentIndex < (int)historyStates.size() - 1);
}

py::dict ChordMelodyTabComponent::deepCopyMusicDict(const py::dict& source)
{
    py::gil_scoped_acquire acquire;
    static py::object deepcopyFunc = py::module::import("copy").attr("deepcopy");
    py::object result = deepcopyFunc(source);
    return result.cast<py::dict>();
}