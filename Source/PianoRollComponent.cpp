#include "PianoRollComponent.h"
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <utility>
#include <cmath>

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
    if (midiNote < 0 || midiNote > 127)
        return {};

    static const juce::StringArray noteNames({ "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" });
    const int octave = (midiNote / 12) - 1;
    const int index = midiNote % 12;

    return noteNames[index] + juce::String(octave);
}

namespace
{
    constexpr float kBasePixelsPerBeat = 100.0f;
    constexpr float kMinHorizontalZoom = 0.25f;
    constexpr float kMaxHorizontalZoom = 6.0f;
}

PianoRollComponent::PianoRollComponent() {}
PianoRollComponent::~PianoRollComponent() {}

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

    if (notes.isEmpty())
    {
        g.setColour(juce::Colours::lightgrey);
        g.drawText("Piano Roll - Esperando datos...", getLocalBounds(), juce::Justification::centred);
        return;
    }

    const float pixelsPerBeat = kBasePixelsPerBeat * horizontalZoom;

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
    if (event.mods.isMiddleButtonDown() || event.mods.isRightButtonDown() || event.mods.isAltDown())
    {
        isPanning = true;
        lastPanPosition = event.getPosition();
        setMouseCursor(juce::MouseCursor::DraggingHandCursor);
    }
}

void PianoRollComponent::mouseDrag(const juce::MouseEvent& event)
{
    if (!isPanning)
        return;

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
}

void PianoRollComponent::mouseUp(const juce::MouseEvent& event)
{
    juce::ignoreUnused(event);
    if (isPanning)
    {
        isPanning = false;
        setMouseCursor(juce::MouseCursor::NormalCursor);
    }
}


void PianoRollComponent::setMusicData(const py::dict& data)
{
    DBG("PianoRollComponent::setMusicData fue llamado.");
    stopPlayback();
    notes.clear();
    musicData.clear();
    float time = 0.0f;

    try
    {
        // --- PROCESAR ACORDES ---
        if (data.contains("acordes") && data.contains("ritmo"))
        {
            py::list pyChords = data["acordes"];
            py::list pyRhythm = data["ritmo"];
            DBG("Procesando " + juce::String(pyChords.size()) + " acordes...");

            for (size_t i = 0; i < pyChords.size(); ++i)
            {
                auto item = pyChords[i];
                float duration = pyRhythm[i].cast<float>();
                std::vector<int> chordMidiValues;

                if (py::isinstance<py::list>(item))
                {
                    py::list noteList = item.cast<py::list>();
                    for (auto note : noteList)
                    {
                        std::string noteName = note.cast<std::string>();
                        int midiNote = noteNameToMidi(noteName);
                        if (midiNote != -1)
                        {
                            notes.add({ midiNote, time, duration, true });
                            chordMidiValues.push_back(midiNote);
                        }
                    }
                }

                if (!chordMidiValues.empty())
                {
                    NoteInfo chordInfo;
                    chordInfo.isMelody = false;
                    chordInfo.startTime = static_cast<double>(time);
                    chordInfo.duration = static_cast<double>(duration);
                    chordInfo.midiValue = chordMidiValues.front();
                    chordInfo.chordMidiValues = std::move(chordMidiValues);
                    musicData.push_back(std::move(chordInfo));
                }

                time += duration;
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
                        notes.add({ midiNote, melodyTime, duration, false });
                        NoteInfo melodyInfo;
                        melodyInfo.isMelody = true;
                        melodyInfo.startTime = static_cast<double>(melodyTime);
                        melodyInfo.duration = static_cast<double>(duration);
                        melodyInfo.midiValue = midiNote;
                        musicData.push_back(std::move(melodyInfo));
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

    contentLengthBeats = 0.0;
    for (const auto& note : notes)
        contentLengthBeats = std::max(contentLengthBeats, static_cast<double>(note.startTime + note.duration));

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