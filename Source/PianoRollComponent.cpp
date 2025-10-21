#include "PianoRollComponent.h"
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <utility>
#include <cmath>
#include <limits>

namespace
{
    constexpr int kMaxDisplayMidiNote = 143; // B10 (mantener sincronizado con PianoRollComponent::defaultHighestNote)
    constexpr float kBasePixelsPerBeat = 100.0f;
    constexpr float kMinHorizontalZoom = 0.25f;
    constexpr float kMaxHorizontalZoom = 6.0f;
    constexpr int kBeatsPerBar = 4;
    constexpr double kDefaultQuantiseStepBeats = 0.25;
    constexpr float kResizeHandleWidthPixels = 8.0f;
    constexpr double kMinimumNoteDurationBeats = 0.0625;
    constexpr double kRestMergeTolerance = 1.0e-4;

    juce::String formatBeats(double beats)
    {
        if (!std::isfinite(beats))
            beats = 0.0;

        juce::String text(beats, 6);
        text = text.trimCharactersAtEnd("0").trimCharactersAtEnd(".");
        if (text.isEmpty())
            text = "0";
        return text;
    }
}

// --- Función de ayuda para convertir nombres de nota ("C4", "G#3") a números MIDI ---
int noteNameToMidi(const std::string& noteName)
{
    if (noteName.empty() || noteName == "0") return -1;

    static const std::map<char, int> noteValues = {
        {'C', 0}, {'D', 2}, {'E', 4}, {'F', 5}, {'G', 7}, {'A', 9}, {'B', 11}
    };

    char baseNote = std::toupper(noteName[0]);
    if (noteValues.find(baseNote) == noteValues.end()) return -1;

    int midiNote = noteValues.at(baseNote);
    int pos = 1;

    if (pos < noteName.length())
    {
        if (noteName[pos] == '#') {
            midiNote++;
            pos++;
        }
        else if (noteName[pos] == 'b' || noteName[pos] == '-') {
            midiNote--;
            pos++;
        }
    }

    if (pos >= noteName.length() || !std::isdigit(noteName[pos])) return -1;

    int octave = std::stoi(noteName.substr(pos));
    midiNote += (octave + 1) * 12;

    return midiNote;
}

// --- Función auxiliar para convertir un número MIDI a una etiqueta de nota legible ---
juce::String midiToNoteName(int midiNote)
{
    if (midiNote < 0 || midiNote > kMaxDisplayMidiNote)
        return {};

    static const juce::StringArray noteNames({ "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" });
    const int octave = (midiNote / 12) - 1;
    const int index = midiNote % 12;

    return noteNames[index] + juce::String(octave);
}

PianoRollComponent::PianoRollComponent() {}
PianoRollComponent::~PianoRollComponent() {}

void PianoRollComponent::setContentChangedCallback(std::function<void()> callback)
{
    contentChangedCallback = std::move(callback);
}

void PianoRollComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff3c3c3c));

    const int keyWidth = getKeyWidth();
    const int lowestNote = displayLowestNote;
    const int highestNote = displayHighestNote;
    const int numNotes = juce::jmax(1, visibleNoteCount);
    const float noteHeight = numNotes > 0 ? (float)getHeight() / (float)numNotes : (float)getHeight();

    // Fondo para la zona del teclado lateral
    juce::Rectangle<float> keyArea(0.0f, 0.0f, (float)keyWidth, (float)getHeight());
    g.setColour(juce::Colour(0xff2b2b2b));
    g.fillRect(keyArea);

    // Dibuja el fondo del piano roll
    for (int note = lowestNote; note <= highestNote; ++note)
    {
        const bool isBlackKey = (note % 12 == 1 || note % 12 == 3 || note % 12 == 6 || note % 12 == 8 || note % 12 == 10);
        const bool isC = (note % 12 == 0);

        const float y = (highestNote - note) * noteHeight;

        // Dibujo del teclado lateral estilo FL Studio
        juce::Colour keyColour = isBlackKey ? juce::Colour(0xff1f1f1f) : juce::Colour(0xff3d3d3d);
        if (isC)
            keyColour = keyColour.brighter(0.15f);

        g.setColour(keyColour);
        g.fillRect(0.0f, y, (float)keyWidth, noteHeight);

        // Etiqueta de la nota (solo en teclas blancas para claridad)
        if (!isBlackKey || isC)
        {
            g.setColour(juce::Colours::whitesmoke.withAlpha(isC ? 1.0f : 0.85f));
            g.setFont(juce::Font(13.0f, juce::Font::bold));
            g.drawText(midiToNoteName(note), juce::Rectangle<float>(4.0f, y, (float)keyWidth - 8.0f, noteHeight), juce::Justification::centredLeft, false);
        }

        g.setColour(juce::Colours::black.withAlpha(0.35f));
        g.drawLine(0.0f, y, (float)keyWidth, y);

        // Fondo principal del piano roll siguiendo la tonalidad
        juce::Colour rollColour = isBlackKey ? juce::Colour(0xff2e2e2e) : juce::Colour(0xff3c3c3c);
        if (isC)
            rollColour = rollColour.brighter(0.12f);

        g.setColour(rollColour);
        g.fillRect((float)keyWidth, y, (float)(getWidth() - keyWidth), noteHeight);
        // Línea divisoria horizontal para cada nota
        g.setColour(juce::Colours::black.withAlpha(0.2f));
        g.drawLine((float)keyWidth, y, (float)getWidth(), y);
    }

    g.setColour(juce::Colours::black.withAlpha(0.2f));
    g.drawLine(0.0f, (float)getHeight(), (float)getWidth(), (float)getHeight());

    // Borde exterior del teclado
    g.setColour(juce::Colours::black.withAlpha(0.6f));
    g.drawRect(keyArea);

    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;
    const int availableWidth = juce::jmax(0, getWidth() - keyWidth);
    const double visibleBeats = pixelsPerBeat > 0.0f ? (double)availableWidth / pixelsPerBeat : 0.0;
    const double startBeat = horizontalScrollBeats;
    const double endBeat = startBeat + visibleBeats + 1.0; // Añadir 1 beat extra para cubrir el borde derecho
    const float rollHeight = (float)getHeight();

    const int firstBar = (int)std::floor(startBeat / (double)kBeatsPerBar);
    const int lastBar = (int)std::ceil(endBeat / (double)kBeatsPerBar);

    for (int bar = firstBar; bar <= lastBar; ++bar)
    {
        const double barStart = (double)bar * (double)kBeatsPerBar;
        const double barEnd = barStart + kBeatsPerBar;
        const double drawStart = juce::jmax(barStart, startBeat);
        const double drawEnd = juce::jmin(barEnd, endBeat);

        if (drawEnd <= drawStart)
            continue;

        const float x1 = (float)keyWidth + (float)((drawStart - startBeat) * pixelsPerBeat);
        const float x2 = (float)keyWidth + (float)((drawEnd - startBeat) * pixelsPerBeat);

        const float drawX = juce::jmax(x1, (float)keyWidth);
        const float drawRight = juce::jmin(x2, (float)getWidth());
        const float drawWidth = drawRight - drawX;

        if (drawWidth <= 0.0f)
            continue;

        const bool evenBar = (bar % 2) == 0;
        g.setColour(evenBar ? juce::Colours::black.withAlpha(0.05f)
            : juce::Colours::black.withAlpha(0.025f));
        g.fillRect(drawX, 0.0f, drawWidth, rollHeight);
    }

    const bool hasNotes = !notes.isEmpty();

    if (hasNotes)
    {
        for (const auto& note : notes)
        {
            if (note.midiNote < lowestNote || note.midiNote > highestNote) continue;

            float x = (float)keyWidth + ((note.startTime - (float)horizontalScrollBeats) * pixelsPerBeat);
            // La 'y' y la 'altura' del rectángulo de la nota también usan la nueva altura escalada
            float y = (highestNote - note.midiNote) * noteHeight;
            float width = note.duration * pixelsPerBeat;

            if (x + width < (float)keyWidth || x >(float)getWidth())
                continue;

            g.setColour(note.isChordNote ? juce::Colours::cornflowerblue : juce::Colours::mediumspringgreen);
            g.fillRect(x, y, width, noteHeight);
            g.setColour(juce::Colours::black);
            g.drawRect(x, y, width, noteHeight, 1.0f);
        }
    }

    const int firstBeatLine = (int)std::floor(startBeat);
    const int lastBeatLine = (int)std::ceil(endBeat);

    for (int beat = firstBeatLine; beat <= lastBeatLine; ++beat)
    {
        const float x = (float)keyWidth + (float)((beat - startBeat) * pixelsPerBeat);
        if (x < (float)keyWidth - 1.0f || x >(float)getWidth() + 1.0f)
            continue;

        const bool isBarLine = (beat % kBeatsPerBar) == 0;
        const bool isHalfBarLine = (kBeatsPerBar % 2 == 0) && ((beat % kBeatsPerBar) == kBeatsPerBar / 2);

        juce::Colour lineColour;
        float thickness = 1.0f;

        if (isBarLine)
        {
            lineColour = juce::Colours::whitesmoke.withAlpha(0.5f);
            thickness = 2.0f;
        }
        else if (isHalfBarLine)
        {
            lineColour = juce::Colours::whitesmoke.withAlpha(0.25f);
        }
        else
        {
            lineColour = juce::Colours::whitesmoke.withAlpha(0.12f);
        }

        g.setColour(lineColour);
        g.drawLine(x, 0.0f, x, rollHeight, thickness);

        if (isBarLine && x >= (float)keyWidth && x <= (float)getWidth() - 8.0f)
        {
            const int barNumber = juce::jmax(0, beat / kBeatsPerBar) + 1;
            g.setColour(juce::Colours::whitesmoke.withAlpha(0.85f));
            g.setFont(juce::Font(12.0f, juce::Font::bold));
            juce::Rectangle<float> labelBounds(x + 4.0f, 2.0f, 40.0f, 14.0f);
            labelBounds.setRight(juce::jmin(labelBounds.getRight(), (float)getWidth() - 4.0f));
            g.drawText(juce::String(barNumber), labelBounds, juce::Justification::left, false);
        }
    }

    if (!hasNotes)
    {
        g.setColour(juce::Colours::lightgrey);
        g.drawText("Piano Roll - Esperando datos...", getLocalBounds(), juce::Justification::centred);
    }

    if (isPlaybackActive)
    {
        const float playbackX = (float)keyWidth + (float)((playbackPositionBeats - horizontalScrollBeats) * pixelsPerBeat);
        if (playbackX >= (float)keyWidth - 1.0f && playbackX <= (float)getWidth() + 1.0f)
        {
            g.setColour(juce::Colours::red);
            g.drawLine(playbackX, 0.0f, playbackX, (float)getHeight(), 2.0f);
        }
    }
}

void PianoRollComponent::resized()
{
    clampHorizontalScroll();
    clampVerticalScroll();
}

