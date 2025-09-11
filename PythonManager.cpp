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
    // El 'scoped_interpreter' del .h se encarga de esto automáticamente.
    // Pero si quieres ser explícito, puedes añadir py::finalize_interpreter();
    // aunque no es estrictamente necesario con el 'guard'.
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
        // 1. Obtener la función de Python desde el módulo importado
        auto generateFunc = neuraChordApi.attr("generar_acordes_desde_prompt");

        // 2. Llamar a la función de Python pasándole el prompt como argumento
        py::list pyResult = generateFunc(prompt.toStdString());

        // 3. Convertir la lista de Python a un juce::StringArray
        for (auto item : pyResult)
        {
            // Primero convertimos el objeto de Python a un std::string de C++
            std::string stdString = py::str(item);
            // Luego, creamos un juce::String a partir del std::string
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