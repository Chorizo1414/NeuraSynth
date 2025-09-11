#include "PythonManager.h"

PythonManager::PythonManager()
{
    try
    {
        // ++ PASO 1: ESTABLECEMOS EL "HOGAR" DE PYTHON ++
        // Pon aquí la ruta a tu carpeta principal de Python 3.8
        _putenv_s("PYTHONHOME", "C:\\Users\\Progra.CHORI1414\\AppData\\Local\\Programs\\Python\\Python38");
        
        py::initialize_interpreter();
        auto sys = py::module::import("sys");
        
        // ++ PASO 2: AÑADIMOS LA RUTA A TUS SCRIPTS ++
        // Usa la ruta absoluta a tu carpeta NeuraChord
        sys.attr("path").attr("append")("C:\\Users\\Progra.CHORI1414\\Desktop\\Proyectos\\JUCE\\NeuraSynth\\Source\\NeuraChord");
        
        // ++ PASO 3: INTENTAMOS IMPORTAR TU API ++
        neuraChordApi = py::module::import("neurachord_api");
        
        DBG("PythonManager: ¡Intérprete y neurachord_api importados con ÉXITO!");
    }
    catch (py::error_already_set& e)
    {
        DBG("!!! PYBIND11 ERROR: " << e.what());
    }
    catch (const std::exception& e)
    {
        DBG("!!! STD EXCEPTION ERROR: " << e.what());
    }
}

PythonManager::~PythonManager()
{
    py::finalize_interpreter();
}

juce::StringArray PythonManager::generateChordProgression(const juce::String& prompt)
{
    juce::StringArray generatedChords;

    // Asegurarnos de que el módulo de la API esté cargado
    if (!neuraChordApi)
    {
        DBG("ERROR: Módulo neurachord_api no cargado.");
        return generatedChords;
    }

    // Bloqueo del Global Interpreter Lock (GIL) para seguridad en hilos
    py::gil_scoped_acquire acquire;

    try
    {
        //    Ahora se llama "generar_progresion" en la API de Python
        auto generateFunc = neuraChordApi.attr("generar_progresion");

        // 2. Llamar a la función de Python pasándole el prompt como argumento y obtener un diccionario
        py::dict result = generateFunc(prompt.toStdString()).cast<py::dict>();

            // Verificar que exista la clave "acordes" en el resultado
            if (!result.contains("acordes"))
            {
                DBG("Error: la respuesta de Python no contiene la clave 'acordes'.");
                return generatedChords;
            }

        // 3. Obtener la lista de acordes y convertirla en juce::StringArray
        py::list pyChords = result["acordes"].cast<py::list>();
        for (auto item : pyChords)
        {
            std::string stdString = py::str(item);
            generatedChords.add(juce::String(stdString));
        }
    }
    catch (const py::error_already_set& e)
    {
        // Si algo sale mal en Python, lo mostramos en la consola de JUCE
        DBG("Error de Python: " << e.what());
    }

    return generatedChords;
}

py::dict PythonManager::generateMusicData(const juce::String& prompt)
{
    py::dict result;

    if (!neuraChordApi)
    {
        DBG("ERROR: Módulo neurachord_api no cargado.");
        return result;
    }

    py::gil_scoped_acquire acquire;

    try
    {
        result = neuraChordApi.attr("generar_progresion")(prompt.toStdString()).cast<py::dict>();
    }
    catch (const py::error_already_set& e)
    {
        DBG("Error de Python: " << e.what());
    }

    return result;
}