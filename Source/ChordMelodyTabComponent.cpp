#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h"

namespace
{
    const juce::Colour backgroundTopColour = juce::Colour::fromRGB(20, 22, 25);
    const juce::Colour backgroundBottomColour = juce::Colour::fromRGB(12, 13, 15);
    const juce::Colour panelBaseColour = juce::Colour::fromRGB(30, 33, 37);
    const juce::Colour panelOutlineColour = juce::Colour::fromRGB(62, 66, 73);
    const juce::Colour panelHighlightColour = juce::Colour::fromRGB(44, 48, 54);
    const juce::Colour accentColour = juce::Colour::fromRGB(120, 144, 165);
    const juce::Colour buttonBaseColour = juce::Colour::fromRGB(40, 43, 48);
    const juce::Colour buttonDownColour = juce::Colour::fromRGB(66, 92, 116);
    const juce::Colour mainTextColour = juce::Colour::fromRGB(218, 222, 227);
    const juce::Colour subtleTextColour = juce::Colour::fromRGB(148, 156, 165);

    juce::Rectangle<int> expanded(const juce::Rectangle<int>& rect, int amountX, int amountY)
    {
        auto result = rect;
        result.setX(result.getX() - amountX);
        result.setY(result.getY() - amountY);
        result.setWidth(result.getWidth() + amountX * 2);
        result.setHeight(result.getHeight() + amountY * 2);
        return result;
    }

    juce::String utf8String(const char* text)
    {
        return text != nullptr ? juce::String::fromUTF8(text) : juce::String();
    }

    juce::String utf8String(const std::string& text)
    {
        return juce::String::fromUTF8(text.c_str());
    }
}

