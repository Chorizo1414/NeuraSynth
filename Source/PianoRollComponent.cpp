#include "PianoRollComponent.h"

PianoRollComponent::PianoRollComponent() {}
PianoRollComponent::~PianoRollComponent() {}

void PianoRollComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::darkgrey.darker());
    drawGrid(g);
    drawKeys(g);
    drawNotes(g);
}

void PianoRollComponent::resized() {}

void PianoRollComponent::setMusicData(const py::dict& data)
{
    notes.clear();

    // Extraemos acordes
    if (data.contains("acordes") && py::isinstance<py::list>(data["acordes"]))
    {
        py::list chords = data["acordes"];
        double time = 0.0;
        for (const auto& chord_handle : chords)
        {
            py::list chord_notes = chord_handle.cast<py::list>();
            for (const auto& note_handle : chord_notes)
            {
                int noteNum = note_handle.cast<int>();

                // Forma correcta de crear el mensaje y asignarle el tiempo
                auto noteOn = juce::MidiMessage::noteOn(1, noteNum, (juce::uint8)100);
                noteOn.setTimeStamp(time);
                notes.add(noteOn);

                auto noteOff = juce::MidiMessage::noteOff(1, noteNum);
                noteOff.setTimeStamp(time + 0.95); // Duración de casi 1 beat
                notes.add(noteOff);
            }
            time += 1.0; // Avanzamos 1 beat por cada acorde
        }
    }

    // Extraemos melodía
    if (data.contains("melodia") && py::isinstance<py::list>(data["melodia"]))
    {
        py::list melody_events = data["melodia"];
        for (const auto& event_handle : melody_events)
        {
            py::list event_data = event_handle.cast<py::list>();
            int noteNum = event_data[0].cast<int>();
            double startTime = event_data[1].cast<double>();
            double duration = event_data[2].cast<double>();

            auto noteOn = juce::MidiMessage::noteOn(1, noteNum, (juce::uint8)120);
            noteOn.setTimeStamp(startTime);
            notes.add(noteOn);

            auto noteOff = juce::MidiMessage::noteOff(1, noteNum);
            noteOff.setTimeStamp(startTime + duration);
            notes.add(noteOff);
        }
    }

    repaint();
}

void PianoRollComponent::drawGrid(juce::Graphics& g)
{
    auto bounds = getLocalBounds().withLeft((int)keyWidth);
    g.setColour(juce::Colours::black.withAlpha(0.5f));

    // Dibuja líneas verticales para los beats
    for (int i = 0; i < 16; ++i)
    {
        float x = bounds.getX() + (float)i * bounds.getWidth() / 16.0f;
        g.drawVerticalLine((int)x, (float)bounds.getY(), (float)bounds.getBottom());
    }

    // Dibuja líneas horizontales para cada nota
    int numKeys = highestNote - lowestNote;
    for (int i = 0; i <= numKeys; ++i)
    {
        int midiNote = highestNote - i;
        bool isBlackKey = juce::MidiMessage::isMidiNoteBlack(midiNote);
        if (!isBlackKey)
        {
            float y = (float)bounds.getY() + (float)i * (float)bounds.getHeight() / (float)numKeys;
            g.drawHorizontalLine((int)y, (float)bounds.getX(), (float)bounds.getRight());
        }
    }
}

void PianoRollComponent::drawKeys(juce::Graphics& g)
{
    auto bounds = getLocalBounds();
    auto keysArea = bounds.withWidth((int)keyWidth);
    int numKeys = highestNote - lowestNote;

    for (int i = 0; i <= numKeys; ++i)
    {
        float y = (float)keysArea.getY() + (float)i * (float)keysArea.getHeight() / (float)numKeys;
        float h = (float)keysArea.getHeight() / (float)numKeys;
        int midiNote = highestNote - i;

        if (!juce::MidiMessage::isMidiNoteBlack(midiNote))
        {
            g.setColour(juce::Colours::white);
            g.fillRect((float)keysArea.getX(), y, (float)keysArea.getWidth(), h);
            g.setColour(juce::Colours::black);
            g.drawRect((float)keysArea.getX(), y, (float)keysArea.getWidth(), h, 0.5f);
        }
    }

    for (int i = 0; i <= numKeys; ++i)
    {
        float y = (float)keysArea.getY() + (float)i * (float)keysArea.getHeight() / (float)numKeys;
        float h = (float)keysArea.getHeight() / (float)numKeys;
        int midiNote = highestNote - i;

        if (juce::MidiMessage::isMidiNoteBlack(midiNote))
        {
            g.setColour(juce::Colours::black);
            g.fillRect((float)keysArea.getX(), y - h / 2.0f, (float)keysArea.getWidth() * 0.6f, h);
        }
    }
}

void PianoRollComponent::drawNotes(juce::Graphics& g)
{
    auto bounds = getLocalBounds().withLeft((int)keyWidth);
    int numKeys = highestNote - lowestNote;
    float keyHeight = (float)bounds.getHeight() / (float)numKeys;
    float pixelsPerBeat = (float)bounds.getWidth() / 16.0f;

    for (const auto& onMessage : notes)
    {
        if (!onMessage.isNoteOn()) continue;

        for (const auto& offMessage : notes)
        {
            // Buscamos su correspondiente Note Off
            if (offMessage.isNoteOff() && offMessage.getNoteNumber() == onMessage.getNoteNumber() && offMessage.getTimeStamp() > onMessage.getTimeStamp())
            {
                // Conversión explícita a float para resolver la ambigüedad
                float x = (float)bounds.getX() + (float)onMessage.getTimeStamp() * pixelsPerBeat;
                float y = (float)bounds.getY() + (float)(highestNote - onMessage.getNoteNumber()) * keyHeight;
                float w = (float)(offMessage.getTimeStamp() - onMessage.getTimeStamp()) * pixelsPerBeat;
                float h = keyHeight;

                g.setColour(juce::Colour(0xff8a2be2)); // Azul violeta
                g.fillRect(x, y, w, h);
                g.setColour(juce::Colours::black);
                g.drawRect(x, y, w, h, 1.0f);

                break;
            }
        }
    }
}