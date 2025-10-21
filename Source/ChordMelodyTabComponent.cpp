#include "ChordMelodyTabComponent.h"
#include "PluginProcessor.h"
#include <algorithm>
#include <utility>

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

    constexpr int bottomControlsHeight = 90;
    constexpr int promptEditorHeight = 125;
    constexpr int topControlRowHeight = 30;
    constexpr int topControlSpacing = 5;
    constexpr int promptToControlsSpacing = 10;
    constexpr int topControlsHeight = promptEditorHeight + promptToControlsSpacing
        + topControlRowHeight + topControlSpacing + topControlRowHeight;
    constexpr int dragStartDistance = 10;

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
} // End anonymous namespace


// Drag handle implementation
ChordMelodyTabComponent::MidiDragHandle::MidiDragHandle(juce::DragAndDropContainer& containerRef,
    const juce::String& labelText,
    std::function<juce::File()> prepareFn)
    : container(containerRef)
    , text(labelText)
    , prepareFileCallback(std::move(prepareFn))
{
    setMouseCursor(juce::MouseCursor::DraggingHandCursor);
    setRepaintsOnMouseActivity(true);
}

void ChordMelodyTabComponent::MidiDragHandle::setText(const juce::String& newText)
{
    if (text == newText)
        return;

    text = newText;
    repaint();
}

juce::String ChordMelodyTabComponent::MidiDragHandle::getText() const
{
    return text;
}

void ChordMelodyTabComponent::MidiDragHandle::setTooltipText(const juce::String& newTooltipText)
{
    if (tooltipText == newTooltipText)
        return;

    tooltipText = newTooltipText;
}

void ChordMelodyTabComponent::MidiDragHandle::setDragEnabled(bool shouldBeEnabled)
{
    if (isEnabled() == shouldBeEnabled)
        return;

    juce::Component::setEnabled(shouldBeEnabled);
}

void ChordMelodyTabComponent::MidiDragHandle::paint(juce::Graphics& g)
{
    auto area = getLocalBounds().toFloat();
    const float cornerRadius = 6.0f;

    juce::Colour fill = buttonBaseColour;
    if (!isEnabled())
        fill = fill.withMultipliedAlpha(0.35f);
    else if (isMouseDown || dragStarted)
        fill = buttonDownColour;
    else if (isHover)
        fill = buttonBaseColour.brighter(0.25f);

    g.setColour(fill);
    g.fillRoundedRectangle(area, cornerRadius);

    g.setColour(panelOutlineColour.withAlpha(isEnabled() ? 0.45f : 0.2f));
    g.drawRoundedRectangle(area, cornerRadius, 1.0f);

    auto textColour = isEnabled() ? mainTextColour : mainTextColour.withMultipliedAlpha(0.4f);
    g.setColour(textColour);
    g.setFont(juce::Font(14.0f, juce::Font::bold));
    g.drawFittedText(text, getLocalBounds().reduced(10, 0), juce::Justification::centred, 2);

    auto iconArea = getLocalBounds().reduced(12, 8).removeFromLeft(24).toFloat();
    juce::Path arrows;
    const float centreX = iconArea.getCentreX();
    const float centreY = iconArea.getCentreY();
    const float arrowLength = juce::jmin(iconArea.getWidth(), iconArea.getHeight()) * 0.45f;
    const float arrowHead = arrowLength * 0.45f;

    auto drawArrow = [&](float dx, float dy)
        {
            juce::Path p;
            juce::Point<float> start(centreX - dx * arrowLength, centreY - dy * arrowLength);
            juce::Point<float> end(centreX + dx * arrowLength, centreY + dy * arrowLength);
            p.startNewSubPath(start);
            p.lineTo(end);

            juce::Point<float> head1 = end - juce::Point<float>(dx * arrowHead - dy * arrowHead, dy * arrowHead + dx * arrowHead);
            juce::Point<float> head2 = end - juce::Point<float>(dx * arrowHead + dy * arrowHead, dy * arrowHead - dx * arrowHead);
            p.startNewSubPath(end);
            p.lineTo(head1);
            p.startNewSubPath(end);
            p.lineTo(head2);
            arrows.addPath(p);
        };

    drawArrow(1.0f, 0.0f);
    drawArrow(-1.0f, 0.0f);
    drawArrow(0.0f, 1.0f);
    drawArrow(0.0f, -1.0f);

    g.setColour(textColour.withMultipliedAlpha(0.7f));
    g.strokePath(arrows, juce::PathStrokeType(1.3f));
}