void PianoRollComponent::mouseWheelMove(const juce::MouseEvent& event, const juce::MouseWheelDetails& wheel)
{
    const int keyWidth = getKeyWidth();

    if (event.mods.isCtrlDown())
    {
        const float oldZoom = horizontalZoom;
        const float zoomFactor = juce::jlimit(0.1f, 10.0f, 1.0f + wheel.deltaY * 0.1f);
        horizontalZoom = juce::jlimit(kMinHorizontalZoom, kMaxHorizontalZoom, horizontalZoom * zoomFactor);

        if (std::abs(oldZoom - horizontalZoom) > 1.0e-5f)
        {
            const double mouseX = juce::jmax(0.0, event.position.x - (double)keyWidth);
            const double beatAtMouse = (mouseX / (kBasePixelsPerBeat * oldZoom)) + horizontalScrollBeats;

            clampHorizontalScroll();

            if (mouseX > 0.0)
            {
                const double newVisibleBeats = (double)juce::jmax(1, getWidth() - keyWidth) / (kBasePixelsPerBeat * horizontalZoom);
                const double newScroll = beatAtMouse - (mouseX / (kBasePixelsPerBeat * horizontalZoom));
                const double maxScroll = juce::jmax(0.0, contentLengthBeats - newVisibleBeats);
                horizontalScrollBeats = juce::jlimit(0.0, maxScroll, newScroll);
            }
        }

        repaint();
        return;
    }

    if (std::abs(wheel.deltaX) > 1.0e-5f)
        scrollHorizontally((double)wheel.deltaX * 4.0 / horizontalZoom);

    if (std::abs(wheel.deltaY) > 1.0e-5f)
    {
        verticalScrollRemainder += -wheel.deltaY * 4.0f;
        const int deltaNotes = (int)verticalScrollRemainder;
        if (deltaNotes != 0)
        {
            const int applied = scrollVertically(deltaNotes);
            if (applied != 0)
                verticalScrollRemainder -= (float)applied;
            else
                verticalScrollRemainder = 0.0f;
        }
    }
}

void PianoRollComponent::mouseDown(const juce::MouseEvent& event)
{
    if (event.mods.isAltDown() || event.mods.isMiddleButtonDown())
    {
        isPanning = true;
        lastPanPosition = event.getPosition();
        setMouseCursor(juce::MouseCursor::DraggingHandCursor);
        return;
    }

    if (event.mods.isRightButtonDown())
    {
        const int noteIndex = hitTestNote(event.position);
        if (noteIndex >= 0)
        {
            if (isDraggingNotes)
                endNoteDrag();
            if (isResizingNotes)
                endNoteResize();

            deleteNoteAt(noteIndex);
            return;
        }

        isPanning = true;
        lastPanPosition = event.getPosition();
        setMouseCursor(juce::MouseCursor::DraggingHandCursor);
        return;
    }

    if (event.mods.isLeftButtonDown())
    {
        if (isDraggingNotes)
            endNoteDrag();
        if (isResizingNotes)
            endNoteResize();

        const int noteIndex = hitTestNote(event.position);
        if (noteIndex >= 0)
        {
            beginNoteDrag(noteIndex, event);
            return;
        }

        endNoteDrag();
        endNoteResize();
    }
}

void PianoRollComponent::mouseDrag(const juce::MouseEvent& event)
{
    if (isPanning)
    {
        const auto delta = event.getPosition() - lastPanPosition;
        lastPanPosition = event.getPosition();

        if (delta.x != 0)
            scrollHorizontally((double)delta.x / (kBasePixelsPerBeat * horizontalZoom));

        if (delta.y != 0)
        {
            const int currentNotes = juce::jmax(1, visibleNoteCount);
            const float noteHeight = currentNotes > 0 ? (float)getHeight() / (float)currentNotes : 0.0f;
            if (noteHeight > 0.0f)
            {
                const int deltaNotes = juce::roundToInt((float)delta.y / noteHeight);
                if (deltaNotes != 0)
                {
                    const int applied = scrollVertically(deltaNotes);
                    if (applied != 0)
                        verticalScrollRemainder = 0.0f;
                }
            }
        }
        return;
    }

    if (isResizingNotes)
    {
        updateResizedNotes(event);
        return;
    }

    if (isDraggingNotes)
        updateDraggedNotes(event);
}

void PianoRollComponent::mouseUp(const juce::MouseEvent& event)
{
    juce::ignoreUnused(event);
    if (isPanning)
    {
        isPanning = false;
        setMouseCursor(juce::MouseCursor::NormalCursor);
    }

    if (isDraggingNotes)
        endNoteDrag();

    if (isResizingNotes)
        endNoteResize();
}


