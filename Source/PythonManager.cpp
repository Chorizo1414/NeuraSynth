#include "PythonManager.h"

PythonManager::PythonManager()
{
    initializePython();
    midiFile = juce::File::getSpecialLocation(juce::File::tempDirectory).getChildFile("temp_midi.mid");
}

PythonManager::~PythonManager()
{
    shutdownPython();
}

void PythonManager::initializePython()
{
    try
    {
        py::module_ sys = py::module_::import("sys");
        // La ruta debe apuntar a la carpeta que contiene neurachord_api.py
        sys.attr("path").attr("append")("C:/Users/Darkm/Documents/GitHub/NeuraSynth/Source/NeuraChord");
        neurachord_api = py::module_::import("neurachord_api");
    }
    catch (py::error_already_set& e)
    {
        juce::Logger::writeToLog(e.what());
    }
}

void PythonManager::shutdownPython()
{
    neurachord_api.release();
}

// ---- IMPLEMENTACIÓN DE LAS NUEVAS FUNCIONES ----

void PythonManager::callGenerateMusic(const std::string& text)
{
    if (python_thread && python_thread->joinable()) {
        python_thread->join();
    }
    python_thread = std::make_unique<std::thread>([this, text]() {
        try {
            if (neurachord_api) {
                // Llama solo a la generación y guardado del MIDI
                neurachord_api.attr("generar_y_guardar_midi")(text, midiFile.getFullPathName().toStdString());
                juce::Logger::writeToLog("MIDI generado en: " + midiFile.getFullPathName());
            }
        }
        catch (py::error_already_set& e) {
            juce::Logger::writeToLog(e.what());
        }
        });
    // Esperamos a que el hilo de generación termine para asegurar que el archivo existe
    if (python_thread && python_thread->joinable()) {
        python_thread->join();
    }
}

void PythonManager::playGeneratedMidi()
{
    if (python_thread && python_thread->joinable()) {
        python_thread->join();
    }
    python_thread = std::make_unique<std::thread>([this]() {
        try {
            if (neurachord_api && midiFile.existsAsFile()) {
                // Llama solo a la reproducción
                neurachord_api.attr("reproducir_midi")(midiFile.getFullPathName().toStdString());
            }
        }
        catch (py::error_already_set& e) {
            juce::Logger::writeToLog(e.what());
        }
        });
}

void PythonManager::stopMidiPlayback()
{
    detenerMusica(); // Reutilizamos la función original para detener
}

juce::File PythonManager::getMidiFilePath()
{
    return midiFile;
}

// ---- FUNCIONES ORIGINALES ----

void PythonManager::generarYReproducirMusica(const std::string& text)
{
    if (python_thread && python_thread->joinable()) {
        python_thread->join();
    }
    python_thread = std::make_unique<std::thread>([this, text]() {
        try {
            if (neurachord_api) {
                neurachord_api.attr("generar_y_reproducir_musica")(text);
            }
        }
        catch (py::error_already_set& e) {
            juce::Logger::writeToLog(e.what());
        }
        });
}

void PythonManager::detenerMusica()
{
    if (python_thread && python_thread->joinable()) {
        python_thread->join();
    }
    python_thread = std::make_unique<std::thread>([this]() {
        try {
            if (neurachord_api) {
                neurachord_api.attr("detener_musica")();
            }
        }
        catch (py::error_already_set& e) {
            juce::Logger::writeToLog(e.what());
        }
        });
}