void ChordMelodyTabComponent::MidiDragHandle::mouseEnter(const juce::MouseEvent&)
{
    if (!isEnabled())
        return;

    isHover = true;
    repaint();
}

void ChordMelodyTabComponent::MidiDragHandle::mouseExit(const juce::MouseEvent&)
{
    isHover = false;
    isMouseDown = false;
    repaint();
}

void ChordMelodyTabComponent::MidiDragHandle::mouseDown(const juce::MouseEvent&)
{
    if (!isEnabled())
        return;

    isMouseDown = true;
    dragStarted = false;
    repaint();
}

void ChordMelodyTabComponent::MidiDragHandle::mouseUp(const juce::MouseEvent&)
{
    isMouseDown = false;
    dragStarted = false;
    repaint();
}

void ChordMelodyTabComponent::MidiDragHandle::mouseDrag(const juce::MouseEvent& event)
{
    if (!isEnabled() || dragStarted || !isMouseDown)
        return;

    if (event.getDistanceFromDragStart() < dragStartDistance)
        return;

    dragStarted = true;
    isMouseDown = false;
    repaint();
    beginExternalDrag();
}

void ChordMelodyTabComponent::MidiDragHandle::enablementChanged()
{
    juce::Component::enablementChanged();

    if (isEnabled())
    {
        setMouseCursor(juce::MouseCursor::DraggingHandCursor);
    }
    else
    {
        setMouseCursor(juce::MouseCursor::NormalCursor);
        isHover = false;
        isMouseDown = false;
        dragStarted = false;
    }

    repaint();
}

juce::String ChordMelodyTabComponent::MidiDragHandle::getTooltip() const
{
    return tooltipText;
}