ChordMelodyTabComponent::ChordMelodyTabComponent(NeuraSynthAudioProcessor& processor)
    : audioProcessor(processor)
{
    setOpaque(true);

    auto stylizeButton = [](juce::TextButton& button)
        {
            button.setColour(juce::TextButton::buttonColourId, buttonBaseColour);
            button.setColour(juce::TextButton::buttonOnColourId, buttonDownColour);
            button.setColour(juce::TextButton::textColourOffId, mainTextColour);
            button.setColour(juce::TextButton::textColourOnId, mainTextColour);
            //button.setColour(juce::TextButton::outlineColourId, panelOutlineColour.withAlpha(0.35f));
        };

    auto stylizeCombo = [](juce::ComboBox& combo)
        {
            combo.setColour(juce::ComboBox::backgroundColourId, buttonBaseColour);
            combo.setColour(juce::ComboBox::textColourId, mainTextColour);
            combo.setColour(juce::ComboBox::arrowColourId, mainTextColour);
            combo.setColour(juce::ComboBox::outlineColourId, panelOutlineColour.withAlpha(0.35f));
        };

    auto stylizeLabel = [](juce::Label& label)
        {
            label.setColour(juce::Label::textColourId, subtleTextColour);
            label.setJustificationType(juce::Justification::centredLeft);
        };

    promptEditor.setColour(juce::TextEditor::backgroundColourId, juce::Colour::fromRGB(26, 28, 32));
    promptEditor.setColour(juce::TextEditor::outlineColourId, panelOutlineColour.withAlpha(0.4f));
    promptEditor.setColour(juce::TextEditor::focusedOutlineColourId, panelOutlineColour.brighter(0.3f));
    promptEditor.setColour(juce::TextEditor::highlightColourId, panelHighlightColour.withAlpha(0.55f));
    promptEditor.setColour(juce::TextEditor::highlightedTextColourId, mainTextColour);
    promptEditor.setColour(juce::TextEditor::textColourId, mainTextColour);
    promptEditor.setBorder(juce::BorderSize<int>(6));
    promptEditor.setScrollbarsShown(true);
    promptEditor.setFont(juce::Font(15.0f, juce::Font::plain));

    stylizeLabel(promptLabel);

    // === EDITOR DE PROMPT ===
    addAndMakeVisible(promptLabel);
    promptLabel.setText("Escribe tu prompt aqui (ej: 'C minor', 'triste en Am')", juce::dontSendNotification);
    addAndMakeVisible(promptEditor);
    promptEditor.setMultiLine(true);

    // === MENU DE GENERO ===
    addAndMakeVisible(genreLabel);
    genreLabel.setText("Genero", juce::dontSendNotification);
    stylizeLabel(genreLabel);
    addAndMakeVisible(genreComboBox);
    stylizeCombo(genreComboBox);
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
    stylizeCombo(chordCountComboBox);
    chordCountComboBox.addItem(juce::String::fromUTF8("Sin límite"), 1);
    chordCountComboBox.addItem("4", 2);
    chordCountComboBox.addItem("6", 3);
    chordCountComboBox.addItem("8", 4);
    chordCountComboBox.setSelectedId(1);
    addAndMakeVisible(chordCountLabel);
    chordCountLabel.setText(juce::String::fromUTF8("N° Acordes:"), juce::dontSendNotification);
    stylizeLabel(chordCountLabel);
    chordCountLabel.attachToComponent(&chordCountComboBox, true);

    // === CONTROL DE BPM ===
    addAndMakeVisible(bpmLabel);
    bpmLabel.setText("BPM:", juce::dontSendNotification);
    stylizeLabel(bpmLabel);

    addAndMakeVisible(bpmSlider);
    bpmSlider.setSliderStyle(juce::Slider::IncDecButtons);
    bpmSlider.setTextBoxStyle(juce::Slider::TextBoxLeft, false, 50, 20);
    bpmSlider.setRange(40.0, 220.0, 1.0);
    bpmSlider.setColour(juce::Slider::backgroundColourId, juce::Colour::fromRGB(24, 26, 29));
    bpmSlider.setColour(juce::Slider::trackColourId, panelOutlineColour.withAlpha(0.45f));
    bpmSlider.setColour(juce::Slider::thumbColourId, accentColour.withAlpha(0.9f));
    bpmSlider.setColour(juce::Slider::textBoxTextColourId, mainTextColour);
    bpmSlider.setColour(juce::Slider::textBoxBackgroundColourId, buttonBaseColour);
    bpmSlider.setColour(juce::Slider::textBoxOutlineColourId, panelOutlineColour.withAlpha(0.35f));
    bpmLabel.attachToComponent(&bpmSlider, true);

    setBpmValue(120.0, juce::dontSendNotification);

    // === BOTONES DE GENERACIÓN Y TRANSPOSICIÓN ===
    addAndMakeVisible(generateChordsButton);
    generateChordsButton.setButtonText("1. Generar Acordes");
    stylizeButton(generateChordsButton);
    addAndMakeVisible(generateMelodyButton);
    generateMelodyButton.setButtonText("2. Generar Melodia");
    generateMelodyButton.setEnabled(false);
    stylizeButton(generateMelodyButton);

    addAndMakeVisible(transposeUpButton);
    transposeUpButton.setButtonText("+1 Semitono");
    transposeUpButton.setEnabled(false);
    stylizeButton(transposeUpButton);

    addAndMakeVisible(transposeDownButton);
    transposeDownButton.setButtonText("-1 Semitono");
    transposeDownButton.setEnabled(false);
    stylizeButton(transposeDownButton);

    // === BOTONES DE CONTROL Y EXPORTACIÓN ===
    addAndMakeVisible(playAllButton);
    playAllButton.setButtonText("Reproducir Todo");
    stylizeButton(playAllButton);
    addAndMakeVisible(playChordsButton);
    playChordsButton.setButtonText("Reproducir Acordes");
    stylizeButton(playChordsButton);
    addAndMakeVisible(playMelodyButton);
    playMelodyButton.setButtonText("Reproducir Melodia");
    stylizeButton(playMelodyButton);
    addAndMakeVisible(stopButton);
    stopButton.setButtonText("Detener");
    stylizeButton(stopButton);
    addAndMakeVisible(exportChordsButton);
    exportChordsButton.setButtonText("Exportar Acordes");
    stylizeButton(exportChordsButton);
    addAndMakeVisible(exportMelodyButton);
    exportMelodyButton.setButtonText("Exportar Melodia");
    exportMelodyButton.setEnabled(false);
    stylizeButton(exportMelodyButton);

    // === PIANO ROLL ===
    addAndMakeVisible(pianoRollComponent);

    // === LOGICA DE LOS BOTONES ===
    generateChordsButton.onClick = [this]
        {
            generateChordsFromCurrentPrompt();
        };

    // Crear y configurar el botón "Me gusta"
    likeButton = std::make_unique<juce::ImageButton>();
    auto likeImg = juce::ImageCache::getFromMemory(BinaryData::corazon_png, BinaryData::corazon_pngSize);
    likeButton->setImages(false, true, true,
        likeImg, 1.0f, juce::Colours::transparentBlack,
        likeImg, 0.85f, juce::Colours::transparentBlack,
        likeImg, 0.7f, juce::Colours::transparentBlack);
    likeButton->onClick = [this] {
        audioProcessor.pythonManager->like();
        showNotification("Feedback Positivo Enviado!");
        };
    addAndMakeVisible(*likeButton);

    // Crear y configurar el botón "No me gusta"
    dislikeButton = std::make_unique<juce::ImageButton>();
    auto dislikeImg = juce::ImageCache::getFromMemory(BinaryData::pulgar_abajo_png, BinaryData::pulgar_abajo_pngSize);
    dislikeButton->setImages(false, true, true,
        dislikeImg, 1.0f, juce::Colours::transparentBlack,
        dislikeImg, 0.85f, juce::Colours::transparentBlack,
        dislikeImg, 0.7f, juce::Colours::transparentBlack);
    dislikeButton->onClick = [this] {
        audioProcessor.pythonManager->dislike();
        showNotification("Feedback Negativo Enviado! Generando nueva progresion...");
        generateChordsFromCurrentPrompt();
        };
    addAndMakeVisible(*dislikeButton);

    addAndMakeVisible(undoButton);
    undoButton.setButtonText("Deshacer");
    stylizeButton(undoButton);
    undoButton.onClick = [this]
        {
            if (historyCurrentIndex > 0)
                applyStateFromHistory(historyCurrentIndex - 1);
        };

    addAndMakeVisible(redoButton);
    redoButton.setButtonText("Rehacer");
    stylizeButton(redoButton);
    redoButton.onClick = [this]
        {
            if (historyCurrentIndex >= 0 && historyCurrentIndex < (int)historyStates.size() - 1)
                applyStateFromHistory(historyCurrentIndex + 1);
        };

    addAndMakeVisible(notificationLabel);
    notificationLabel.setColour(juce::Label::backgroundColourId, juce::Colour::fromRGBA(14, 16, 20, 200));
    notificationLabel.setColour(juce::Label::outlineColourId, panelOutlineColour.withAlpha(0.45f));
    notificationLabel.setColour(juce::Label::textColourId, mainTextColour);
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
                DBG("!!! Error al generar la melodia desde Python: " + utf8String(errorMessage));
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
                    if (audioProcessor.isPlayingSequence())
                    {
                        audioProcessor.stopPlayback();
                        stopTimer(playbackMonitorTimerId);
                        handlePlaybackFinished();

                    }

                    if (prepareAndPlaySequence(includeChords, includeMelody))
                    {
                        activePlaybackButton = buttonPtr;
                    }
                };
        };

    configurePlaybackButton(playAllButton, true, true);
    configurePlaybackButton(playChordsButton, true, false);
    configurePlaybackButton(playMelodyButton, false, true);

    stopButton.onClick = [this]
        {
            audioProcessor.stopPlayback();
            stopTimer(playbackMonitorTimerId);
            handlePlaybackFinished();
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
    juce::ColourGradient backgroundGradient(backgroundTopColour, 0.0f, 0.0f,
        backgroundBottomColour, 0.0f, (float)getHeight(), false);
    g.setGradientFill(backgroundGradient);
    g.fillAll();

    auto drawPanel = [&g](const juce::Rectangle<int>& area)
        {
            if (area.isEmpty())
                return;

            auto bounded = area.getIntersection(g.getClipBounds());
            if (bounded.isEmpty())
                return;

            auto roundedBounds = bounded.toFloat();

            juce::ColourGradient panelGradient(panelBaseColour.brighter(0.06f),
                roundedBounds.getCentreX(), roundedBounds.getY(),
                panelBaseColour.darker(0.04f),
                roundedBounds.getCentreX(), roundedBounds.getBottom(), false);

            g.setGradientFill(panelGradient);
            g.fillRoundedRectangle(roundedBounds, 10.0f);

            g.setColour(panelOutlineColour.withAlpha(0.45f));
            g.drawRoundedRectangle(roundedBounds, 10.0f, 1.0f);

            auto innerBounds = bounded.reduced(8);
            if (!innerBounds.isEmpty())
            {
                g.setColour(panelHighlightColour.withAlpha(0.25f));
                g.drawRoundedRectangle(innerBounds.toFloat(), 8.0f, 1.0f);
            }
        };

    auto bounds = getLocalBounds().reduced(10);

    auto bottomArea = bounds.removeFromBottom(90);
    auto topArea = bounds.removeFromTop(180);
    bounds.removeFromTop(10);
    auto pianoArea = bounds;

    auto topWorking = topArea;
    auto rightColumn = topWorking.removeFromRight(200).reduced(5, 0);
    auto leftColumn = topWorking;
    leftColumn.removeFromRight(10);
    auto promptArea = leftColumn.removeFromTop(125);
    leftColumn.removeFromTop(10);
    auto generationArea = leftColumn;

    auto bottomWorking = bottomArea;
    auto playbackRow = bottomWorking.removeFromTop(40);
    auto exportRow = bottomWorking.removeFromBottom(40);

    drawPanel(expanded(promptArea.getUnion(generationArea), 12, 8));
    drawPanel(expanded(rightColumn, 12, 8));
    drawPanel(expanded(playbackRow, 10, 6));
    drawPanel(expanded(exportRow, 10, 6));
    drawPanel(expanded(pianoArea, 8, 12));

    auto drawRightColumnDividers = [&](juce::Rectangle<int> columnArea)
        {
            auto working = columnArea;
            const int rowHeight = 25;
            const int spacing = 5;
            for (int i = 0; i < 6; ++i)
            {
                if (working.getHeight() <= rowHeight)
                    break;

                working.removeFromTop(rowHeight);
                if (working.getHeight() <= 0)
                    break;

                auto dividerY = working.getY() - spacing / 2;
                g.setColour(panelOutlineColour.withAlpha(0.25f));
                g.fillRect(juce::Rectangle<int>(columnArea.getX() + 12, dividerY, columnArea.getWidth() - 24, 1));

                working.removeFromTop(spacing);
            }
        };

    drawRightColumnDividers(rightColumn);
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
        DBG("!!! Error al transponer desde Python: " + utf8String(errorMessage));
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::WarningIcon, "Error de Transposicion", utf8String(errorMessage));
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
    pianoRollComponent.startPlayback(bpm);
    startTimer(playbackMonitorTimerId, 30);
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
    startTimer(notificationTimerId, 2000); // Iniciamos un temporizador de 2 segundos (2000 ms)
}