void PianoRollComponent::setMusicData(const py::dict& data)
{
    DBG("PianoRollComponent::setMusicData fue llamado.");
    stopPlayback();
    notes.clear();
    musicData.clear();
    isDraggingNotes = false;
    primaryDragNoteIndex = -1;
    draggedNoteIndices.clearQuick();
    draggedMidiOffsets.clear();
    draggedStartOffsets.clear();
    isResizingNotes = false;
    resizingNoteIndices.clearQuick();
    resizeAnchorBeats = 0.0;
    hasPendingContentChange = false;
    float sequentialChordTime = 0.0f;

    try
    {
        // --- PROCESAR ACORDES ---
        if (data.contains("acordes") && data.contains("ritmo"))
        {
            py::list pyChords = data["acordes"];
            py::list pyRhythm = data["ritmo"];
            DBG("Procesando " + juce::String(pyChords.size()) + " acordes...");

            std::vector<std::vector<double>> importedOffsets;
            std::vector<std::vector<double>> importedDurations;
            if (data.contains("acordes_detallados"))
            {
                py::list pyDetailed = data["acordes_detallados"];
                importedOffsets.resize(pyDetailed.size());
                importedDurations.resize(pyDetailed.size());

                for (size_t i = 0; i < pyDetailed.size(); ++i)
                {
                    if (!py::isinstance<py::list>(pyDetailed[i]))
                        continue;

                    py::list detailList = pyDetailed[i].cast<py::list>();
                    auto& offsets = importedOffsets[i];
                    auto& durations = importedDurations[i];
                    offsets.reserve(detailList.size());
                    durations.reserve(detailList.size());

                    for (auto detailItem : detailList)
                    {
                        try
                        {
                            py::tuple tupleData = detailItem.cast<py::tuple>();
                            double offset = tupleData.size() > 1 ? tupleData[1].cast<double>() : 0.0;
                            double perNoteDur = tupleData.size() > 2 ? tupleData[2].cast<double>() : 0.0;
                            offsets.push_back(offset);
                            durations.push_back(perNoteDur);
                        }
                        catch (...)
                        {
                            offsets.push_back(0.0);
                            durations.push_back(0.0);
                        }
                    }
                }
            }

            std::vector<double> importedStarts;
            if (data.contains("acordes_tiempos"))
            {
                py::list pyStarts = data["acordes_tiempos"];
                importedStarts.reserve(pyStarts.size());
                for (auto item : pyStarts)
                {
                    try
                    {
                        importedStarts.push_back(item.cast<double>());
                    }
                    catch (...)
                    {
                        importedStarts.push_back(0.0);
                    }
                }
            }

            for (size_t i = 0; i < pyChords.size(); ++i)
            {
                auto item = pyChords[i];
                float duration = 0.0f;
                try
                {
                    duration = pyRhythm[i].cast<float>();
                }
                catch (...)
                {
                    duration = 0.0f;
                }

                const float chordBaseTime = (i < importedStarts.size())
                    ? static_cast<float>(importedStarts[i])
                    : sequentialChordTime;

                std::vector<int> chordMidiValues;
                juce::Array<int> chordNoteIndices;
                std::vector<double> actualStarts;
                std::vector<double> actualDurations;
                double earliestStart = std::numeric_limits<double>::infinity();
                double latestEnd = -std::numeric_limits<double>::infinity();

                if (py::isinstance<py::list>(item))
                {
                    py::list noteList = item.cast<py::list>();
                    for (auto note : noteList)
                    {
                        std::string noteName = note.cast<std::string>();
                        int midiNote = noteNameToMidi(noteName);
                        if (midiNote != -1)
                        {
                            const size_t slot = chordMidiValues.size();
                            double offset = 0.0;
                            double perNoteDur = 0.0;
                            if (i < importedOffsets.size() && slot < importedOffsets[i].size())
                                offset = importedOffsets[i][slot];
                            if (i < importedDurations.size() && slot < importedDurations[i].size())
                                perNoteDur = importedDurations[i][slot];

                            if (perNoteDur <= 0.0)
                                perNoteDur = (double)duration;

                            const double actualStart = static_cast<double>(chordBaseTime) + offset;
                            const int noteIndex = notes.size();
                            notes.add({ midiNote, (float)actualStart, (float)perNoteDur, true, -1, 0 });
                            chordNoteIndices.add(noteIndex);
                            chordMidiValues.push_back(midiNote);

                            actualStarts.push_back(actualStart);
                            actualDurations.push_back(perNoteDur);
                            earliestStart = std::min(earliestStart, actualStart);
                            latestEnd = std::max(latestEnd, actualStart + perNoteDur);
                        }
                    }
                }

                if (!chordMidiValues.empty())
                {
                    const double defaultStart = static_cast<double>(chordBaseTime);
                    const double safeEarliest = std::isfinite(earliestStart) ? earliestStart : defaultStart;
                    double safeLatest = std::isfinite(latestEnd) ? latestEnd : (safeEarliest + duration);
                    if (safeLatest < safeEarliest)
                        safeLatest = safeEarliest;

                    NoteInfo chordInfo;
                    chordInfo.isMelody = false;
                    chordInfo.startTime = safeEarliest;
                    chordInfo.duration = std::max<double>(0.0, std::max((double)duration, safeLatest - safeEarliest));
                    chordInfo.midiValue = chordMidiValues.front();
                    const size_t chordSize = chordMidiValues.size();
                    chordInfo.chordMidiValues = std::move(chordMidiValues);
                    chordInfo.chordNoteOffsets.assign(chordSize, 0.0);
                    chordInfo.chordNoteDurations.assign(chordSize, chordInfo.duration);
                    musicData.push_back(std::move(chordInfo));

                    const int infoIndex = static_cast<int>(musicData.size()) - 1;
                    for (int slot = 0; slot < chordNoteIndices.size(); ++slot)
                    {
                        auto& storedNote = notes.getReference(chordNoteIndices[slot]);
                        storedNote.infoIndex = infoIndex;
                        storedNote.chordNoteSlot = slot;

                        if (slot < (int)actualStarts.size())
                        {
                            const double relativeOffset = actualStarts[(size_t)slot] - musicData[(size_t)infoIndex].startTime;
                            musicData[(size_t)infoIndex].chordNoteOffsets[(size_t)slot] = relativeOffset;
                        }

                        if (slot < (int)actualDurations.size())
                            musicData[(size_t)infoIndex].chordNoteDurations[(size_t)slot] = actualDurations[(size_t)slot];
                    }
                }

                sequentialChordTime += duration;
            }
        }

        // --- PROCESAR MELODÍA (CON NUEVA DEPURACIÓN) ---
        if (data.contains("melodia"))
        {
            py::list pyMelody = data["melodia"];
            float melodyTime = 0.0f;
            DBG("Procesando " + juce::String(pyMelody.size()) + " eventos de melodia...");

            for (auto item : pyMelody)
            {
                py::tuple noteTuple = item.cast<py::tuple>();
                std::string noteName = noteTuple[0].cast<std::string>();
                std::string durStr = noteTuple[1].cast<std::string>();
                float duration = std::stof(durStr);

                // Mensaje de depuración para cada nota de la melodía
                DBG("  -> Melodia: " + juce::String(noteName) + " | MIDI: " + juce::String(noteNameToMidi(noteName)) + " | Tiempo: " + juce::String(melodyTime) + " | Dur: " + juce::String(duration));

                if (noteName != "0")
                {
                    int midiNote = noteNameToMidi(noteName);
                    if (midiNote != -1)
                    {
                        const int noteIndex = notes.size();
                        notes.add({ midiNote, melodyTime, duration, false, -1, 0 });
                        NoteInfo melodyInfo;
                        melodyInfo.isMelody = true;
                        melodyInfo.startTime = static_cast<double>(melodyTime);
                        melodyInfo.duration = static_cast<double>(duration);
                        melodyInfo.midiValue = midiNote;
                        melodyInfo.chordMidiValues.clear();
                        melodyInfo.chordNoteOffsets.clear();
                        melodyInfo.chordNoteDurations.clear();
                        musicData.push_back(std::move(melodyInfo));

                        const int infoIndex = static_cast<int>(musicData.size()) - 1;
                        auto& storedNote = notes.getReference(noteIndex);
                        storedNote.infoIndex = infoIndex;
                        storedNote.chordNoteSlot = 0;
                    }
                }
                melodyTime += duration;
            }
        }
    }
    catch (const py::cast_error& e)
    {
        DBG("!!! pybind11::cast_error en setMusicData: " << e.what());
    }

    std::sort(musicData.begin(), musicData.end(), [](const NoteInfo& a, const NoteInfo& b)
        {
            if (a.startTime == b.startTime)
                return a.isMelody && !b.isMelody; // Opcional: priorizar melodía cuando empatan
            return a.startTime < b.startTime;
        });

    DBG("Procesamiento finalizado. Total de notas en el array: " + juce::String(notes.size()) +
        ", eventos para reproducir: " + juce::String((int)musicData.size()));
    if (notes.isEmpty())
    {
        visibleNoteCount = juce::jmin(24, (defaultHighestNote - defaultLowestNote) + 1);
        displayLowestNote = defaultLowestNote;
    }
    else
    {
        int minNote = defaultHighestNote;
        int maxNote = defaultLowestNote;

        for (const auto& note : notes)
        {
            minNote = std::min(minNote, note.midiNote);
            maxNote = std::max(maxNote, note.midiNote);
        }

        minNote = juce::jmax(defaultLowestNote, minNote - 4);
        maxNote = juce::jmin(defaultHighestNote, maxNote + 4);

        if (maxNote < minNote)
            std::swap(maxNote, minNote);

        visibleNoteCount = juce::jmax(1, juce::jmin((defaultHighestNote - defaultLowestNote) + 1, (maxNote - minNote) + 1));
        displayLowestNote = juce::jlimit(defaultLowestNote, defaultHighestNote - visibleNoteCount + 1, minNote);
    }

    displayHighestNote = displayLowestNote + visibleNoteCount - 1;

    recalculateContentLength();

    horizontalScrollBeats = 0.0;
    verticalScrollRemainder = 0.0f;
    clampVerticalScroll();
    clampHorizontalScroll();
    repaint();
}

