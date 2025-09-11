#pragma once
#include <JuceHeader.h>

// --- Incluir Pybind11 ---
#include <pybind11/embed.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class PythonManager
{
public:
    PythonManager();
    ~PythonManager();
    juce::StringArray generateChordProgression(const juce::String& prompt, const juce::String& genre, const juce::String& sentiment);
    py::dict generateMusicData(const juce::String& prompt);
private:
    py::module neuraChordApi;
};