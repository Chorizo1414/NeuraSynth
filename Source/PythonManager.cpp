#include "PythonManager.h"
#include <mutex>
#include <vector>
#include <cstdlib>

namespace
{
    std::mutex pythonInitMutex;
    bool pythonInterpreterReady = false;

    using FileList = std::vector<juce::File>;

    juce::String getPathListSeparator()
    {
#if JUCE_WINDOWS
        return ";";
#else
        return ":";
#endif
    }

    void setEnvironmentVariable(const juce::String& name, const juce::String& value)
    {
#if JUCE_WINDOWS
        _putenv_s(name.toRawUTF8(), value.toRawUTF8());
#else
        ::setenv(name.toRawUTF8(), value.toRawUTF8(), 1);
#endif
    }

    void appendIfUnique(FileList& files, const juce::File& candidate)
    {
        if (candidate == juce::File())
            return;

        const auto path = candidate.getFullPathName();
        if (path.isEmpty())
            return;

        for (const auto& existing : files)
            if (existing.getFullPathName() == path)
                return;

        files.push_back(candidate);
    }

    FileList enumerateBaseDirectories()
    {
        FileList bases;

        const juce::File currentExecutable = juce::File::getSpecialLocation(juce::File::currentExecutableFile);
        if (currentExecutable.existsAsFile())
        {
            auto directory = currentExecutable.getParentDirectory();
            for (int i = 0; i < 8 && directory != juce::File(); ++i)
            {
                appendIfUnique(bases, directory);
                appendIfUnique(bases, directory.getChildFile("Resources"));
                appendIfUnique(bases, directory.getChildFile("Python"));
                directory = directory.getParentDirectory();
            }
        }

        const juce::File invokedExecutable = juce::File::getSpecialLocation(juce::File::invokedExecutableFile);
        if (invokedExecutable.existsAsFile())
        {
            auto directory = invokedExecutable.getParentDirectory();
            for (int i = 0; i < 6 && directory != juce::File(); ++i)
            {
                appendIfUnique(bases, directory);
                appendIfUnique(bases, directory.getChildFile("Resources"));
                appendIfUnique(bases, directory.getChildFile("Python"));
                directory = directory.getParentDirectory();
            }
        }

#if JUCE_WINDOWS
        const juce::File programFiles = juce::File::getSpecialLocation(juce::File::globalApplicationsDirectory);
        appendIfUnique(bases, programFiles.getChildFile("NeuraSynth"));
        appendIfUnique(bases, programFiles.getChildFile("NeuraSynth").getChildFile("Python"));

        const juce::File commonAppData = juce::File::getSpecialLocation(juce::File::commonApplicationDataDirectory);
        appendIfUnique(bases, commonAppData.getChildFile("NeuraSynth"));
        appendIfUnique(bases, commonAppData.getChildFile("NeuraSynth").getChildFile("Python"));
#endif

        return bases;
    }

    bool looksLikePythonHome(const juce::File& directory)
    {
        if (!directory.isDirectory())
            return false;

        static const char* pythonDlls[] = { "python38.dll", "python39.dll", "python310.dll", "python311.dll" };

        auto hasRuntimeLibraryIn = [](const juce::File& candidate)
            {
                if (!candidate.isDirectory())
                    return false;

                for (auto* dll : pythonDlls)
                {
                    if (candidate.getChildFile(dll).existsAsFile())
                        return true;
                }

                if (candidate.getChildFile("python3.dll").existsAsFile())
                    return true;

                if (candidate.getChildFile("python.exe").existsAsFile()
                    || candidate.getChildFile("pythonw.exe").existsAsFile())
                    return true;

                juce::Array<juce::File> pythonZips;
                candidate.findChildFiles(pythonZips, juce::File::findFiles, false, "python3*.zip");
                return !pythonZips.isEmpty();
            };

        bool hasRuntimeLibrary = hasRuntimeLibraryIn(directory);
        if (!hasRuntimeLibrary)
        {
            const auto parent = directory.getParentDirectory();
            hasRuntimeLibrary = hasRuntimeLibraryIn(parent);
        }

        if (!hasRuntimeLibrary)
            return false;

        auto hasLibStructure = [](const juce::File& candidate)
            {
                if (!candidate.isDirectory())
                    return false;

                if (candidate.getChildFile("Lib").isDirectory()
                    || candidate.getChildFile("lib").isDirectory())
                    return true;

                juce::Array<juce::File> pythonZips;
                candidate.findChildFiles(pythonZips, juce::File::findFiles, false, "python3*.zip");
                if (!pythonZips.isEmpty())
                    return true;

                const auto binDir = candidate.getChildFile("bin");
                if (binDir.isDirectory() && candidate.getChildFile("lib").isDirectory())
                    return true;

                return false;
            };

        if (hasLibStructure(directory))
            return true;

        const auto embeddedPythonDir = directory.getChildFile("Python");
        if (hasLibStructure(embeddedPythonDir))
            return true;

        return false;
    }