void PianoRollComponent::startPlayback(double bpm)
{
    const double safeBpm = juce::jmax(0.001, bpm);
    secondsPerBeat = 60.0 / safeBpm;
    playbackPositionBeats = 0.0;
    lastPlaybackUpdateSeconds = juce::Time::getMillisecondCounterHiRes() * 0.001;

    if (contentLengthBeats <= 0.0)
    {
        isPlaybackActive = false;
        stopTimer();
        repaint();
        return;
    }

    isPlaybackActive = true;
    startTimerHz(60);
    repaint();
}

void PianoRollComponent::stopPlayback()
{
    const bool wasActive = isPlaybackActive || playbackPositionBeats > 0.0;
    isPlaybackActive = false;
    playbackPositionBeats = 0.0;
    stopTimer();

    if (wasActive)
        repaint();
}

void PianoRollComponent::clampHorizontalScroll()
{
    const int keyWidth = getKeyWidth();
    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;
    const int availableWidth = juce::jmax(0, getWidth() - keyWidth);
    const double visibleBeats = pixelsPerBeat > 0.0f ? (double)availableWidth / pixelsPerBeat : 0.0;
    const double maxScroll = juce::jmax(0.0, contentLengthBeats - visibleBeats);
    horizontalScrollBeats = juce::jlimit(0.0, maxScroll, horizontalScrollBeats);
}

void PianoRollComponent::clampVerticalScroll()
{
    const int totalRange = (defaultHighestNote - defaultLowestNote) + 1;
    visibleNoteCount = juce::jlimit(1, totalRange, visibleNoteCount);

    const int maxLowest = defaultHighestNote - visibleNoteCount + 1;
    displayLowestNote = juce::jlimit(defaultLowestNote, maxLowest, displayLowestNote);
    displayHighestNote = displayLowestNote + visibleNoteCount - 1;
}

void PianoRollComponent::scrollHorizontally(double deltaBeats)
{
    if (std::abs(deltaBeats) < 1.0e-5)
        return;

    const double previous = horizontalScrollBeats;
    horizontalScrollBeats += deltaBeats;
    clampHorizontalScroll();
    if (horizontalScrollBeats != previous)
        repaint();
}

int PianoRollComponent::scrollVertically(int deltaNotes)
{
    if (deltaNotes == 0)
        return 0;

    const int originalLowest = displayLowestNote;
    displayLowestNote += deltaNotes;
    clampVerticalScroll();
    const int appliedDelta = displayLowestNote - originalLowest;
    if (appliedDelta != 0)
        repaint();
    return appliedDelta;
}

int PianoRollComponent::hitTestNote(juce::Point<float> position) const
{
    const int keyWidth = getKeyWidth();
    if (position.x <= (float)keyWidth)
        return -1;

    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;
    if (pixelsPerBeat <= 0.0f)
        return -1;

    const int highestNote = displayHighestNote;
    const int lowestNote = displayLowestNote;
    const int numNotes = juce::jmax(1, visibleNoteCount);
    const float noteHeight = numNotes > 0 ? (float)getHeight() / (float)numNotes : 0.0f;
    if (noteHeight <= 0.0f)
        return -1;

    for (int i = notes.size(); --i >= 0;)
    {
        const auto& note = notes[(int)i];
        if (note.midiNote < lowestNote || note.midiNote > highestNote)
            continue;

        const float x = (float)keyWidth + ((note.startTime - (float)horizontalScrollBeats) * pixelsPerBeat);
        const float width = note.duration * pixelsPerBeat;
        const float y = (highestNote - note.midiNote) * noteHeight;

        if (position.x >= x && position.x <= x + width &&
            position.y >= y && position.y <= y + noteHeight)
        {
            return (int)i;
        }
    }

    return -1;
}

