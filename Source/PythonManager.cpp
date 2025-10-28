#include "PythonManager.h"
#include <mutex>
#include <vector>
#include <cstdlib> // Required for _putenv_s / setenv

// Anonymous namespace for helper functions and variables
namespace
{
    std::mutex pythonInitMutex;
    bool pythonInterpreterReady = false;

    using FileList = std::vector<juce::File>;

    // Appends a file to the list if it's unique and valid
    void appendIfUnique(FileList& files, const juce::File& candidate)
    {
        if (candidate == juce::File()) return;
        const auto path = candidate.getFullPathName();
        if (path.isEmpty()) return;
        for (const auto& existing : files)
            if (existing.getFullPathName() == path) return;
        files.push_back(candidate);
    }

    // Checks if a directory contains Python runtime markers (DLLs, zip, exe)
    bool hasRuntimeLibraryIn(const juce::File& candidate)
    {
        if (!candidate.isDirectory()) return false;
        static const char* pythonDlls[] = { "python38.dll", "python39.dll", "python310.dll", "python311.dll" };
        for (auto* dll : pythonDlls)
            if (candidate.getChildFile(dll).existsAsFile()) return true;
        if (candidate.getChildFile("python3.dll").existsAsFile()) return true;
        if (candidate.getChildFile("python.exe").existsAsFile() || candidate.getChildFile("pythonw.exe").existsAsFile()) return true;
        juce::Array<juce::File> pythonZips;
        candidate.findChildFiles(pythonZips, juce::File::findFiles, false, "python3*.zip");
        return !pythonZips.isEmpty();
    }

    // Gets the OS-specific path list separator (';' for Windows, ':' otherwise)
    juce::String getPathListSeparator()
    {
#if JUCE_WINDOWS
        return ";";
#else
        return ":";
#endif
    }

    // Sets an environment variable
    void setEnvironmentVariable(const juce::String& name, const juce::String& value)
    {
#if JUCE_WINDOWS
        _putenv_s(name.toRawUTF8(), value.toRawUTF8());
#else
        ::setenv(name.toRawUTF8(), value.toRawUTF8(), 1); // Use ::setenv for POSIX
#endif
    }

#if JUCE_WINDOWS
    // Adds a directory to the system PATH if not already present (Windows specific)
    void prependToPathIfNecessary(const juce::File& directory)
    {
        if (!directory.isDirectory()) return;
        const auto candidate = directory.getFullPathName();
        if (candidate.isEmpty()) return;
        const juce::String existingPath = juce::SystemStats::getEnvironmentVariable("PATH", {});
        juce::StringArray entries;
        entries.addTokens(existingPath, getPathListSeparator(), "\"");
        entries.trim();
        entries.removeEmptyStrings();
        for (const auto& entry : entries)
            if (entry == candidate) return;
        const juce::String newPath = existingPath.isEmpty() ? candidate : candidate + getPathListSeparator() + existingPath;
        setEnvironmentVariable("PATH", newPath);
    }

    // Exposes the Python runtime and its DLLs on the system PATH (Windows specific)
    void exposePythonRuntimeOnPath(const juce::File& pythonHome)
    {
        if (!pythonHome.isDirectory()) return;
        FileList candidates;
        auto addCandidate = [&candidates](const juce::File& directory) { appendIfUnique(candidates, directory); };
        addCandidate(pythonHome);
        addCandidate(pythonHome.getChildFile("DLLs"));
        const auto parent = pythonHome.getParentDirectory();
        if (hasRuntimeLibraryIn(parent)) addCandidate(parent);
        const auto binDir = pythonHome.getChildFile("bin");
        if (hasRuntimeLibraryIn(binDir)) addCandidate(binDir);
        for (const auto& candidate : candidates)
            prependToPathIfNecessary(candidate);
    }
#endif

} // End anonymous namespace

