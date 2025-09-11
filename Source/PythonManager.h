#pragma once
#include <JuceHeader.h>
#include <pybind11/embed.h>
#include <thread>

namespace py = pybind11;

class PythonManager
{
public:
    PythonManager();
    ~PythonManager();

    // NUEVAS FUNCIONES (MÁS ESPECÍFICAS)
    void callGenerateMusic(const std::string& text);
    void playGeneratedMidi();
    void stopMidiPlayback();
    juce::File getMidiFilePath();

    // Funciones originales (las mantenemos por si acaso)
    void generarYReproducirMusica(const std::string& text);
    void detenerMusica();

private:
    void initializePython();
    void shutdownPython();

    py::scoped_interpreter guard{};
    py::object neurachord_api;
    std::unique_ptr<std::thread> python_thread;
    juce::File midiFile;
};