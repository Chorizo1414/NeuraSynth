#include "PianoRollComponent.h"
#include <string>
#include <vector>
#include <map>

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


PianoRollComponent::PianoRollComponent()
{
    // Constructor
}

PianoRollComponent::~PianoRollComponent() {}

void PianoRollComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour(0xff3c3c3c)); // Un fondo oscuro

    const int keyWidth = 25;
    const float noteHeight = 12.0f;
    const int lowestNote = 21; // A0
    const int highestNote = 108; // C8

    // Dibuja el fondo del piano roll
    g.setColour(juce::Colours::black.withAlpha(0.5f));
    for (int note = lowestNote; note <= highestNote; ++note)
    {
        // Alterna colores para las filas, como un piano roll real
        if (note % 12 == 1 || note % 12 == 3 || note % 12 == 6 || note % 12 == 8 || note % 12 == 10)
            g.setColour(juce::Colours::black.withAlpha(0.3f));
        else
            g.setColour(juce::Colours::transparentBlack);

        float y = (highestNote - note) * noteHeight;
        g.fillRect((float)keyWidth, y, (float)(getWidth() - keyWidth), noteHeight);
    }


    if (notes.isEmpty()) // Usa el método correcto de JUCE: isEmpty()
    {
        g.setColour(juce::Colours::lightgrey);
        g.drawText("Piano Roll - Esperando datos...", getLocalBounds(), juce::Justification::centred);
        return;
    }

    const float pixelsPerBeat = 60.0f;

    for (const auto& note : notes)
    {
        if (note.midiNote < lowestNote || note.midiNote > highestNote) continue;

        float x = keyWidth + (note.startTime * pixelsPerBeat);
        float y = (highestNote - note.midiNote) * noteHeight;
        float width = note.duration * pixelsPerBeat;

        g.setColour(note.isChordNote ? juce::Colours::cornflowerblue : juce::Colours::mediumspringgreen);
        g.fillRect(x, y, width, noteHeight);
        g.setColour(juce::Colours::black);
        g.drawRect(x, y, width, noteHeight, 1.0f);
    }
}

void PianoRollComponent::resized()
{
    // No se necesita nada aquí por ahora
}


void PianoRollComponent::setMusicData(const py::dict& data)
{
    notes.clear(); // Usa el método correcto de JUCE: clear()
    float time = 0.0f;

    try
    {
        // --- PROCESAR ACORDES ---
        if (data.contains("acordes") && data.contains("ritmo"))
        {
            py::list pyChords = data["acordes"];
            py::list pyRhythm = data["ritmo"];

            if (pyChords.size() != pyRhythm.size()) {
                DBG("!!! ADVERTENCIA: La lista de acordes y de ritmo tienen diferente tamano.");
            }

            for (size_t i = 0; i < pyChords.size(); ++i)
            {
                auto item = pyChords[i];
                float duration = pyRhythm[i].cast<float>();

                if (py::isinstance<py::list>(item))
                {
                    py::list noteList = item.cast<py::list>();
                    for (auto note : noteList)
                    {
                        std::string noteName = note.cast<std::string>();
                        int midiNote = noteNameToMidi(noteName);
                        if (midiNote != -1)
                        {
                            // Usa el método correcto de JUCE: add()
                            notes.add({ midiNote, time, duration, true });
                        }
                    }
                }
                time += duration;
            }
        }

        // --- PROCESAR MELODÍA ---
        if (data.contains("melodia"))
        {
            py::list pyMelody = data["melodia"];
            float melodyTime = 0.0f;

            for (auto item : pyMelody)
            {
                py::tuple noteTuple = item.cast<py::tuple>();
                std::string noteName = noteTuple[0].cast<std::string>();
                std::string durStr = noteTuple[1].cast<std::string>();
                float duration = std::stof(durStr);

                if (noteName != "0")
                {
                    int midiNote = noteNameToMidi(noteName);
                    if (midiNote != -1)
                    {
                        // Usa el método correcto de JUCE: add()
                        notes.add({ midiNote, melodyTime, duration, false });
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

    repaint();
}