PythonManager::PythonManager()
{
    try {
        std::scoped_lock<std::mutex> lock(pythonInitMutex);
        runtimeAvailable.store(false);

        // --- FORCED PATH CONFIGURATION ---
        const juce::File pythonHome("C:\\ProgramData\\NeuraSynth\\Python");
        const bool hasEmbeddedRuntime = pythonHome.isDirectory();
        if (hasEmbeddedRuntime)
            DBG("PythonManager: Using fixed PYTHONHOME path: " << pythonHome.getFullPathName());
        else
            DBG("!!! PYTHON MANAGER ERROR: Fixed path C:\\ProgramData\\NeuraSynth\\Python not found. Check installation.");

        const juce::File neuraChordRoot = pythonHome.getChildFile("NeuraChord");
        // --- END FORCED PATH ---

        juce::StringArray pythonPathEntries;
        auto addPathEntry = [&pythonPathEntries](const juce::String& path) {
            if (path.isNotEmpty()) pythonPathEntries.addIfNotAlreadyThere(path);
            };

        if (hasEmbeddedRuntime)
        {
            addPathEntry(pythonHome.getFullPathName());

            const juce::File libDir = pythonHome.getChildFile("Lib");
            if (libDir.isDirectory())
            {
                addPathEntry(libDir.getFullPathName());
                const juce::File sitePackages = libDir.getChildFile("site-packages");
                if (sitePackages.isDirectory()) addPathEntry(sitePackages.getFullPathName());
                const juce::File encodingsDir = libDir.getChildFile("encodings");
                if (encodingsDir.isDirectory()) addPathEntry(encodingsDir.getFullPathName());
            }

            const juce::File lowerLibDir = pythonHome.getChildFile("lib");
            if (lowerLibDir.isDirectory())
            {
                addPathEntry(lowerLibDir.getFullPathName());
                const juce::File sitePackages = lowerLibDir.getChildFile("site-packages");
                if (sitePackages.isDirectory()) addPathEntry(sitePackages.getFullPathName());
                const juce::File encodingsDir = lowerLibDir.getChildFile("encodings");
                if (encodingsDir.isDirectory()) addPathEntry(encodingsDir.getFullPathName());
            }

            auto addPythonZip = [&addPathEntry](const juce::File& directory, const juce::String& pattern) {
                juce::Array<juce::File> matches;
                directory.findChildFiles(matches, juce::File::findFiles, false, pattern);
                for (const auto& match : matches) addPathEntry(match.getFullPathName());
                };
            addPythonZip(pythonHome, "python*.zip");
            if (pythonHome.getChildFile("Lib").isDirectory()) addPythonZip(pythonHome.getChildFile("Lib"), "python*.zip");
            if (pythonHome.getChildFile("lib").isDirectory()) addPythonZip(pythonHome.getChildFile("lib"), "python*.zip");
        }

        if (neuraChordRoot.isDirectory())
            addPathEntry(neuraChordRoot.getFullPathName());
        else
            DBG("!!! PYTHON MANAGER WARNING: NeuraChord script directory not found at " << neuraChordRoot.getFullPathName());


#if JUCE_WINDOWS
        if (hasEmbeddedRuntime)
            exposePythonRuntimeOnPath(pythonHome);
#endif

        const juce::String existingPythonPath = juce::SystemStats::getEnvironmentVariable("PYTHONPATH", {});
        if (existingPythonPath.isNotEmpty())
        {
            juce::StringArray existingEntries;
            existingEntries.addTokens(existingPythonPath, getPathListSeparator(), "\"");
            existingEntries.trim();
            existingEntries.removeEmptyStrings();
            for (const auto& entry : existingEntries) addPathEntry(entry);
        }

        if (hasEmbeddedRuntime)
            setEnvironmentVariable("PYTHONHOME", pythonHome.getFullPathName());
        else
            DBG("!!! PYTHON MANAGER WARNING: PYTHONHOME not set as embedded runtime wasn't found at the fixed path.");


        if (hasEmbeddedRuntime && !pythonPathEntries.isEmpty())
        {
            const juce::String combinedPythonPath = pythonPathEntries.joinIntoString(getPathListSeparator());
            setEnvironmentVariable("PYTHONPATH", combinedPythonPath);
        }
        else if (!hasEmbeddedRuntime)
        {
            DBG("!!! PYTHON MANAGER WARNING: PYTHONPATH not explicitly set as embedded runtime wasn't found.");
        }


        // Initialize interpreter only once
        if (!pythonInterpreterReady)
        {
            if (!hasEmbeddedRuntime)
            {
                DBG("!!! PYTHON MANAGER WARNING: Attempting to initialize Python interpreter without finding embedded runtime. This might fail or use a system Python.");
            }
            py::initialize_interpreter();
            pythonInterpreterReady = true;
        }

        py::gil_scoped_acquire acquire;
        auto sys = py::module::import("sys");
        py::list sysPath = sys.attr("path");

        // Ensure Python's sys.path includes our needed directories
        for (const auto& entry : pythonPathEntries)
        {
            bool alreadyPresent = false;
            for (auto item : sysPath) {
                if (item.cast<std::string>() == entry.toStdString()) {
                    alreadyPresent = true;
                    break;
                }
            }
            if (!alreadyPresent) sysPath.attr("append")(entry.toStdString());
        }

        neuraChordApi = py::module::import("neurachord_api");
        runtimeAvailable.store(true);
        DBG("PythonManager: Interpreter initialized and neurachord_api imported successfully!");

    }
    catch (const py::error_already_set& e) {
        DBG("!!! PYTHON MANAGER PYBIND ERROR during initialization: " << e.what());
        if (PyErr_Occurred()) {
            py::gil_scoped_acquire acquire; // Need GIL to handle Python errors
            PyErr_Print(); // Print Python traceback to stderr
            PyErr_Clear(); // Clear the error state
        }
        runtimeAvailable.store(false);
    }
    catch (const std::exception& e) {
        DBG("!!! PYTHON MANAGER C++ ERROR during initialization: " << e.what());
        runtimeAvailable.store(false);
    }
}


