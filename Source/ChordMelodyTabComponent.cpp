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
    const auto bpmFieldBackground = juce::Colour::fromRGB(32, 34, 38);
    const auto bpmButtonBackground = juce::Colour::fromRGB(58, 60, 64);
    const auto bpmOutlineColour = juce::Colours::white.withAlpha(0.35f);

    bpmSlider.setRange(40.0, 220.0, 1.0);
    bpmSlider.setNumDecimalPlacesToDisplay(0);

    bpmSlider.onValueChange = [this]() { updateBpmDisplayFromSlider(); };

    addAndMakeVisible(bpmValueLabel);
    bpmValueLabel.setJustificationType(juce::Justification::centred);
    bpmValueLabel.setEditable(true, true, false);
    bpmValueLabel.setColour(juce::Label::textColourId, juce::Colours::white);
    bpmValueLabel.setColour(juce::Label::backgroundColourId, bpmFieldBackground);
    bpmValueLabel.setColour(juce::Label::outlineColourId, bpmOutlineColour);
    bpmValueLabel.onTextChange = [this]() { commitBpmEditorText(); };
    bpmValueLabel.setTooltip("Editar BPM (40-220)");
    bpmValueLabel.onEditorShow = [this]()
        {
            if (auto* editor = bpmValueLabel.getCurrentTextEditor())
            {
                editor->setInputRestrictions(3, "0123456789");
                editor->selectAll();
            }
        };

    addAndMakeVisible(bpmIncreaseButton);
    bpmIncreaseButton.setButtonText(juce::CharPointer_UTF8("▲")); // up arrow
    bpmIncreaseButton.setRepeatSpeed(200, 50);
    bpmIncreaseButton.onClick = [this]() { adjustBpmValue(1); };
    bpmIncreaseButton.setColour(juce::TextButton::buttonColourId, bpmButtonBackground);
    bpmIncreaseButton.setColour(juce::TextButton::buttonOnColourId, bpmButtonBackground.brighter(0.2f));
    bpmIncreaseButton.setColour(juce::TextButton::textColourOnId, juce::Colours::white);
    bpmIncreaseButton.setColour(juce::TextButton::textColourOffId, juce::Colours::white);
    bpmIncreaseButton.setTooltip("Aumentar BPM");

    addAndMakeVisible(bpmDecreaseButton);
    bpmDecreaseButton.setButtonText(juce::CharPointer_UTF8("▼")); // down arrow
    bpmDecreaseButton.setRepeatSpeed(200, 50);
    bpmDecreaseButton.onClick = [this]() { adjustBpmValue(-1); };
    bpmDecreaseButton.setColour(juce::TextButton::buttonColourId, bpmButtonBackground);
    bpmDecreaseButton.setColour(juce::TextButton::buttonOnColourId, bpmButtonBackground.brighter(0.2f));
    bpmDecreaseButton.setColour(juce::TextButton::textColourOnId, juce::Colours::white);
    bpmDecreaseButton.setColour(juce::TextButton::textColourOffId, juce::Colours::white);
    bpmDecreaseButton.setTooltip("Reducir BPM");

    addAndMakeVisible(bpmLabel);
    bpmLabel.setText("BPM:", juce::dontSendNotification);
    bpmLabel.attachToComponent(&bpmValueLabel, true);

    setBpmValue(120.0, juce::dontSendNotification);
    updateBpmDisplayFromSlider();

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

    controlsArea.removeFromTop(10);
    chordCountComboBox.setBounds(controlsArea.removeFromTop(30));

    controlsArea.removeFromTop(10);
    auto bpmRow = controlsArea.removeFromTop(40);
    auto bpmValueArea = bpmRow.removeFromLeft(80);
    bpmValueLabel.setBounds(bpmValueArea.reduced(0, 6));
    bpmRow.removeFromLeft(6);
    auto bpmButtonsArea = bpmRow.removeFromLeft(24);
    auto bpmUpArea = bpmButtonsArea.removeFromTop(bpmButtonsArea.getHeight() / 2);
    bpmIncreaseButton.setBounds(bpmUpArea.reduced(0, 1));
    bpmDecreaseButton.setBounds(bpmButtonsArea.reduced(0, 1));

    bounds.removeFromTop(10);
    auto generationButtonsArea = bounds.removeFromTop(40);
    auto leftButtons = generationButtonsArea.removeFromLeft(generationButtonsArea.getWidth() * 0.7);
    generateChordsButton.setBounds(leftButtons.removeFromLeft(leftButtons.getWidth() / 2).reduced(5, 0));
    generateMelodyButton.setBounds(leftButtons.reduced(5, 0));

    auto transposeArea = generationButtonsArea;
    transposeDownButton.setBounds(transposeArea.removeFromLeft(transposeArea.getWidth() / 2).reduced(5, 0));
    transposeUpButton.setBounds(transposeArea.reduced(5, 0));

    bounds.removeFromTop(10);

    const int playbackRowHeight = 40;
    const int exportRowHeight = 40;
    const int bottomSpacing = 10;
    const int bottomAreaHeight = playbackRowHeight + exportRowHeight + bottomSpacing;

    pianoRollComponent.setBounds(bounds.removeFromTop(bounds.getHeight() - bottomAreaHeight));

    bounds.removeFromTop(bottomSpacing);
    auto playbackRow = bounds.removeFromTop(playbackRowHeight);
    auto exportRow = bounds;

    auto playbackButtonWidth = playbackRow.getWidth() / 4;
    playAllButton.setBounds(playbackRow.removeFromLeft(playbackButtonWidth).reduced(5, 0));
    playChordsButton.setBounds(playbackRow.removeFromLeft(playbackButtonWidth).reduced(5, 0));
    playMelodyButton.setBounds(playbackRow.removeFromLeft(playbackButtonWidth).reduced(5, 0));
    stopButton.setBounds(playbackRow.reduced(5, 0));

    exportChordsButton.setBounds(exportRow.removeFromLeft(exportRow.getWidth() / 2).reduced(5, 0));
    exportMelodyButton.setBounds(exportRow.reduced(5, 0));
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
    auto previousValue = bpmSlider.getValue();

    bpmSlider.setValue(limitedValue, notification);

    if (notification == juce::dontSendNotification || previousValue == limitedValue)
        updateBpmDisplayFromSlider();
}

void ChordMelodyTabComponent::updateBpmDisplayFromSlider()
{
    const int bpmAsInt = juce::roundToInt(bpmSlider.getValue());
    const juce::String bpmText(bpmAsInt);

    if (bpmValueLabel.getText() != bpmText)
        bpmValueLabel.setText(bpmText, juce::dontSendNotification);
}

void ChordMelodyTabComponent::commitBpmEditorText()
{
    auto text = bpmValueLabel.getText().trim();

    if (text.isEmpty())
    {
        updateBpmDisplayFromSlider();
        return;
    }

    auto digitsOnly = text.retainCharacters("0123456789");
    if (digitsOnly.isEmpty())
    {
        updateBpmDisplayFromSlider();
        return;
    }

    auto enteredValue = digitsOnly.getIntValue();
    setBpmValue(static_cast<double>(enteredValue));
    updateBpmDisplayFromSlider();
}

void ChordMelodyTabComponent::adjustBpmValue(int delta)
{
    auto modifiers = juce::ModifierKeys::getCurrentModifiers();
    int step = delta;

    if (modifiers.isShiftDown())
        step *= 5;
    else if (modifiers.isCommandDown() || modifiers.isCtrlDown())
        step *= 10;

    setBpmValue(bpmSlider.getValue() + static_cast<double>(step));
}