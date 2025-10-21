#pragma once
#include <JuceHeader.h>
#include <pybind11/embed.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class PythonManager
{
public:
    PythonManager();
    ~PythonManager();

    // --- Funciones de NeuraChord ---
    py::dict generateMusicData(const juce::String& prompt, int numChords = -1);
    py::dict generateMusicData(const juce::String& prompt, int numChords, const py::list& melody, int bpm);
    py::dict generateMelodyData(const py::list& chords, const py::list& rhythm, const juce::String& root, const juce::String& mode, int bpm);
    py::dict generateMelodyFromPrompt(const juce::String& prompt, int numChords, int bpm);
    juce::StringArray getAvailableGenres();
    juce::String exportChords(const py::dict& musicData, int bpm);
    juce::String exportMelody(const py::dict& musicData, int bpm);
    py::dict transposeMusic(const py::dict& musicData, int semitones);
    void like();
    void dislike();
    void updateEditedMusic(const py::dict& musicData);

    // ---> AADE ESTA NUEVA LNEA <---
    // --- Funcin del Generador de Sonido ---
    py::dict generateSynthSound(const juce::String& prompt);

    bool likeLastSound();
    pybind11::dict getLearnedSounds();
    juce::StringArray getSoundArchetypes();

private:
    py::module neuraChordApi;
};