    juce::File findPythonHome()
    {
        const juce::String envOverride = juce::SystemStats::getEnvironmentVariable("NEURASYNTH_PYTHON_HOME", {});
        if (envOverride.isNotEmpty())
        {
            juce::File envCandidate(envOverride);
            if (looksLikePythonHome(envCandidate))
                return envCandidate;
        }

        for (const auto& base : enumerateBaseDirectories())
        {
            if (looksLikePythonHome(base))
                return base;

            const auto pythonDir = base.getChildFile("Python");
            if (looksLikePythonHome(pythonDir))
                return pythonDir;

            if (pythonDir.isDirectory())
            {
                juce::DirectoryIterator iterator(pythonDir, false, "*", juce::File::findDirectories);
                while (iterator.next())
                {
                    const auto subDirectory = iterator.getFile();
                    if (looksLikePythonHome(subDirectory))
                        return subDirectory;
                }
            }
        }

        return {};
    }

    juce::File findNeuraChordRoot(const juce::File& pythonHome)
    {
        const juce::String envOverride = juce::SystemStats::getEnvironmentVariable("NEURASYNTH_PYTHON_MODULE", {});
        if (envOverride.isNotEmpty())
        {
            juce::File envCandidate(envOverride);
            if (envCandidate.isDirectory())
                return envCandidate;
        }

        if (pythonHome.isDirectory())
        {
            const juce::File direct = pythonHome.getChildFile("NeuraChord");
            if (direct.isDirectory())
                return direct;

            const juce::File sitePackages = pythonHome.getChildFile("Lib").getChildFile("site-packages").getChildFile("NeuraChord");
            if (sitePackages.isDirectory())
                return sitePackages;
        }

        for (const auto& base : enumerateBaseDirectories())
        {
            const juce::File direct = base.getChildFile("NeuraChord");
            if (direct.isDirectory())
                return direct;

            const juce::File inPython = base.getChildFile("Python").getChildFile("NeuraChord");
            if (inPython.isDirectory())
                return inPython;

            const juce::File inResources = base.getChildFile("Resources").getChildFile("NeuraChord");
            if (inResources.isDirectory())
                return inResources;

            const juce::File inSource = base.getChildFile("Source").getChildFile("NeuraChord");
            if (inSource.isDirectory())
                return inSource;
        }

        return {};
    }
}

PythonManager::PythonManager()
{
    try {
        std::scoped_lock<std::mutex> lock(pythonInitMutex);

        runtimeAvailable.store(false);

        const juce::File pythonHome = findPythonHome();
        const bool hasEmbeddedRuntime = pythonHome.isDirectory();
        if (!hasEmbeddedRuntime)
            DBG("!!! PYTHON MANAGER ERROR: No se encontró el runtime embebido de Python. Se intentará usar el intérprete global si está disponible.");

        const juce::File neuraChordRoot = findNeuraChordRoot(pythonHome);

        juce::StringArray pythonPathEntries;
        auto addPathEntry = [&pythonPathEntries](const juce::String& path)
            {
                if (path.isNotEmpty())
                    pythonPathEntries.addIfNotAlreadyThere(path);
            };

        if (hasEmbeddedRuntime)
        {
            addPathEntry(pythonHome.getFullPathName());

            const juce::File libDir = pythonHome.getChildFile("Lib");
            if (libDir.isDirectory())
            {
                addPathEntry(libDir.getFullPathName());

                const juce::File sitePackages = libDir.getChildFile("site-packages");
                if (sitePackages.isDirectory())
                    addPathEntry(sitePackages.getFullPathName());
            }
        }

        if (neuraChordRoot.isDirectory())
            addPathEntry(neuraChordRoot.getFullPathName());

        const juce::String existingPythonPath = juce::SystemStats::getEnvironmentVariable("PYTHONPATH", {});
        if (existingPythonPath.isNotEmpty())
        {
            juce::StringArray existingEntries;
            existingEntries.addTokens(existingPythonPath, getPathListSeparator(), "\"");
            existingEntries.trim();
            existingEntries.removeEmptyStrings();

            for (const auto& entry : existingEntries)
                addPathEntry(entry);
        }

        if (hasEmbeddedRuntime)
            setEnvironmentVariable("PYTHONHOME", pythonHome.getFullPathName());


        if (pythonPathEntries.size() > 0)
        {
            const juce::String combinedPythonPath = pythonPathEntries.joinIntoString(getPathListSeparator());
            setEnvironmentVariable("PYTHONPATH", combinedPythonPath);
        }

        if (!pythonInterpreterReady)
        {
            py::initialize_interpreter();
            pythonInterpreterReady = true;
        }

        py::gil_scoped_acquire acquire;
        auto sys = py::module::import("sys");
        py::list sysPath = sys.attr("path");

        for (const auto& entry : pythonPathEntries)
        {
            bool alreadyPresent = false;
            for (auto item : sysPath)
            {
                if (item.cast<std::string>() == entry.toStdString())
                {
                    alreadyPresent = true;
                    break;
                }
            }

            if (!alreadyPresent)
                sysPath.attr("append")(entry.toStdString());
        }

        neuraChordApi = py::module::import("neurachord_api");
        runtimeAvailable.store(true);
        DBG("PythonManager: Interprete y neurachord_api importados con EXITO!");
    }
    catch (const std::exception& e) {
        DBG("!!! PYTHON MANAGER ERROR: " << e.what());
        runtimeAvailable.store(false);
    }
}