void ChordMelodyTabComponent::timerCallback(int timerId)
{
    if (timerId == notificationTimerId)
    {
        notificationLabel.setAlpha(0.0f); // Ocultamos la etiqueta
        stopTimer(notificationTimerId); // Detenemos el temporizador
    }
    else if (timerId == playbackMonitorTimerId)
    {
        if (!audioProcessor.isPlayingSequence())
        {
            stopTimer(playbackMonitorTimerId);
            handlePlaybackFinished();
        }
    }
}

void ChordMelodyTabComponent::handlePlaybackFinished()
{
    pianoRollComponent.stopPlayback();
    if (activePlaybackButton != nullptr)
        resetPlaybackButtonStates();
}

void ChordMelodyTabComponent::generateChordsFromCurrentPrompt()
{
    juce::String userPrompt = promptEditor.getText();
    if (userPrompt.isEmpty())
        return;

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
        DBG("!!! Error desde Python: " + utf8String(errorMessage));
        return;
    }

    DBG("Acordes generados desde Python con exito!");

    juce::String modeSummary;
    if (lastGeneratedChordsData.contains("tipo_generacion"))
    {
        py::object modeObj = lastGeneratedChordsData["tipo_generacion"];
        if (!modeObj.is_none())
        {
            const std::string modeType = modeObj.cast<std::string>();
            if (modeType == "markov")
                modeSummary = utf8String(u8"Progresión generada con el método de Markov.");
            else if (modeType == "learned")
                modeSummary = utf8String(u8"Progresión obtenida de una progresión guardada.");
            else if (modeType == "fallback")
                modeSummary = utf8String(u8"Progresión generada mediante el fallback interno.");
            else if (!modeType.empty() && modeType != "unknown")
                modeSummary = utf8String(u8"Progresión generada con modo: ") + utf8String(modeType);
        }
    }

    if (modeSummary.isNotEmpty())
        DBG(modeSummary);

    if (lastGeneratedChordsData.contains("fuente_generacion"))
    {
        py::object detailObj = lastGeneratedChordsData["fuente_generacion"];
        if (!detailObj.is_none())
        {
            const std::string detail = detailObj.cast<std::string>();
            if (!detail.empty())
                DBG(utf8String(u8"Detalle de origen de progresión: ") + utf8String(detail));
        }
    }

    if (lastGeneratedChordsData.contains("bpm"))
    {
        int suggestedBpm = lastGeneratedChordsData["bpm"].cast<int>();
        setBpmValue(suggestedBpm);
    }

    pianoRollComponent.setMusicData(lastGeneratedChordsData);
    updateUiForCurrentState();
    pushStateToHistory(lastGeneratedChordsData);
    repaint();
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