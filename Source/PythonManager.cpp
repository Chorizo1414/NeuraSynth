#include "PythonManager.h"

PythonManager::PythonManager()
{
    try {
        _putenv_s("PYTHONHOME", "C:\\Users\\Progra.CHORI1414\\AppData\\Local\\Programs\\Python\\Python38");
        py::initialize_interpreter();
        auto sys = py::module::import("sys");
        sys.attr("path").attr("append")("C:\\Users\\Progra.CHORI1414\\Desktop\\Proyectos\\JUCE\\NeuraSynth\\Source\\NeuraChord");
        neuraChordApi = py::module::import("neurachord_api");
        DBG("PythonManager: Interprete y neurachord_api importados con EXITO!");
    }
    catch (const std::exception& e) {
        DBG("!!! PYTHON MANAGER ERROR: " << e.what());
    }
}

PythonManager::~PythonManager()
{
    py::finalize_interpreter();
}

// Implementación de la nueva función
py::dict PythonManager::generateMusicData(const juce::String& prompt)
{
    py::dict result;
    if (!neuraChordApi) {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        return result;
    }

    try {
        // La gil_scoped_acquire es crucial para la seguridad de hilos con Python
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_progresion")(prompt.toStdString());
    }
    catch (const py::error_already_set& e) {
        DBG("Error de Python en generateMusicData: " << e.what());
    }
    return result;
}

// Implementación de la función para melodía
py::dict PythonManager::generateMelodyData(const py::list& chords, const py::list& rhythm, const juce::String& root, const juce::String& mode)
{
    py::dict result;
    if (!neuraChordApi) {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        return result;
    }

    try {
        py::gil_scoped_acquire acquire;
        // BPM fijo por ahora, luego lo podemos hacer un parámetro de la UI
        int bpm = 120;
        result = neuraChordApi.attr("generar_melodia")(chords, rhythm, root.toStdString(), mode.toStdString(), bpm);
    }
    catch (const py::error_already_set& e) {
        DBG("Error de Python en generateMelodyData: " << e.what());
    }
    return result;
}

juce::StringArray PythonManager::getAvailableGenres()
{
    juce::StringArray genres;
    if (!neuraChordApi)
    {
        DBG("ERROR: Modulo neurachord_api no cargado, no se pueden obtener generos.");
        return genres;
    }

    try
    {
        py::gil_scoped_acquire acquire;
        py::list pyGenres = neuraChordApi.attr("get_available_genres")();
        for (auto item : pyGenres)
        {
            genres.add(item.cast<std::string>());
        }
    }
    catch (const py::error_already_set& e)
    {
        DBG("!!! Error de Python en getAvailableGenres: " << e.what());
    }
    return genres;
}