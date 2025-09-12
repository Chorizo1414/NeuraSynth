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
    py::dict generateMelodyData(const py::list& chords, const py::list& rhythm, const juce::String& root, const juce::String& mode);

    juce::StringArray getAvailableGenres();
private:
    py::module neuraChordApi;
};