void PianoRollComponent::beginNoteDrag(int noteIndex, const juce::MouseEvent& event)
{
    if (!juce::isPositiveAndBelow(noteIndex, notes.size()))
        return;

    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;
    const int numNotes = juce::jmax(1, visibleNoteCount);
    const float noteHeight = numNotes > 0 ? (float)getHeight() / (float)numNotes : 0.0f;
    if (pixelsPerBeat <= 0.0f || noteHeight <= 0.0f)
        return;

    auto& baseNote = notes.getReference(noteIndex);
    const int keyWidth = getKeyWidth();
    const float noteX = (float)keyWidth + ((baseNote.startTime - (float)horizontalScrollBeats) * pixelsPerBeat);
    const float noteWidth = baseNote.duration * pixelsPerBeat;
    const bool shouldGroupChord = baseNote.isChordNote && event.mods.isCommandDown();

    const bool nearRightEdge = noteWidth > 0.0f &&
        event.position.x >= noteX + juce::jmax(0.0f, noteWidth - kResizeHandleWidthPixels);

    if (nearRightEdge)
    {
        resizingNoteIndices.clearQuick();
        primaryDragNoteIndex = noteIndex;
        resizeAnchorBeats = baseNote.startTime;

        resizingNoteIndices.addIfNotAlreadyThere(noteIndex);

        const int infoIndex = baseNote.infoIndex;
        if (shouldGroupChord && infoIndex >= 0)
        {
            for (int i = 0; i < notes.size(); ++i)
            {
                if (i == noteIndex)
                    continue;

                const auto& candidate = notes.getReference(i);
                if (candidate.infoIndex == infoIndex)
                    resizingNoteIndices.addIfNotAlreadyThere(i);
            }
        }

        isResizingNotes = true;
        setMouseCursor(juce::MouseCursor::LeftRightResizeCursor);
        return;
    }

    draggedNoteIndices.clearQuick();
    draggedMidiOffsets.clear();
    draggedStartOffsets.clear();

    primaryDragNoteIndex = noteIndex;

    draggedNoteIndices.add(noteIndex);
    draggedMidiOffsets.push_back(0);
    draggedStartOffsets.push_back(0.0);

    const int infoIndex = baseNote.infoIndex;
    if (shouldGroupChord && infoIndex >= 0)
    {
        for (int i = 0; i < notes.size(); ++i)
        {
            if (i == noteIndex)
                continue;

            const auto& candidate = notes.getReference(i);
            if (candidate.infoIndex == infoIndex)
            {
                draggedNoteIndices.add(i);
                draggedMidiOffsets.push_back(candidate.midiNote - baseNote.midiNote);
                draggedStartOffsets.push_back(static_cast<double>(candidate.startTime) - static_cast<double>(baseNote.startTime));
            }
        }
    }

    const double clickBeats = horizontalScrollBeats + ((event.position.x - (float)keyWidth) / pixelsPerBeat);
    dragOffsetBeats = clickBeats - (double)baseNote.startTime;

    const float noteTop = (displayHighestNote - baseNote.midiNote) * noteHeight;
    dragOffsetNoteY = event.position.y - noteTop;

    isDraggingNotes = true;
    setMouseCursor(juce::MouseCursor::DraggingHandCursor);
}

void PianoRollComponent::updateDraggedNotes(const juce::MouseEvent& event)
{
    if (!isDraggingNotes || !juce::isPositiveAndBelow(primaryDragNoteIndex, notes.size()))
        return;

    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;
    const int numNotes = juce::jmax(1, visibleNoteCount);
    const float noteHeight = numNotes > 0 ? (float)getHeight() / (float)numNotes : 0.0f;
    if (pixelsPerBeat <= 0.0f || noteHeight <= 0.0f)
        return;

    const int keyWidth = getKeyWidth();
    double pointerBeats = horizontalScrollBeats + ((event.position.x - (float)keyWidth) / pixelsPerBeat);
    double newStart = pointerBeats - dragOffsetBeats;

    if (!event.mods.isShiftDown())
    {
        const double step = kDefaultQuantiseStepBeats;
        if (step > 0.0)
            newStart = std::round(newStart / step) * step;
    }

    newStart = std::max(0.0, newStart);

    const float newTop = event.position.y - dragOffsetNoteY;
    const float noteIndexFloat = newTop / noteHeight;
    int newBaseMidi = displayHighestNote - juce::roundToInt(noteIndexFloat);
    newBaseMidi = juce::jlimit(defaultLowestNote, defaultHighestNote, newBaseMidi);

    bool anyChanged = false;
    for (int i = 0; i < draggedNoteIndices.size(); ++i)
    {
        const int index = draggedNoteIndices[i];
        if (!juce::isPositiveAndBelow(index, notes.size()))
            continue;

        auto& note = notes.getReference(index);
        double adjustedStart = newStart;
        if (i < (int)draggedStartOffsets.size())
            adjustedStart += draggedStartOffsets[(size_t)i];

        const float clampedStart = (float)juce::jmax(0.0, adjustedStart);
        if (std::abs(note.startTime - clampedStart) > 1.0e-4f)
        {
            note.startTime = clampedStart;
            anyChanged = true;
        }
        const int relative = draggedMidiOffsets[(size_t)i];
        const int newMidi = juce::jlimit(defaultLowestNote, defaultHighestNote, newBaseMidi + relative);
        if (note.midiNote != newMidi)
        {
            note.midiNote = newMidi;
            anyChanged = true;
        }
    }

    const int infoIndex = notes.getReference(primaryDragNoteIndex).infoIndex;
    if (infoIndex >= 0)
        refreshNoteInfo(infoIndex);

    recalculateContentLength();
    clampHorizontalScroll();
    repaint();

    if (anyChanged)
        markContentDirty();
}