PythonManager::~PythonManager()
{
    std::scoped_lock<std::mutex> lock(pythonInitMutex);
    if (!pythonInterpreterReady) return;

    try {
        py::gil_scoped_acquire acquire;
        neuraChordApi = py::module(); // Release module reference
    }
    catch (const std::exception& e) {
        DBG("PythonManager::~PythonManager - error releasing module: " << e.what());
    }

    runtimeAvailable.store(false);
    // As noted before, py::finalize_interpreter() is generally avoided in plugins.
}

py::dict PythonManager::generateMusicData(const juce::String& prompt, int numChords)
{
    py::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        DBG("PythonManager::generateMusicData ERROR: Python runtime not available.");
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_progresion")(prompt.toStdString(), numChords);
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::generateMusicData Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

py::dict PythonManager::generateMusicData(const juce::String& prompt, int numChords, const py::list& melody, int bpm)
{
    py::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        DBG("PythonManager::generateMusicData(melody) ERROR: Python runtime not available.");
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_progresion")(prompt.toStdString(), numChords, melody, bpm);
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::generateMusicData(melody) Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

py::dict PythonManager::generateMelodyData(const py::list& chords, const py::list& rhythm, const juce::String& root, const juce::String& mode, int bpm)
{
    py::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        DBG("PythonManager::generateMelodyData ERROR: Python runtime not available.");
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_melodia")(chords, rhythm, root.toStdString(), mode.toStdString(), bpm);
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::generateMelodyData Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

py::dict PythonManager::generateMelodyFromPrompt(const juce::String& prompt, int numChords, int bpm)
{
    py::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        DBG("PythonManager::generateMelodyFromPrompt ERROR: Python runtime not available.");
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_melodia_desde_prompt")(prompt.toStdString(), numChords, bpm);
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::generateMelodyFromPrompt Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

juce::StringArray PythonManager::getAvailableGenres()
{
    juce::StringArray genres;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        DBG("PythonManager::getAvailableGenres ERROR: Python runtime not available.");
        return genres;
    }
    try {
        py::gil_scoped_acquire acquire;
        py::list pyGenres = neuraChordApi.attr("get_available_genres")();
        for (auto item : pyGenres) genres.add(item.cast<std::string>());
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::getAvailableGenres Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return genres;
}

juce::String PythonManager::exportChords(const py::dict& musicData, int bpm)
{
    if (!runtimeAvailable.load() || !neuraChordApi) return "Error: Python runtime not available.";
    if (!musicData.contains("acordes")) return "Error: No chord data provided.";

    try {
        py::gil_scoped_acquire acquire;
        lastExportedChordsFile = juce::File();
        py::object detalles = musicData.contains("acordes_detallados") ? py::reinterpret_borrow<py::object>(musicData["acordes_detallados"]) : py::none();
        py::object tiempos = musicData.contains("acordes_tiempos") ? py::reinterpret_borrow<py::object>(musicData["acordes_tiempos"]) : py::none();
        py::object resultObj = neuraChordApi.attr("exportar_acordes_midi")(musicData["acordes"], musicData["ritmo"], bpm, detalles, tiempos);

        if (resultObj.is_none() || !py::isinstance<py::dict>(resultObj)) return "Python export error: Invalid response.";
        py::dict result = resultObj.cast<py::dict>();
        if (result.contains("error") && !result["error"].cast<std::string>().empty()) return "Python Error: " + juce::String(result["error"].cast<std::string>());

        auto ruta = result.contains("ruta") ? result["ruta"].cast<std::string>() : std::string();
        if (!ruta.empty()) lastExportedChordsFile = juce::File(ruta);
        return ruta.empty() ? "Chords exported." : "Chords exported to: " + juce::String(ruta);

    }
    catch (const py::error_already_set& e) {
        lastExportedChordsFile = juce::File();
        DBG("PythonManager::exportChords Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
        return juce::String("Python export error: ") + e.what();
    }
}

juce::String PythonManager::exportMelody(const py::dict& musicData, int bpm)
{
    if (!runtimeAvailable.load() || !neuraChordApi) return "Error: Python runtime not available.";
    if (!musicData.contains("melodia")) return "Error: No melody data provided.";

    try {
        py::gil_scoped_acquire acquire;
        lastExportedMelodyFile = juce::File();
        py::object resultObj = neuraChordApi.attr("exportar_melodia_midi")(musicData["melodia"], bpm);

        if (resultObj.is_none() || !py::isinstance<py::dict>(resultObj)) return "Python export error: Invalid response.";
        py::dict result = resultObj.cast<py::dict>();
        if (result.contains("error") && !result["error"].cast<std::string>().empty()) return "Python Error: " + juce::String(result["error"].cast<std::string>());

        auto ruta = result.contains("ruta") ? result["ruta"].cast<std::string>() : std::string();
        if (!ruta.empty()) lastExportedMelodyFile = juce::File(ruta);
        return ruta.empty() ? "Melody exported." : "Melody exported to: " + juce::String(ruta);

    }
    catch (const py::error_already_set& e) {
        lastExportedMelodyFile = juce::File();
        DBG("PythonManager::exportMelody Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
        return juce::String("Python export error: ") + e.what();
    }
}

juce::File PythonManager::getLastExportedChordsFile() const { return lastExportedChordsFile; }
juce::File PythonManager::getLastExportedMelodyFile() const { return lastExportedMelodyFile; }

py::dict PythonManager::transposeMusic(const py::dict& musicData, int semitones)
{
    py::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("transponer_musica")(musicData, semitones);
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::transposeMusic Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

void PythonManager::like()
{
    if (!runtimeAvailable.load() || !neuraChordApi) return;
    try {
        py::gil_scoped_acquire acquire;
        neuraChordApi.attr("puntuar_positivamente")();
        DBG("PythonManager: 'Like' action sent.");
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::like Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
}

void PythonManager::dislike()
{
    if (!runtimeAvailable.load() || !neuraChordApi) return;
    try {
        py::gil_scoped_acquire acquire;
        neuraChordApi.attr("puntuar_negativamente")();
        DBG("PythonManager: 'Dislike' action sent.");
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::dislike Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
}

void PythonManager::updateEditedMusic(const py::dict& musicData)
{
    if (!runtimeAvailable.load() || !neuraChordApi) return;
    try {
        py::gil_scoped_acquire acquire;
        neuraChordApi.attr("actualizar_progresion_editada")(musicData);
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::updateEditedMusic Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
}

py::dict PythonManager::generateSynthSound(const juce::String& prompt)
{
    py::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("generar_sonido")(prompt.toStdString());
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::generateSynthSound Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

bool PythonManager::likeLastSound()
{
    if (!runtimeAvailable.load() || !neuraChordApi) return false;
    try {
        py::gil_scoped_acquire acquire;
        py::dict result = neuraChordApi.attr("like_last_sound")();
        if (result.contains("status") && result["status"].cast<std::string>() == "ok") {
            DBG("PythonManager: 'Like Sound' action sent successfully.");
            return true;
        }
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::likeLastSound Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return false;
}

pybind11::dict PythonManager::getLearnedSounds()
{
    pybind11::dict result;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        result["error"] = "Python runtime not available.";
        return result;
    }
    try {
        py::gil_scoped_acquire acquire;
        result = neuraChordApi.attr("get_learned_sounds")();
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::getLearnedSounds Python Error: " << e.what());
        result["error"] = juce::String("Python Error: ") + e.what();
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return result;
}

juce::StringArray PythonManager::getSoundArchetypes()
{
    juce::StringArray archetypes;
    if (!runtimeAvailable.load() || !neuraChordApi) {
        DBG("PythonManager::getSoundArchetypes ERROR: Python runtime not available.");
        return archetypes;
    }
    try {
        py::gil_scoped_acquire acquire;
        py::list result = neuraChordApi.attr("get_sound_archetypes")();
        for (auto item : result) archetypes.add(item.cast<std::string>());
    }
    catch (const py::error_already_set& e) {
        DBG("PythonManager::getSoundArchetypes Python Error: " << e.what());
        if (PyErr_Occurred()) { PyErr_Print(); PyErr_Clear(); }
    }
    return archetypes;
}