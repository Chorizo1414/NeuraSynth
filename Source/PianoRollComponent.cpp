#include "PianoRollComponent.h"
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <utility>

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


PianoRollComponent::PianoRollComponent() {}
PianoRollComponent::~PianoRollComponent() {}

void PianoRollComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff3c3c3c));

    const int keyWidth = 25;
    const int lowestNote = 21;  // A0
    const int highestNote = 108; // C8
    const int numNotes = highestNote - lowestNote;

    // --- LÓGICA DE DIBUJO CORREGIDA ---
    // Calculamos la altura de cada "fila" de nota basándonos en la altura actual del componente
    const float noteHeight = (float)getHeight() / (float)numNotes;

    // Dibuja el fondo del piano roll
    for (int note = lowestNote; note <= highestNote; ++note)
    {
        if (note % 12 == 1 || note % 12 == 3 || note % 12 == 6 || note % 12 == 8 || note % 12 == 10)
            g.setColour(juce::Colours::black.withAlpha(0.3f));
        else
            g.setColour(juce::Colours::transparentBlack);

        // La 'y' ahora es relativa a la altura total
        float y = (highestNote - note) * noteHeight;
        g.fillRect((float)keyWidth, y, (float)(getWidth() - keyWidth), noteHeight);
    }

    if (notes.isEmpty())
    {
        g.setColour(juce::Colours::lightgrey);
        g.drawText("Piano Roll - Esperando datos...", getLocalBounds(), juce::Justification::centred);
        return;
    }

    const float pixelsPerBeat = 60.0f;

    for (const auto& note : notes)
    {
        if (note.midiNote < lowestNote || note.midiNote > highestNote) continue;

        float x = (float)keyWidth + (note.startTime * pixelsPerBeat);
        // La 'y' y la 'altura' del rectángulo de la nota también usan la nueva altura escalada
        float y = (highestNote - note.midiNote) * noteHeight;
        float width = note.duration * pixelsPerBeat;

        g.setColour(note.isChordNote ? juce::Colours::cornflowerblue : juce::Colours::mediumspringgreen);
        g.fillRect(x, y, width, noteHeight);
        g.setColour(juce::Colours::black);
        g.drawRect(x, y, width, noteHeight, 1.0f);
    }
}

void PianoRollComponent::resized() {}


void PianoRollComponent::setMusicData(const py::dict& data)
{
    DBG("PianoRollComponent::setMusicData fue llamado.");
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
                        // Descomenta la siguiente línea si necesitas depurar cada nota de acorde
                        // DBG("  -> Acorde: " + juce::String(noteName) + " | MIDI: " + juce::String(midiNote));
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
    repaint();
}