void PianoRollComponent::updateResizedNotes(const juce::MouseEvent& event)
{
    if (!isResizingNotes || !juce::isPositiveAndBelow(primaryDragNoteIndex, notes.size()))
        return;

    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;
    if (pixelsPerBeat <= 0.0f)
        return;

    const int keyWidth = getKeyWidth();
    double pointerBeats = horizontalScrollBeats + ((event.position.x - (float)keyWidth) / pixelsPerBeat);
    double newDuration = pointerBeats - resizeAnchorBeats;

    const bool allowFreeMove = event.mods.isShiftDown();
    if (!allowFreeMove)
    {
        const double step = kDefaultQuantiseStepBeats;
        if (step > 0.0)
            newDuration = std::round(newDuration / step) * step;
    }

    const double minDuration = allowFreeMove ? kMinimumNoteDurationBeats
        : juce::jmax(kDefaultQuantiseStepBeats, kMinimumNoteDurationBeats);

    if (!std::isfinite(newDuration))
        return;

    newDuration = juce::jmax(minDuration, newDuration);

    bool anyChanged = false;
    for (int i = 0; i < resizingNoteIndices.size(); ++i)
    {
        const int index = resizingNoteIndices[i];
        if (!juce::isPositiveAndBelow(index, notes.size()))
            continue;

        auto& note = notes.getReference(index);
        const float newDurFloat = (float)newDuration;
        if (std::abs(note.duration - newDurFloat) > 1.0e-4f)
        {
            note.duration = newDurFloat;
            anyChanged = true;
        }
    }

    const int infoIndex = notes.getReference(primaryDragNoteIndex).infoIndex;
    if (infoIndex >= 0)
        refreshNoteInfo(infoIndex);

    recalculateContentLength();
    clampHorizontalScroll();
    repaint();

    if (anyChanged)
        markContentDirty();
}

void PianoRollComponent::endNoteDrag()
{
    if (!isDraggingNotes)
        return;

    isDraggingNotes = false;
    primaryDragNoteIndex = -1;
    draggedNoteIndices.clearQuick();
    draggedMidiOffsets.clear();
    draggedStartOffsets.clear();
    setMouseCursor(juce::MouseCursor::NormalCursor);

    recalculateContentLength();
    clampHorizontalScroll();
    repaint();

    commitContentChange();
}

void PianoRollComponent::endNoteResize()
{
    if (!isResizingNotes)
        return;

    isResizingNotes = false;
    primaryDragNoteIndex = -1;
    resizingNoteIndices.clearQuick();
    setMouseCursor(juce::MouseCursor::NormalCursor);

    recalculateContentLength();
    clampHorizontalScroll();
    repaint();

    commitContentChange();
}

void PianoRollComponent::deleteNoteAt(int noteIndex)
{
    if (!juce::isPositiveAndBelow(noteIndex, notes.size()))
        return;

    isDraggingNotes = false;
    isResizingNotes = false;
    primaryDragNoteIndex = -1;
    draggedNoteIndices.clearQuick();
    draggedMidiOffsets.clear();
    draggedStartOffsets.clear();
    resizingNoteIndices.clearQuick();

    const int infoIndex = notes.getReference(noteIndex).infoIndex;
    bool modified = false;

    if (!juce::isPositiveAndBelow(infoIndex, (int)musicData.size()))
    {
        notes.remove(noteIndex);
        modified = true;
    }
    else
    {
        int chordNoteCount = 0;
        for (const auto& note : notes)
        {
            if (note.infoIndex == infoIndex)
                ++chordNoteCount;
        }

        if (chordNoteCount <= 1)
        {
            for (int i = notes.size(); --i >= 0;)
            {
                if (notes.getReference(i).infoIndex == infoIndex)
                    notes.remove(i);
            }

            musicData.erase(musicData.begin() + infoIndex);

            for (auto& remaining : notes)
            {
                if (remaining.infoIndex > infoIndex)
                    --remaining.infoIndex;
            }
            modified = true;
        }
        else
        {
            notes.remove(noteIndex);
            modified = true;

            std::vector<int> remainingIndices;
            remainingIndices.reserve(notes.size());
            for (int i = 0; i < notes.size(); ++i)
            {
                if (notes.getReference(i).infoIndex == infoIndex)
                    remainingIndices.push_back(i);
            }

            std::sort(remainingIndices.begin(), remainingIndices.end(), [&](int a, int b)
                {
                    return notes[a].chordNoteSlot < notes[b].chordNoteSlot;
                });

            for (size_t slot = 0; slot < remainingIndices.size(); ++slot)
                notes.getReference(remainingIndices[slot]).chordNoteSlot = (int)slot;

            refreshNoteInfo(infoIndex);
        }
    }

    recalculateContentLength();
    clampHorizontalScroll();
    repaint();

    if (modified)
    {
        markContentDirty();
        commitContentChange();
    }
}

