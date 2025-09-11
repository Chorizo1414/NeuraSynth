#include "ChordMelodyTabComponent.h"

ChordMelodyTabComponent::ChordMelodyTabComponent(PythonManager& pm) : pythonManager(pm)
{
    // --- Configuración del Editor de Texto (Prompt) ---
    addAndMakeVisible(promptEditor);
    promptEditor.setMultiLine(true);
    promptEditor.setReturnKeyStartsNewLine(true);
    promptEditor.setTextToShowWhenEmpty("Escribe tu idea musical...", juce::Colours::grey);
    promptEditor.setColour(juce::TextEditor::backgroundColourId, juce::Colours::darkgrey.darker());

    // --- Añadir el Piano Roll ---
    addAndMakeVisible(pianoRollComponent);

    // --- Configuración de los Botones ---
    addAndMakeVisible(generateButton);
    addAndMakeVisible(playButton);
    addAndMakeVisible(stopButton);
    addAndMakeVisible(likeButton);
    addAndMakeVisible(dislikeButton);
    addAndMakeVisible(exportButton);

    loadButtonImages(); // Cargar las imágenes para los botones

    // --- Lógica de los Botones ---

    generateButton.onClick = [this]() {
        juce::String prompt = promptEditor.getText();
        if (prompt.isNotEmpty()) {
            pythonManager.callGenerateMusic(prompt.toStdString());

            // Cargar el MIDI generado en el Piano Roll
            juce::File midiFile = pythonManager.getMidiFilePath();
            if (midiFile.existsAsFile())
            {
                juce::FileInputStream stream(midiFile);
                juce::MidiFile midi;
                if (midi.readFrom(stream))
                {
                    // Asumimos que la pista 1 tiene las notas de la melodía
                    const auto* track = midi.getTrack(1);
                    if (track)
                        pianoRollComponent.setMidiSequence(*track);
                }
            }
        }
        };

    playButton.onClick = [this]() { pythonManager.playGeneratedMidi(); };
    stopButton.onClick = [this]() { pythonManager.stopMidiPlayback(); };

    // TODO: Implementar la lógica para estos botones
    likeButton.onClick = []() { DBG("Botón 'Me Gusta' presionado"); };
    dislikeButton.onClick = []() { DBG("Botón 'No me Gusta' presionado"); };
    exportButton.onClick = []() { DBG("Botón 'Exportar' presionado"); };
}

ChordMelodyTabComponent::~ChordMelodyTabComponent()
{
}

void ChordMelodyTabComponent::paint(juce::Graphics& g)
{
    // Fondo general
    g.fillAll(getLookAndFeel().findColour(juce::ResizableWindow::backgroundColourId).darker(0.5));
}

void ChordMelodyTabComponent::resized()
{
    auto bounds = getLocalBounds().reduced(10); // Margen general

    // 1. Área para el prompt de texto (15% superior)
    auto promptArea = bounds.removeFromTop(bounds.getHeight() * 0.20);
    promptEditor.setBounds(promptArea);

    // 2. Área para la barra de botones (50px en la parte inferior)
    auto buttonBarArea = bounds.removeFromBottom(50);

    // 3. El resto del espacio es para el Piano Roll
    pianoRollComponent.setBounds(bounds.reduced(0, 10)); // Margen vertical

    // --- Distribuir los botones en la barra inferior ---
    auto buttonWidth = buttonBarArea.getWidth() / 6;
    generateButton.setBounds(buttonBarArea.removeFromLeft(buttonWidth).reduced(5));
    playButton.setBounds(buttonBarArea.removeFromLeft(buttonWidth).reduced(5));
    stopButton.setBounds(buttonBarArea.removeFromLeft(buttonWidth).reduced(5));
    likeButton.setBounds(buttonBarArea.removeFromLeft(buttonWidth).reduced(5));
    dislikeButton.setBounds(buttonBarArea.removeFromLeft(buttonWidth).reduced(5));
    exportButton.setBounds(buttonBarArea.removeFromLeft(buttonWidth).reduced(5));
}

// Nueva función para cargar las imágenes de los botones
void ChordMelodyTabComponent::loadButtonImages()
{
    // Carga las imágenes desde los datos binarios (o desde archivos si los tienes en otro lado)
    // Asegúrate de que las rutas a las imágenes son correctas.
    // Estas rutas asumen que las imágenes están en Source/NeuraChord/sources
    // Para que esto funcione, debes añadir estas imágenes a tu proyecto en el Projucer.

    // NOTA: La forma más robusta es añadir los PNG al Projucer y cargarlos desde memoria.
    // Aquí muestro cómo cargarlos desde un archivo como ejemplo.
    // Debes tener una forma de encontrar la ruta correcta en tiempo de ejecución.

    // Esta es una forma SIMPLIFICADA. La mejor práctica es usar BinaryData.
    juce::File imageFolder = juce::File::getSpecialLocation(juce::File::currentApplicationFile)
        .getParentDirectory().getParentDirectory()
        .getChildFile("Resources/sources"); // Esto puede variar!

    auto playImg = juce::ImageFileFormat::loadFrom(imageFolder.getChildFile("reproducir.png"));
    auto stopImg = juce::ImageFileFormat::loadFrom(imageFolder.getChildFile("pausa.png"));
    auto likeImg = juce::ImageFileFormat::loadFrom(imageFolder.getChildFile("corazon.png"));
    auto dislikeImg = juce::ImageFileFormat::loadFrom(imageFolder.getChildFile("pulgar_abajo.png"));
    auto exportImg = juce::ImageFileFormat::loadFrom(imageFolder.getChildFile("nota.png"));
    // No hay un icono claro para "Generar", usaré el de "nota" también por ahora
    auto generateImg = juce::ImageFileFormat::loadFrom(imageFolder.getChildFile("nota.png"));


    playButton.setImages(true, true, true, playImg, 1.0f, {}, playImg, 0.8f, {}, playImg, 0.5f, {});
    stopButton.setImages(true, true, true, stopImg, 1.0f, {}, stopImg, 0.8f, {}, stopImg, 0.5f, {});
    likeButton.setImages(true, true, true, likeImg, 1.0f, {}, likeImg, 0.8f, {}, likeImg, 0.5f, {});
    dislikeButton.setImages(true, true, true, dislikeImg, 1.0f, {}, dislikeImg, 0.8f, {}, dislikeImg, 0.5f, {});
    exportButton.setImages(true, true, true, exportImg, 1.0f, {}, exportImg, 0.8f, {}, exportImg, 0.5f, {});
    generateButton.setImages(true, true, true, generateImg, 1.0f, {}, generateImg, 0.8f, {}, generateImg, 0.5f, {});
}