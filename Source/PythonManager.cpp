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
py::dict PythonManager::generateMusicData(const juce::String& prompt, int numChords)
{
    py::dict result;
    if (!neuraChordApi) {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        return result;
    }

    try {
        // La gil_scoped_acquire es crucial para la seguridad de hilos con Python
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_progresion")(prompt.toStdString(), numChords);
    }
    catch (const py::error_already_set& e) {
        DBG("Error de Python en generateMusicData: " << e.what());
    }
    return result;
}

// Implementación de la función para melodía
py::dict PythonManager::generateMelodyData(const py::list& chords, const py::list& rhythm, const juce::String& root, const juce::String& mode, int bpm)
{
    py::dict result;
    if (!neuraChordApi) {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        return result;
    }

    try {
        py::gil_scoped_acquire acquire;
        // --- MODIFICADO: Ahora usamos el BPM que recibimos como argumento ---
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

juce::String PythonManager::exportChords(const py::dict& musicData, int bpm)
{
    if (!neuraChordApi || !musicData.contains("acordes"))
        return "Error: No hay datos de acordes para exportar.";

    try
    {
        py::gil_scoped_acquire acquire;
        // Ahora usamos el BPM que viene como argumento
        py::dict result = neuraChordApi.attr("exportar_acordes_midi")(
            musicData["acordes"], musicData["ritmo"], bpm);

        if (result.contains("error") && !result["error"].cast<std::string>().empty())
            return "Error en Python: " + juce::String(result["error"].cast<std::string>());

        return "Acordes exportados a: " + juce::String(result["ruta"].cast<std::string>());
    }
    catch (const py::error_already_set& e)
    {
        return juce::String("Error de Python al exportar acordes: ") + e.what();
    }
}

juce::String PythonManager::exportMelody(const py::dict& musicData, int bpm)
{
    if (!neuraChordApi || !musicData.contains("melodia"))
        return "Error: No hay datos de melodia para exportar.";

    try
    {
        py::gil_scoped_acquire acquire;
        // Ahora usamos el BPM que viene como argumento
        py::dict result = neuraChordApi.attr("exportar_melodia_midi")(
            musicData["melodia"], bpm);

        if (result.contains("error") && !result["error"].cast<std::string>().empty())
            return "Error en Python: " + juce::String(result["error"].cast<std::string>());

        return "Melodia exportada a: " + juce::String(result["ruta"].cast<std::string>());
    }
    catch (const py::error_already_set& e)
    {
        return juce::String("Error de Python al exportar melodia: ") + e.what();
    }
}

py::dict PythonManager::transposeMusic(const py::dict& musicData, int semitones)
{
    py::dict result;
    if (!neuraChordApi)
    {
        result["error"] = "Modulo neurachord_api no cargado.";
        return result;
    }
    try
    {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("transponer_musica")(musicData, semitones);
    }
    catch (const py::error_already_set& e)
    {
        py::dict errorDict;
        errorDict["error"] = juce::String("Error de Python en transposeMusic: ") + e.what();
        return errorDict;
    }
    return result;
}

void PythonManager::like()
{
    if (!neuraChordApi) return;
    try
    {
        py::gil_scoped_acquire acquire;
        // CORRECCIÓN: Llamamos a la función a través del generador de acordes
        neuraChordApi.attr("generador_acordes").attr("puntuar_acordes_positivamente")();
        DBG("PythonManager: 'Like' action sent.");
    }
    catch (const py::error_already_set& e)
    {
        DBG("Python Error en like(): " << e.what());
    }
}

void PythonManager::dislike()
{
    if (!neuraChordApi) return;
    try
    {
        py::gil_scoped_acquire acquire;
        // CORRECCIÓN: Llamamos a la función a través del generador de acordes
        neuraChordApi.attr("generador_acordes").attr("puntuar_acordes_negativamente")();
        DBG("PythonManager: 'Dislike' action sent.");
    }
    catch (const py::error_already_set& e)
    {
        DBG("Python Error en dislike(): " << e.what());
    }
}