void ChordMelodyTabComponent::MidiDragHandle::beginExternalDrag()
{
    if (!prepareFileCallback)
        return;

    juce::File file = prepareFileCallback();
    if (!file.existsAsFile())
        return;

    juce::StringArray files;
    files.add(file.getFullPathName());
    container.performExternalDragDropOfFiles(files, false);
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
    promptEditor.onTextChange = [this]() { updateUiForCurrentState(); };

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

    addAndMakeVisible(clearCanvasButton);
    clearCanvasButton.setButtonText("Limpiar Lienzo");
    stylizeButton(clearCanvasButton);
    clearCanvasButton.setTooltip(juce::String::fromUTF8("Detiene la reproducción y borra acordes/melodías actuales."));

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

    chordsDragHandle = std::make_unique<MidiDragHandle>(*this,
        juce::String::fromUTF8("Arrastrar Acordes"),
        [this]() { return prepareChordMidiFileForDrag(); });
    chordsDragHandle->setTooltipText(juce::String::fromUTF8("Exporta y arrastra el MIDI de acordes."));
    addAndMakeVisible(*chordsDragHandle);

    melodyDragHandle = std::make_unique<MidiDragHandle>(*this,
        juce::String::fromUTF8("Arrastrar Melodia"),
        [this]() { return prepareMelodyMidiFileForDrag(); });
    melodyDragHandle->setTooltipText(juce::String::fromUTF8("Exporta y arrastra el MIDI de melodía."));
    addAndMakeVisible(*melodyDragHandle);

    // === PIANO ROLL ===
    addAndMakeVisible(pianoRollComponent);
    pianoRollComponent.setContentChangedCallback([this]() { handlePianoRollContentChanged(); });

    // === LOGICA DE LOS BOTONES ===
    generateChordsButton.onClick = [this]
        {
            generateChordsFromCurrentPrompt();
        };

    clearCanvasButton.onClick = [this]
        {
            clearGeneratedContent();
        };

    // Crear y configurar el botón "Me gusta"
    likeButton = std::make_unique<juce::ImageButton>();
    auto likeImg = juce::ImageCache::getFromMemory(BinaryData::corazon_png, BinaryData::corazon_pngSize);
    likeButton->setImages(false, true, true,
        likeImg, 1.0f, juce::Colours::transparentBlack,
        likeImg, 0.85f, juce::Colours::transparentBlack,
        likeImg, 0.7f, juce::Colours::transparentBlack);
    likeButton->onClick = [this] {
        if (pianoRollComponent.getNotes().isEmpty())
        {
            showNotification(juce::String::fromUTF8("No hay datos para enviar feedback."));
            return;
        }

        lastGeneratedChordsData = rebuildMusicDictFromPianoRoll();
        sendEditedMusicToPython();
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
        if (pianoRollComponent.getNotes().isEmpty())
        {
            showNotification(juce::String::fromUTF8("No hay datos para enviar feedback."));
            return;
        }

        lastGeneratedChordsData = rebuildMusicDictFromPianoRoll();
        sendEditedMusicToPython();
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
    notificationLabel.setInterceptsMouseClicks(false, false);
    notificationLabel.setMouseClickGrabsKeyboardFocus(false);
    notificationLabel.setAlpha(0.0f);

    generateMelodyButton.onClick = [this]
        {
            py::dict currentSnapshot = rebuildMusicDictFromPianoRoll();
            lastGeneratedChordsData = currentSnapshot;

            const bool hasChordData = hasUsableChordContent(currentSnapshot);
            const int bpm = (int)bpmSlider.getValue();

            if (hasChordData)
            {
                DBG("Enviando datos a Python para generar melodia...");

                py::list chords = currentSnapshot["acordes"];
                py::list rhythm = currentSnapshot["ritmo"];

                juce::String root = lastDetectedRoot.isNotEmpty() ? lastDetectedRoot : juce::String("C");
                juce::String mode = lastDetectedMode.isNotEmpty() ? lastDetectedMode : juce::String("major");

                if (currentSnapshot.contains("raiz"))
                    root = utf8String(currentSnapshot["raiz"].cast<std::string>());
                if (currentSnapshot.contains("modo"))
                    mode = utf8String(currentSnapshot["modo"].cast<std::string>());

                auto melodyData = audioProcessor.pythonManager->generateMelodyData(chords, rhythm, root, mode, bpm);

                if (melodyData.empty() || (melodyData.contains("error") && !melodyData["error"].cast<std::string>().empty()))
                {
                    std::string errorMessage = melodyData.contains("error") ? melodyData["error"].cast<std::string>() : "Diccionario vacio";
                    DBG("!!! Error al generar la melodia desde Python: " + utf8String(errorMessage));
                    showNotification(juce::String::fromUTF8("No se pudo generar la melodía. Revisa la progresión."));
                    return;
                }

                DBG("Melodia generada con exito!");
                py::dict updatedData = deepCopyMusicDict(currentSnapshot);
                py::object newMelody = melodyData.contains("melodia") ? deepCopyPyObject(melodyData["melodia"]) : py::object();

                if (!newMelody.is_none())
                {
                    py::gil_scoped_acquire acquire;
                    updatedData["melodia"] = newMelody;
                }

                applyMusicResult(std::move(updatedData), true);
            }
            else
            {
                auto finalPrompt = buildPromptForRequest();
                if (finalPrompt.isEmpty())
                {
                    showNotification(juce::String::fromUTF8("Escribe un prompt o genera acordes primero."));
                    return;
                }

                lastPromptText = promptEditor.getText();
                DBG(juce::String::fromUTF8(u8"Generando melodía únicamente desde el prompt: ") + finalPrompt);

                const int chordLimit = getSelectedChordLimit();
                auto melodyResult = audioProcessor.pythonManager->generateMelodyFromPrompt(finalPrompt, chordLimit, bpm);

                if (melodyResult.empty() || (melodyResult.contains("error") && !melodyResult["error"].cast<std::string>().empty()))
                {
                    std::string errorMessage = melodyResult.contains("error") ? melodyResult["error"].cast<std::string>() : "Diccionario vacio";
                    DBG("!!! Error al generar la melodia desde prompt: " + utf8String(errorMessage));
                    showNotification(juce::String::fromUTF8("No se pudo generar la melodía desde el prompt."));
                    return;
                }

                DBG("Melodia generada con exito desde el prompt!");
                applyMusicResult(std::move(melodyResult), true);
            }
        };

    auto configurePlaybackButton = [this](juce::TextButton& targetButton, bool includeChords, bool includeMelody)
        {
            auto* buttonPtr = &targetButton;
            targetButton.onClick = [this, includeChords, includeMelody, buttonPtr]()
                {
                    if (audioProcessor.isPlayingSequence())
                    {
                        audioProcessor.stopPlayback();
                        stopTimer(ChordMelodyTabComponent::playbackMonitorTimerId);
                        handlePlaybackFinished();

                    }

                    if (prepareAndPlaySequence(includeChords, includeMelody))
                        setActivePlaybackButton(buttonPtr);
                };
        };

    configurePlaybackButton(playAllButton, true, true);
    configurePlaybackButton(playChordsButton, true, false);
    configurePlaybackButton(playMelodyButton, false, true);

    stopButton.onClick = [this]
        {
            audioProcessor.stopPlayback();
            stopTimer(ChordMelodyTabComponent::playbackMonitorTimerId);
            handlePlaybackFinished();
        };

    transposeUpButton.onClick = [this] { transpose(1); };
    transposeDownButton.onClick = [this] { transpose(-1); };

    exportChordsButton.onClick = [this]
        {
            auto file = exportChordsToFile(true, true);
            if (file.existsAsFile())
                DBG("Acordes exportados a " + file.getFullPathName());
        };

    exportMelodyButton.onClick = [this]
        {
            auto file = exportMelodyToFile(true, true);
            if (file.existsAsFile())
                DBG("Melodia exportada a " + file.getFullPathName());
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

    auto bottomArea = bounds.removeFromBottom(bottomControlsHeight);
    auto topArea = bounds.removeFromTop(topControlsHeight);
    bounds.removeFromTop(10);
    auto pianoArea = bounds;

    auto topWorking = topArea;
    auto rightColumn = topWorking.removeFromRight(200).reduced(5, 0);
    auto leftColumn = topWorking;
    leftColumn.removeFromRight(10);
    auto promptArea = leftColumn.removeFromTop(promptEditorHeight);
    leftColumn.removeFromTop(promptToControlsSpacing);
    auto generationArea = leftColumn.removeFromTop(topControlRowHeight);
    leftColumn.removeFromTop(topControlSpacing);
    auto clearArea = leftColumn.removeFromTop(topControlRowHeight);
    auto leftColumnArea = promptArea;
    if (!generationArea.isEmpty())
        leftColumnArea = leftColumnArea.getUnion(generationArea);
    if (!clearArea.isEmpty())
        leftColumnArea = leftColumnArea.getUnion(clearArea);

    auto bottomWorking = bottomArea;
    auto playbackRow = bottomWorking.removeFromTop(40);
    auto exportRow = bottomWorking.removeFromBottom(40);

    drawPanel(expanded(leftColumnArea, 12, 8));
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
    auto bottomButtonsArea = bounds.removeFromBottom(bottomControlsHeight); // 40px para cada fila + 10px de espacio

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

    // Distribuimos los controles de Exportar con botones más compactos y manijas de arrastre
    auto chordsExportArea = exportRow.removeFromLeft(exportRow.getWidth() / 2);
    auto melodyExportArea = exportRow;

    auto layoutExportSection = [](juce::Rectangle<int> area, juce::Component& button, MidiDragHandle* dragHandle)
        {
            if (area.isEmpty())
            {
                button.setBounds({});
                if (dragHandle)
                    dragHandle->setBounds({});
                return;
            }

            const int minWidth = 90;
            const int maxWidth = 150;
            int buttonWidth = juce::jmax(minWidth, juce::jmin(maxWidth, area.getWidth() / 3));
            buttonWidth = juce::jmin(buttonWidth, area.getWidth());
            auto buttonArea = area.removeFromLeft(buttonWidth);
            button.setBounds(buttonArea.reduced(5, 2));

            area.removeFromLeft(4);
            if (dragHandle)
                dragHandle->setBounds(area.reduced(5, 2));
        };

    layoutExportSection(chordsExportArea, exportChordsButton, chordsDragHandle ? chordsDragHandle.get() : nullptr);
    layoutExportSection(melodyExportArea, exportMelodyButton, melodyDragHandle ? melodyDragHandle.get() : nullptr);


    // --- 2. ÁREA SUPERIOR: Prompt y todos los controles ---
    auto topArea = bounds.removeFromTop(topControlsHeight); // Altura para el prompt y los botones de abajo

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
    promptEditor.setBounds(leftColumn.removeFromTop(promptEditorHeight));

    leftColumn.removeFromTop(promptToControlsSpacing); // Espacio

    // Los botones de generar van debajo del prompt
    auto generationArea = leftColumn.removeFromTop(topControlRowHeight);
    const int generationButtonWidth = juce::jmax(1, generationArea.getWidth() / 2);
    auto chordsArea = generationArea.removeFromLeft(generationButtonWidth);
    generateChordsButton.setBounds(chordsArea.reduced(5, 2));
    generateMelodyButton.setBounds(generationArea.reduced(5, 2));

    leftColumn.removeFromTop(topControlSpacing);

    auto clearArea = leftColumn.removeFromTop(topControlRowHeight);
    if (!clearArea.isEmpty())
        clearCanvasButton.setBounds(clearArea.reduced(5, 2));
    else
        clearCanvasButton.setBounds({});


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

// ... (Resto de las funciones: transpose, prepareAndPlaySequence, etc. SIN CAMBIOS) ...

// Asegúrate de que todas las funciones desde transpose() hasta el final del archivo
// se mantengan EXACTAMENTE como estaban en el archivo original que subiste.
// dentro de mouseDrag().

// Pegar aquí el resto de las funciones desde transpose() hasta el final del archivo original
void ChordMelodyTabComponent::transpose(int semitones)
{
    if (lastGeneratedChordsData.empty() && pianoRollComponent.getNotes().isEmpty())
        return;

    lastGeneratedChordsData = rebuildMusicDictFromPianoRoll();
    if (lastGeneratedChordsData.empty())
        return;

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
    sendEditedMusicToPython();
    repaint();
}

bool ChordMelodyTabComponent::prepareAndPlaySequence(bool includeChords, bool includeMelody)
{
    if (!includeChords && !includeMelody)
        return false;

    const auto& noteList = pianoRollComponent.getNotes();
    if (noteList.isEmpty())
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

    for (int i = 0; i < noteList.size(); ++i)
    {
        const auto& note = noteList.getReference(i);
        if (note.midiNote <= 0 || note.duration <= 0.0f)
            continue;

        if (note.isChordNote)
            hasChordData = true;
        else
            hasMelodyData = true;
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

    auto createEventsForNote = [&](int midiNote, double noteStartBeats, double noteDurationBeats)
        {
            noteDurationBeats = juce::jmax(0.0, noteDurationBeats);
            if (noteDurationBeats <= 0.0)
                return;

            noteStartBeats = juce::jmax(0.0, noteStartBeats);

            double startTimeSecs = noteStartBeats * secondsPerBeat;
            double endTimeSecs = (noteStartBeats + noteDurationBeats) * secondsPerBeat;
            int startSample = static_cast<int>(startTimeSecs * sampleRate);
            int endSample = static_cast<int>(endTimeSecs * sampleRate);

            if (endSample <= startSample)
                return;

            const int safeMidiNote = juce::jlimit(0, 127, midiNote);
            if (safeMidiNote <= 0)
                return;

            eventList.push_back({ startSample, juce::MidiMessage::noteOn(1, safeMidiNote, (juce::uint8)100) });
            eventList.push_back({ endSample, juce::MidiMessage::noteOff(1, safeMidiNote) });
        };

    for (int i = 0; i < noteList.size(); ++i)
    {
        const auto& note = noteList.getReference(i);

        if (note.midiNote <= 0 || note.duration <= 0.0f)
            continue;

        if ((note.isChordNote && !includeChords) || (!note.isChordNote && !includeMelody))
            continue;

        createEventsForNote(note.midiNote, (double)note.startTime, (double)note.duration);
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
    startTimer(ChordMelodyTabComponent::playbackMonitorTimerId, 30);
    return true;
}

void ChordMelodyTabComponent::resetPlaybackButtonStates()
{
    activePlaybackButton = nullptr;
    playAllButton.setButtonText("Reproducir Todo");
    playChordsButton.setButtonText("Reproducir Acordes");
    playMelodyButton.setButtonText("Reproducir Melodia");
}

void ChordMelodyTabComponent::setActivePlaybackButton(juce::TextButton* newButton)
{
    if (activePlaybackButton == newButton && newButton != nullptr)
        return;

    resetPlaybackButtonStates();

    if (newButton == nullptr)
        return;

    activePlaybackButton = newButton;

    if (activePlaybackButton == &playAllButton)
        activePlaybackButton->setButtonText("Reproduciendo Todo...");
    else if (activePlaybackButton == &playChordsButton)
        activePlaybackButton->setButtonText("Reproduciendo Acordes...");
    else if (activePlaybackButton == &playMelodyButton)
        activePlaybackButton->setButtonText("Reproduciendo Melodia...");
    else
        activePlaybackButton->setButtonText("Reproduciendo...");
}

void ChordMelodyTabComponent::setBpmValue(double newValue, juce::NotificationType notification)
{
    auto limitedValue = juce::jlimit(bpmSlider.getMinimum(), bpmSlider.getMaximum(), newValue);
    bpmSlider.setValue(limitedValue, notification);
}

void ChordMelodyTabComponent::showNotification(const juce::String& message)
{
    notificationLabel.setText(message, juce::dontSendNotification);
    notificationLabel.setAlpha(1.0f);
    startTimer(ChordMelodyTabComponent::notificationTimerId, 2000);
}

void ChordMelodyTabComponent::timerCallback(int timerId)
{
    if (timerId == ChordMelodyTabComponent::notificationTimerId)
    {
        notificationLabel.setAlpha(0.0f);
        stopTimer(ChordMelodyTabComponent::notificationTimerId);
    }
    else if (timerId == ChordMelodyTabComponent::playbackMonitorTimerId)
    {
        if (!audioProcessor.isPlayingSequence())
        {
            stopTimer(ChordMelodyTabComponent::playbackMonitorTimerId);
            handlePlaybackFinished();
        }
    }
}

void ChordMelodyTabComponent::handlePlaybackFinished()
{
    pianoRollComponent.stopPlayback();
    setActivePlaybackButton(nullptr);
    showNotification(juce::String::fromUTF8("Reproducción finalizada."));
}

void ChordMelodyTabComponent::generateChordsFromCurrentPrompt()
{
    auto finalPrompt = buildPromptForRequest();
    if (finalPrompt.isEmpty())
    {
        showNotification(juce::String::fromUTF8("Escribe un prompt para generar acordes."));
        return;
    }

    lastPromptText = promptEditor.getText();
    DBG("Prompt final enviado a Python: " + finalPrompt);

    const int chordLimit = getSelectedChordLimit();
    py::list melodyForRequest;
    py::object preservedMelody;
    bool hasActiveMelody = false;

    py::dict currentSnapshot = rebuildMusicDictFromPianoRoll();
    lastGeneratedChordsData = currentSnapshot;
    {
        py::gil_scoped_acquire acquire;
        if (!currentSnapshot.is_none() && currentSnapshot.contains("melodia"))
        {
            py::object melodyObject = currentSnapshot["melodia"];
            if (!melodyObject.is_none() && py::isinstance<py::list>(melodyObject))
            {
                py::object requestCopy = deepCopyPyObject(melodyObject);
                py::object preservedCopy = deepCopyPyObject(melodyObject);

                if (!requestCopy.is_none())
                {
                    melodyForRequest = requestCopy.cast<py::list>();
                    hasActiveMelody = melodyForRequest.size() > 0;
                }

                preservedMelody = preservedCopy;
            }
        }
    }

    const int bpmForRequest = (int)bpmSlider.getValue();
    auto chordsData = hasActiveMelody
        ? audioProcessor.pythonManager->generateMusicData(finalPrompt, chordLimit, melodyForRequest, bpmForRequest)
        : audioProcessor.pythonManager->generateMusicData(finalPrompt, chordLimit);

    if (chordsData.empty() || (chordsData.contains("error") && !chordsData["error"].cast<std::string>().empty()))
    {
        std::string errorMessage = chordsData.contains("error") ? chordsData["error"].cast<std::string>() : "Diccionario vacio";
        DBG("!!! Error desde Python: " + utf8String(errorMessage));
        showNotification(juce::String::fromUTF8("No se pudieron generar acordes. Revisa el prompt."));
        return;
    }

    py::dict finalChordData = deepCopyMusicDict(chordsData);
    if (hasActiveMelody && !preservedMelody.is_none())
    {
        py::gil_scoped_acquire acquire;
        finalChordData["melodia"] = preservedMelody;
    }

    juce::String modeSummary;
    if (finalChordData.contains("tipo_generacion"))
    {
        py::object modeObj = finalChordData["tipo_generacion"];
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

    if (finalChordData.contains("fuente_generacion"))
    {
        py::object detailObj = finalChordData["fuente_generacion"];
        if (!detailObj.is_none())
        {
            const std::string detail = detailObj.cast<std::string>();
            if (!detail.empty())
                DBG(utf8String(u8"Detalle de origen de progresión: ") + utf8String(detail));
        }
    }

    applyMusicResult(std::move(finalChordData), true);
}

void ChordMelodyTabComponent::updateUiForCurrentState()
{
    const bool hasData = !lastGeneratedChordsData.empty();
    const bool hasChordContent = hasUsableChordContent(lastGeneratedChordsData);
    const bool hasMelody = hasData && lastGeneratedChordsData.contains("melodia");
    const bool promptAvailable = promptEditor.getText().trim().isNotEmpty();

    generateMelodyButton.setEnabled(hasChordContent || promptAvailable);
    exportChordsButton.setEnabled(hasChordContent);
    exportMelodyButton.setEnabled(hasMelody);
    if (chordsDragHandle)
        chordsDragHandle->setDragEnabled(hasChordContent);
    if (melodyDragHandle)
        melodyDragHandle->setDragEnabled(hasMelody);
    transposeUpButton.setEnabled(hasData);
    transposeDownButton.setEnabled(hasData);
    clearCanvasButton.setEnabled(hasData || !pianoRollComponent.getNotes().isEmpty() || promptAvailable);
}

juce::File ChordMelodyTabComponent::exportChordsToFile(bool showDialog, bool notifyOnFailure)
{
    const auto& musicEntries = pianoRollComponent.getMusicData();
    const bool hasChordNotes = std::any_of(musicEntries.begin(), musicEntries.end(), [](const NoteInfo& info)
        {
            if (info.isMelody)
                return false;

            for (int midi : info.chordMidiValues)
                if (midi > 0)
                    return true;

            return false;
        });

    if (!hasChordNotes)
    {
        if (notifyOnFailure)
            showNotification(juce::String::fromUTF8("No hay acordes para exportar."));
        return {};
    }

    lastGeneratedChordsData = rebuildMusicDictFromPianoRoll();
    sendEditedMusicToPython();

    const int currentBpm = (int)bpmSlider.getValue();
    juce::String result = audioProcessor.pythonManager->exportChords(lastGeneratedChordsData, currentBpm);

    if (showDialog)
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::InfoIcon, "Exportar Acordes", result);

    auto exportedFile = audioProcessor.pythonManager->getLastExportedChordsFile();
    if (!exportedFile.existsAsFile())
    {
        if (notifyOnFailure && !showDialog)
            showNotification(result);
        return {};
    }

    return exportedFile;
}

juce::File ChordMelodyTabComponent::exportMelodyToFile(bool showDialog, bool notifyOnFailure)
{
    const auto& musicEntries = pianoRollComponent.getMusicData();
    const bool hasMelodyNotes = std::any_of(musicEntries.begin(), musicEntries.end(), [](const NoteInfo& info)
        {
            return info.isMelody && info.midiValue > 0 && info.duration > 0.0;
        });

    if (!hasMelodyNotes)
    {
        if (notifyOnFailure)
            showNotification(juce::String::fromUTF8("No hay melodías para exportar."));
        return {};
    }

    lastGeneratedChordsData = rebuildMusicDictFromPianoRoll();
    sendEditedMusicToPython();

    const int currentBpm = (int)bpmSlider.getValue();
    juce::String result = audioProcessor.pythonManager->exportMelody(lastGeneratedChordsData, currentBpm);

    if (showDialog)
        juce::AlertWindow::showMessageBoxAsync(juce::AlertWindow::InfoIcon, "Exportar Melodia", result);

    auto exportedFile = audioProcessor.pythonManager->getLastExportedMelodyFile();
    if (!exportedFile.existsAsFile())
    {
        if (notifyOnFailure && !showDialog)
            showNotification(result);
        return {};
    }

    return exportedFile;
}

juce::File ChordMelodyTabComponent::prepareChordMidiFileForDrag()
{
    return exportChordsToFile(false, true);
}

juce::File ChordMelodyTabComponent::prepareMelodyMidiFileForDrag()
{
    return exportMelodyToFile(false, true);
}

py::dict ChordMelodyTabComponent::rebuildMusicDictFromPianoRoll()
{
    py::gil_scoped_acquire acquire;

    py::dict snapshot = lastGeneratedChordsData.empty() ? py::dict() : deepCopyMusicDict(lastGeneratedChordsData);
    pianoRollComponent.writeCurrentStateToPyDict(snapshot);
    return snapshot;
}

void ChordMelodyTabComponent::handlePianoRollContentChanged()
{
    lastGeneratedChordsData = rebuildMusicDictFromPianoRoll();

    pushStateToHistory(lastGeneratedChordsData);
    updateUiForCurrentState();
    repaint();
    sendEditedMusicToPython();
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

    sendEditedMusicToPython();
    updateUiForCurrentState();
    repaint();
    updateUndoRedoButtonStates();
}

void ChordMelodyTabComponent::updateUndoRedoButtonStates()
{
    undoButton.setEnabled(historyCurrentIndex > 0);
    redoButton.setEnabled(historyCurrentIndex >= 0 && historyCurrentIndex < (int)historyStates.size() - 1);
}

void ChordMelodyTabComponent::clearGeneratedContent()
{
    audioProcessor.stopPlayback();
    stopTimer(playbackMonitorTimerId);
    pianoRollComponent.stopPlayback();
    resetPlaybackButtonStates();

    historyStates.clear();
    historyCurrentIndex = -1;
    lastGeneratedChordsData = py::dict();
    lastDetectedRoot.clear();
    lastDetectedMode.clear();
    lastDetectedStyle.clear();

    py::dict empty;
    pianoRollComponent.setMusicData(empty);

    updateUiForCurrentState();
    updateUndoRedoButtonStates();
    repaint();

    showNotification(juce::String::fromUTF8("Lienzo limpio. Genera acordes o melodía."));

    sendEditedMusicToPython();
}

juce::String ChordMelodyTabComponent::buildPromptForRequest() const
{
    juce::String prompt = promptEditor.getText().trim();
    if (prompt.isEmpty())
        return {};

    if (genreComboBox.getSelectedId() != 1)
    {
        juce::String selectedGenre = genreComboBox.getText();
        if (!prompt.containsIgnoreCase(selectedGenre))
            prompt = selectedGenre + " " + prompt;
    }

    return prompt;
}

int ChordMelodyTabComponent::getSelectedChordLimit() const
{
    switch (chordCountComboBox.getSelectedId())
    {
    case 2: return 4;
    case 3: return 6;
    case 4: return 8;
    default: break;
    }
    return -1;
}

bool ChordMelodyTabComponent::hasUsableChordContent(const py::dict& data) const
{
    if (data.empty() || !data.contains("acordes") || !data.contains("ritmo"))
        return false;

    py::list chords = data["acordes"];
    for (auto item : chords)
    {
        if (py::isinstance<py::list>(item))
        {
            py::list noteList = item.cast<py::list>();
            for (auto noteObj : noteList)
            {
                std::string noteStr = noteObj.cast<std::string>();
                if (!noteStr.empty() && noteStr != "0")
                    return true;
            }
        }
        else if (py::isinstance<py::tuple>(item))
        {
            py::tuple noteTuple = item.cast<py::tuple>();
            for (auto noteObj : noteTuple)
            {
                std::string noteStr = noteObj.cast<std::string>();
                if (!noteStr.empty() && noteStr != "0")
                    return true;
            }
        }
        else if (py::isinstance<py::dict>(item))
        {
            py::dict chordDict = item.cast<py::dict>();
            if (chordDict.contains("voicing"))
            {
                py::object voicing = chordDict["voicing"];
                if (py::isinstance<py::list>(voicing))
                {
                    for (auto noteObj : voicing.cast<py::list>())
                    {
                        std::string noteStr = noteObj.cast<std::string>();
                        if (!noteStr.empty() && noteStr != "0")
                            return true;
                    }
                }
            }
        }
        else if (py::isinstance<py::str>(item))
        {
            std::string chordStr = item.cast<std::string>();
            if (!chordStr.empty() && chordStr != "0" && chordStr.rfind("SN_", 0) != 0)
                return true;
        }
    }

    return false;
}

void ChordMelodyTabComponent::applyMusicResult(py::dict data, bool pushHistory)
{
    lastGeneratedChordsData = std::move(data);

    auto extractField = [&](const char* key) -> juce::String
        {
            if (lastGeneratedChordsData.contains(key))
            {
                py::object obj = lastGeneratedChordsData[key];
                if (!obj.is_none())
                    return utf8String(obj.cast<std::string>());
            }
            return {};
        };

    lastDetectedRoot = extractField("raiz");
    lastDetectedMode = extractField("modo");
    lastDetectedStyle = extractField("estilo");

    if (lastGeneratedChordsData.contains("bpm"))
    {
        try
        {
            setBpmValue(lastGeneratedChordsData["bpm"].cast<int>());
        }
        catch (...)
        {
        }
    }

    pianoRollComponent.setMusicData(lastGeneratedChordsData);
    updateUiForCurrentState();

    if (pushHistory)
        pushStateToHistory(lastGeneratedChordsData);
    else
        updateUndoRedoButtonStates();

    repaint();
}


py::dict ChordMelodyTabComponent::deepCopyMusicDict(const py::dict& source)
{
    py::gil_scoped_acquire acquire;
    static py::object deepcopyFunc = py::module::import("copy").attr("deepcopy");
    py::object result = deepcopyFunc(source);
    return result.cast<py::dict>();
}

py::object ChordMelodyTabComponent::deepCopyPyObject(const py::object& source)
{
    py::gil_scoped_acquire acquire;
    static py::object deepcopyFunc = py::module::import("copy").attr("deepcopy");
    return deepcopyFunc(source);
}

void ChordMelodyTabComponent::sendEditedMusicToPython()
{
    if (audioProcessor.pythonManager == nullptr)
        return;

    audioProcessor.pythonManager->updateEditedMusic(lastGeneratedChordsData);
}