PythonManager::~PythonManager()
{
    std::scoped_lock<std::mutex> lock(pythonInitMutex);

    if (!pythonInterpreterReady)
        return;

    try
    {
        py::gil_scoped_acquire acquire;
        neuraChordApi = py::module();
    }
    catch (const std::exception& e)
    {
        DBG("PythonManager::~PythonManager - error liberando modulo: " << e.what());
    }

    runtimeAvailable.store(false);
    // No finalizamos el interprete para evitar cierres inesperados cuando otros objetos
    // de Python (py::dict, etc.) aun estan vivos. El interprete permanece activo durante
    // toda la vida del proceso, lo que es seguro en el contexto del plugin standalone/host.
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

py::dict PythonManager::generateMusicData(const juce::String& prompt, int numChords, const py::list& melody, int bpm)
{
    py::dict result;
    if (!neuraChordApi)
    {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        return result;
    }

    try
    {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_progresion")(prompt.toStdString(), numChords, melody, bpm);
    }
    catch (const py::error_already_set& e)
    {
        DBG("Error de Python en generateMusicData (melodia): " << e.what());
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

py::dict PythonManager::generateMelodyFromPrompt(const juce::String& prompt, int numChords, int bpm)
{
    py::dict result;
    if (!neuraChordApi) {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        return result;
    }

    try
    {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_melodia_desde_prompt")(prompt.toStdString(), numChords, bpm);
    }
    catch (const py::error_already_set& e)
    {
        DBG("Error de Python en generateMelodyFromPrompt: " << e.what());
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
        lastExportedChordsFile = juce::File();
        // Ahora usamos el BPM que viene como argumento
        py::object detalles;
        if (musicData.contains("acordes_detallados"))
            detalles = py::reinterpret_borrow<py::object>(musicData["acordes_detallados"]);
        else
            detalles = py::none();

        py::object tiempos;
        if (musicData.contains("acordes_tiempos"))
            tiempos = py::reinterpret_borrow<py::object>(musicData["acordes_tiempos"]);
        else
            tiempos = py::none();

        py::object resultObj = neuraChordApi.attr("exportar_acordes_midi")(
            musicData["acordes"], musicData["ritmo"], bpm, detalles, tiempos);

        if (resultObj.is_none())
            return "Error de Python al exportar acordes: sin respuesta.";

        if (!py::isinstance<py::dict>(resultObj))
            return "Error de Python al exportar acordes: resultado inesperado.";

        py::dict result = resultObj.cast<py::dict>();

        if (result.contains("error") && !result["error"].cast<std::string>().empty())
            return "Error en Python: " + juce::String(result["error"].cast<std::string>());

        auto ruta = result.contains("ruta") ? result["ruta"].cast<std::string>() : std::string();
        if (!ruta.empty())
            lastExportedChordsFile = juce::File(ruta);

        return ruta.empty() ? juce::String("Acordes exportados.")
            : juce::String("Acordes exportados a: ") + ruta;
    }
    catch (const py::type_error& e)
    {
        lastExportedChordsFile = juce::File();
        return juce::String("Error de tipo al exportar acordes: ") + e.what();
    }
    catch (const py::error_already_set& e)
    {
        lastExportedChordsFile = juce::File();
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
        lastExportedMelodyFile = juce::File();
        // Ahora usamos el BPM que viene como argumento
        py::object resultObj = neuraChordApi.attr("exportar_melodia_midi")(
            musicData["melodia"], bpm);

        if (resultObj.is_none())
            return "Error de Python al exportar melodia: sin respuesta.";

        if (!py::isinstance<py::dict>(resultObj))
            return "Error de Python al exportar melodia: resultado inesperado.";

        py::dict result = resultObj.cast<py::dict>();

        if (result.contains("error") && !result["error"].cast<std::string>().empty())
            return "Error en Python: " + juce::String(result["error"].cast<std::string>());

        auto ruta = result.contains("ruta") ? result["ruta"].cast<std::string>() : std::string();
        if (!ruta.empty())
            lastExportedMelodyFile = juce::File(ruta);

        return ruta.empty() ? juce::String("Melodia exportada.")
            : juce::String("Melodia exportada a: ") + ruta;
    }
    catch (const py::type_error& e)
    {
        lastExportedMelodyFile = juce::File();
        return juce::String("Error de tipo al exportar melodia: ") + e.what();
    }
    catch (const py::error_already_set& e)
    {
        lastExportedMelodyFile = juce::File();
        return juce::String("Error de Python al exportar melodia: ") + e.what();
    }
}

juce::File PythonManager::getLastExportedChordsFile() const
{
    return lastExportedChordsFile;
}

juce::File PythonManager::getLastExportedMelodyFile() const
{
    return lastExportedMelodyFile;
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
        // La llamada correcta y directa a la API de Python
        neuraChordApi.attr("puntuar_positivamente")();
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
        // La llamada correcta y directa a la API de Python
        neuraChordApi.attr("puntuar_negativamente")();
        DBG("PythonManager: 'Dislike' action sent.");
    }
    catch (const py::error_already_set& e)
    {
        DBG("Python Error en dislike(): " << e.what());
    }
}

void PythonManager::updateEditedMusic(const py::dict& musicData)
{
    if (!neuraChordApi)
        return;

    try
    {
        py::gil_scoped_acquire acquire;
        neuraChordApi.attr("actualizar_progresion_editada")(musicData);
    }
    catch (const py::type_error& e)
    {
        DBG("Python type_error en updateEditedMusic(): " << e.what());
    }
    catch (const py::error_already_set& e)
    {
        DBG("Python Error en updateEditedMusic(): " << e.what());
    }
    catch (const std::exception& e)
    {
        DBG("Excepcion en updateEditedMusic(): " << e.what());
    }
}

py::dict PythonManager::generateSynthSound(const juce::String& prompt)
{
    py::dict result;
    if (!neuraChordApi) {
        DBG("ERROR: Modulo neurachord_api no cargado.");
        result["error"] = "Modulo neurachord_api no cargado.";
        return result;
    }

    try {
        py::gil_scoped_acquire acquire;
        // Llamamos a la nueva función 'generar_sonido' de nuestro script Python
        result = neuraChordApi.attr("generar_sonido")(prompt.toStdString());
    }
    catch (const py::error_already_set& e) {
        DBG("Error de Python en generateSynthSound: " << e.what());
        py::dict errorDict;
        errorDict["error"] = juce::String("Error de Python en generateSynthSound: ") + e.what();
        return errorDict;
    }
    return result;
}

bool PythonManager::likeLastSound()
{
    if (!neuraChordApi)
    {
        DBG("ERROR: Modulo neurachord_api no cargado, no se puede dar like.");
        return false; // Retornamos falso si no hay módulo
    }

    try
    {
        py::gil_scoped_acquire acquire;
        // 1. Llamamos a la función de Python y guardamos el resultado
        py::dict result = neuraChordApi.attr("like_last_sound")();

        // 2. Comprobamos si el resultado fue exitoso
        if (result.contains("status") && result["status"].cast<std::string>() == "ok")
        {
            DBG("PythonManager: 'Like Sound' action sent successfully.");
            return true; // Éxito
        }
    }
    catch (const py::error_already_set& e)
    {
        DBG("!!! Error de Python en likeLastSound(): " << e.what());
    }

    // Si algo falla, retornamos falso
    return false;
}

pybind11::dict PythonManager::getLearnedSounds()
{
    pybind11::dict result;
    if (!neuraChordApi)
    {
        DBG("ERROR: Modulo neurachord_api no cargado, no se pueden obtener los presets.");
        result["error"] = "Modulo neurachord_api no cargado.";
        return result;
    }

    try
    {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("get_learned_sounds")();
    }
    catch (const py::error_already_set& e)
    {
        DBG("!!! Error de Python en getLearnedSounds(): " << e.what());
        result["error"] = "Error de Python al obtener presets.";
    }
    return result;
}

// (Añade esta función al final de PythonManager.cpp)

juce::StringArray PythonManager::getSoundArchetypes()
{
    juce::StringArray archetypes;
    if (!neuraChordApi)
    {
        DBG("ERROR: Modulo neurachord_api no cargado, no se pueden obtener los arquetipos.");
        return archetypes; // Devuelve un array vacío
    }

    try
    {
        py::gil_scoped_acquire acquire;
        py::list result = neuraChordApi.attr("get_sound_archetypes")();

        for (auto item : result)
        {
            archetypes.add(item.cast<std::string>());
        }
    }
    catch (const py::error_already_set& e)
    {
        DBG("!!! Error de Python en getSoundArchetypes(): " << e.what());
    }

    return archetypes;
}