void PianoRollComponent::refreshNoteInfo(int infoIndex)
{
    if (!juce::isPositiveAndBelow(infoIndex, (int)musicData.size()))
        return;

    auto& info = musicData[(size_t)infoIndex];

    if (info.isMelody)
    {
        for (const auto& note : notes)
        {
            if (note.infoIndex == infoIndex)
            {
                info.startTime = note.startTime;
                info.duration = note.duration;
                info.midiValue = note.midiNote;
                info.chordMidiValues.clear();
                info.chordNoteOffsets.clear();
                info.chordNoteDurations.clear();
                break;
            }
        }
        return;
    }

    struct SlotData
    {
        int slot;
        double start;
        double duration;
        int midi;
    };

    std::vector<SlotData> chordEntries;
    chordEntries.reserve(notes.size());

    double minStart = std::numeric_limits<double>::infinity();
    double maxEnd = -std::numeric_limits<double>::infinity();
    int maxSlot = -1;

    for (const auto& note : notes)
    {
        if (note.infoIndex != infoIndex)
            continue;

        SlotData data
        {
            juce::jmax(0, note.chordNoteSlot),
            static_cast<double>(note.startTime),
            static_cast<double>(note.duration),
            note.midiNote
        };

        chordEntries.push_back(data);
        maxSlot = std::max(maxSlot, data.slot);
        minStart = std::min(minStart, data.start);
        maxEnd = std::max(maxEnd, data.start + data.duration);
    }

    if (chordEntries.empty())
    {
        info.chordMidiValues.clear();
        info.chordNoteOffsets.clear();
        info.chordNoteDurations.clear();
        info.duration = 0.0;
        info.midiValue = 0;
        return;
    }

    if (!std::isfinite(minStart) || !std::isfinite(maxEnd))
        return;

    if (maxEnd < minStart)
        maxEnd = minStart;

    info.startTime = minStart;
    info.duration = juce::jmax(0.0, maxEnd - minStart);

    const size_t vectorSize = (size_t)juce::jmax(0, maxSlot) + 1;
    info.chordMidiValues.assign(vectorSize, 0);
    info.chordNoteOffsets.assign(vectorSize, 0.0);
    info.chordNoteDurations.assign(vectorSize, info.duration);

    for (const auto& entry : chordEntries)
    {
        const size_t slot = (size_t)juce::jlimit(0, (int)vectorSize - 1, entry.slot);
        info.chordMidiValues[slot] = entry.midi;
        info.chordNoteOffsets[slot] = entry.start - info.startTime;
        info.chordNoteDurations[slot] = entry.duration;
    }

    info.midiValue = info.chordMidiValues.empty() ? 0 : info.chordMidiValues.front();
}

void PianoRollComponent::writeCurrentStateToPyDict(py::dict& target) const
{
    py::gil_scoped_acquire acquire;

    py::list chordList;
    py::list rhythmList;
    py::list chordDetails;
    py::list chordStarts;

    std::vector<const NoteInfo*> chordInfos;
    chordInfos.reserve(musicData.size());
    for (const auto& info : musicData)
    {
        if (!info.isMelody)
            chordInfos.push_back(&info);
    }

    std::sort(chordInfos.begin(), chordInfos.end(), [](const NoteInfo* a, const NoteInfo* b)
        {
            if (a->startTime == b->startTime)
                return a < b;
            return a->startTime < b->startTime;
        });

    for (const auto* info : chordInfos)
    {
        if (info == nullptr)
            continue;

        py::list noteNames;
        py::list detailEntries;

        const size_t count = info->chordMidiValues.size();
        for (size_t slot = 0; slot < count; ++slot)
        {
            const int midi = info->chordMidiValues[slot];
            if (midi <= 0)
                continue;

            const auto noteName = midiToNoteName(midi);
            if (noteName.isEmpty())
                continue;

            const double offset = slot < info->chordNoteOffsets.size() ? info->chordNoteOffsets[slot] : 0.0;
            const double perDuration = slot < info->chordNoteDurations.size() ? info->chordNoteDurations[slot] : info->duration;

            noteNames.append(noteName.toStdString());
            detailEntries.append(py::make_tuple(noteName.toStdString(), offset, perDuration));
        }

        if (noteNames.size() == 0)
            continue;

        chordList.append(noteNames);
        rhythmList.append(info->duration);
        chordDetails.append(detailEntries);
        chordStarts.append(info->startTime);
    }

    target["acordes"] = chordList;
    target["ritmo"] = rhythmList;
    target["acordes_detallados"] = chordDetails;
    target["acordes_tiempos"] = chordStarts;

    py::list melodyList;
    std::vector<const NoteInfo*> melodyInfos;
    melodyInfos.reserve(musicData.size());
    for (const auto& info : musicData)
    {
        if (info.isMelody)
            melodyInfos.push_back(&info);
    }

    std::sort(melodyInfos.begin(), melodyInfos.end(), [](const NoteInfo* a, const NoteInfo* b)
        {
            if (a->startTime == b->startTime)
                return a < b;
            return a->startTime < b->startTime;
        });

    double cursor = 0.0;
    for (const auto* info : melodyInfos)
    {
        if (info == nullptr)
            continue;

        if (info->duration <= 0.0)
            continue;

        if (info->startTime > cursor + kRestMergeTolerance)
        {
            const double restDur = info->startTime - cursor;
            melodyList.append(py::make_tuple(std::string("0"), formatBeats(restDur).toStdString()));
            cursor = info->startTime;
        }

        juce::String noteName = midiToNoteName(info->midiValue);
        if (noteName.isEmpty())
            noteName = "0";

        melodyList.append(py::make_tuple(noteName.toStdString(), formatBeats(info->duration).toStdString()));
        cursor = std::max(cursor, info->startTime + info->duration);
    }

    target["melodia"] = melodyList;
    target["error"] = "";
}

void PianoRollComponent::recalculateContentLength()
{
    contentLengthBeats = 0.0;
    for (const auto& note : notes)
        contentLengthBeats = std::max(contentLengthBeats, static_cast<double>(note.startTime + note.duration));
}

void PianoRollComponent::timerCallback()
{
    if (!isPlaybackActive)
    {
        stopTimer();
        return;
    }

    const double nowSeconds = juce::Time::getMillisecondCounterHiRes() * 0.001;
    const double deltaSeconds = nowSeconds - lastPlaybackUpdateSeconds;
    lastPlaybackUpdateSeconds = nowSeconds;

    if (secondsPerBeat > 0.0)
        playbackPositionBeats += deltaSeconds / secondsPerBeat;

    if (playbackPositionBeats >= contentLengthBeats)
    {
        playbackPositionBeats = contentLengthBeats;
        isPlaybackActive = false;
        stopTimer();
    }

    repaint();
}

void PianoRollComponent::markContentDirty()
{
    hasPendingContentChange = true;
}

void PianoRollComponent::commitContentChange()
{
    if (!hasPendingContentChange)
        return;

    hasPendingContentChange = false;

    if (contentChangedCallback)
        contentChangedCallback();
}
