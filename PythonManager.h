#pragma once
#include <juce_core/juce_core.h>

// --- Incluir Pybind11 ---
#include <pybind11/embed.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class PythonManager
{
public:
    PythonManager()
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


    ~PythonManager()
    {
        py::finalize_interpreter();
    }

    py::dict generateMusicData(const juce::String& prompt) const
    {
        py::dict result;
        if (!neuraChordApi)
        {
            DBG("PythonManager: neuraChordApi no es válido.");
            return result;
        }

        try
        {
            result = neuraChordApi.attr("generar_progresion")(prompt.toStdString());
        }
        catch (py::error_already_set& e)
        {
            DBG("!!! PYTHON CALL ERROR en generateMusicData: " << e.what());
        }

        return result;
    }

private:
    py::module neuraChordApi;
};