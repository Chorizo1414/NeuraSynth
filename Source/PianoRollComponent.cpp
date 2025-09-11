#include "PianoRollComponent.h"

PianoRollComponent::PianoRollComponent() {}
PianoRollComponent::~PianoRollComponent() {}

void PianoRollComponent::setMidiSequence(const juce::MidiMessageSequence& sequence)
{
    midiSequence = sequence;
    repaint();
}

void PianoRollComponent::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);

    if (midiSequence.getNumEvents() == 0)
    {
        g.setColour(juce::Colours::lightgrey);
        g.drawText("Genera una melodía para visualizarla aquí", getLocalBounds(), juce::Justification::centred, 1);
        return;
    }

    double totalTime = midiSequence.getEndTime();
    if (totalTime <= 0) totalTime = 1.0;

    g.setColour(juce::Colours::cyan);

    for (int i = 0; i < midiSequence.getNumEvents(); ++i)
    {
        auto* event = midiSequence.getEventPointer(i);
        if (event->message.isNoteOn())
        {
            auto noteOn = event->message;
            double startTime = noteOn.getTimeStamp();

            // --- LÓGICA CORREGIDA PARA ENCONTRAR EL NOTE OFF ---
            double endTime = totalTime; // Por defecto, si no se encuentra el note off
            for (int j = i + 1; j < midiSequence.getNumEvents(); ++j)
            {
                auto* nextEvent = midiSequence.getEventPointer(j);
                if (nextEvent->message.isNoteOff() && nextEvent->message.getNoteNumber() == noteOn.getNoteNumber())
                {
                    endTime = nextEvent->message.getTimeStamp();
                    break; // Encontramos el note off, salimos del bucle
                }
            }
            // --- FIN DE LA LÓGICA CORREGIDA ---

            double duration = endTime - startTime;
            if (duration <= 0) continue; // No dibujar notas con duración cero o negativa

            int noteNumber = noteOn.getNoteNumber();
            float x = (startTime / totalTime) * getWidth();
            float y = (1.0f - ((noteNumber - 21.0f) / 88.0f)) * getHeight(); // Mapeo para un piano de 88 teclas
            float w = (duration / totalTime) * getWidth();
            float h = getHeight() / 88.0f;

            g.fillRect(juce::Rectangle<float>(x, y, w, h).reduced(0.5f));
        }
    }
}

void PianoRollComponent::resized() {}