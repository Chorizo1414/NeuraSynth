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

    // Ahora devuelve un diccionario py::dict con toda la info (acordes, ritmo, etc.)
    py::dict generateMusicData(const juce::String& prompt);

    // Nueva función para generar la melodía
    py::dict generateMelodyData(const py::list& chords, const py::list& rhythm, const juce::String& root, const juce::String& mode, int bpm);

    juce::StringArray getAvailableGenres();

    juce::String exportChords(const py::dict& musicData, int bpm);
    juce::String exportMelody(const py::dict& musicData, int bpm);
    py::dict transposeMusic(const py::dict& musicData, int semitones);
private:
    py::module neuraChordApi;
};