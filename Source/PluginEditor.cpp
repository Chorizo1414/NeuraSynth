#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "LayoutConstants.h"

#include <array>

// Opciones de escala disponibles (id, etiqueta, ancho base)
// El alto se calcula dinámicamente a partir de LayoutConstants y la altura del TabBar.
const std::array<NeuraSynthAudioProcessorEditor::ScaleOption, 3>
NeuraSynthAudioProcessorEditor::scaleOptions{ {
    { 1, "75%",  1440 },
    { 2, "100%", 1920 },
    { 3, "125%", 2340 },
} };

NeuraSynthAudioProcessorEditor::NeuraSynthAudioProcessorEditor(NeuraSynthAudioProcessor& p)
    : AudioProcessorEditor(&p)
    , audioProcessor(p)
    , tabbedComponent(juce::TabbedButtonBar::Orientation::TabsAtTop)
    , synthTab(p)
    , chordMelodyTab(p)
{
    // Apariencia y pestañas
    tabbedComponent.setLookAndFeel(&customLookAndFeel);
    addAndMakeVisible(tabbedComponent);

    tabbedComponent.addTab("Synthesizer", juce::Colours::transparentBlack, &synthTab, false);
    tabbedComponent.addTab("Chord/Melody Generator", juce::Colours::transparentBlack, &chordMelodyTab, false);

    // Controles de tamaño (label + combo)
    addAndMakeVisible(sizeLabel);
    sizeLabel.setText("Size:", juce::dontSendNotification);
    sizeLabel.setJustificationType(juce::Justification::centredRight);
    sizeLabel.setColour(juce::Label::textColourId, juce::Colours::lightgrey);

    addAndMakeVisible(sizeComboBox);
    for (const auto& option : scaleOptions)
        sizeComboBox.addItem(option.label, option.id);

    sizeComboBox.setTooltip("Escala la interfaz del sintetizador");
    sizeComboBox.setJustificationType(juce::Justification::centred);

    // Restricciones (se ajustan en refreshParentConstraints)
    constrainer = std::make_unique<juce::ComponentBoundsConstrainer>();
    setConstrainer(constrainer.get());
    setResizable(true, false);

    // Reacciona al cambio en el combo aplicando la opción seleccionada
    sizeComboBox.onChange = [this]
        {
            applyScaleOption(sizeComboBox.getSelectedId(), false);
        };

    // Inicializa tamaño/escala según lo almacenado en el processor
    initialiseEditorSizeFromProcessor();
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
    tabbedComponent.setLookAndFeel(nullptr);
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);
}

void NeuraSynthAudioProcessorEditor::resized()
{
    // Si hay un tamaño guardado/esperado para la opción actual, mantenlo consistente
    if (!isApplyingStoredSize && currentScaleOption.id != 0)
    {
        auto targetBounds = calculateEditorBoundsForOption(currentScaleOption);
        if (targetBounds.getWidth() != getWidth() || targetBounds.getHeight() != getHeight())
        {
            applyScaleOption(currentScaleOption.id, true);
            return;
        }
    }

    // El TabbedComponent ocupa TODA la ventana.
    tabbedComponent.setBounds(getLocalBounds());

    // Posiciona los controles de tamaño manualmente sobre la barra de pestañas.
    const int tabBarHeight = 35;
    const int sizeControlsWidth = 130;
    auto topArea = getLocalBounds();
    auto sizeControlsArea = topArea.removeFromTop(tabBarHeight).removeFromRight(sizeControlsWidth);

    sizeControlsArea.reduce(8, 4);
    sizeLabel.setBounds(sizeControlsArea.removeFromLeft(45));
    sizeComboBox.setBounds(sizeControlsArea);

    sizeLabel.toFront(false);
    sizeComboBox.toFront(false);
}

// Se llama si cambia la jerarquía de padres (útil para VST/AU hosts)
void NeuraSynthAudioProcessorEditor::parentHierarchyChanged()
{
    juce::AudioProcessorEditor::parentHierarchyChanged();

    if (currentScaleOption.id != 0)
        refreshParentConstraints(calculateEditorBoundsForOption(currentScaleOption));
}

// Se llama si cambia el factor global de escala del sistema
void NeuraSynthAudioProcessorEditor::globalScaleFactorChanged()
{
    juce::AudioProcessorEditor::globalScaleFactorChanged();

    if (currentScaleOption.id != 0)
        applyScaleOption(currentScaleOption.id, true);
}

// Lee del processor la última escala/tamaño y lo aplica
void NeuraSynthAudioProcessorEditor::initialiseEditorSizeFromProcessor()
{
    int storedId = audioProcessor.getStoredEditorScaleId();
    if (findScaleOptionById(storedId) == nullptr)
        storedId = scaleOptions[1].id; // por defecto 100%

    sizeComboBox.setSelectedId(storedId, juce::dontSendNotification);

    auto storedBounds = audioProcessor.getStoredEditorBounds();
    if (storedBounds.getWidth() > 0 && storedBounds.getHeight() > 0)
    {
        const auto expectedBounds = calculateEditorBoundsForOption(*findScaleOptionById(storedId));
        if (storedBounds.getWidth() != expectedBounds.getWidth()
            || storedBounds.getHeight() != expectedBounds.getHeight())
        {
            storedBounds = expectedBounds;
        }

        const juce::ScopedValueSetter<bool> guard(isApplyingStoredSize, true);
        setSize(storedBounds.getWidth(), storedBounds.getHeight());
        refreshParentConstraints(storedBounds);
        currentScaleOption = *findScaleOptionById(storedId);
    }

    applyScaleOption(storedId, false);
}

// Busca una opción por id
const NeuraSynthAudioProcessorEditor::ScaleOption*
NeuraSynthAudioProcessorEditor::findScaleOptionById(int optionId) const
{
    for (const auto& option : scaleOptions)
        if (option.id == optionId)
            return &option;

    return nullptr;
}

// Calcula los bounds completos del editor (ancho deseado + alto contenido + tab bar)
juce::Rectangle<int>
NeuraSynthAudioProcessorEditor::calculateEditorBoundsForOption(const ScaleOption& option) const
{
    int tabDepth = tabbedComponent.getTabBarDepth();
    if (tabDepth <= 0)
        tabDepth = 35;

    const double scale = static_cast<double>(option.width)
        / static_cast<double>(LayoutConstants::DESIGN_WIDTH);

    const int contentHeight = juce::roundToInt(
        scale * (LayoutConstants::DESIGN_SYNTH_HEIGHT + LayoutConstants::KEYBOARD_HEIGHT));

    const int totalHeight = contentHeight + tabDepth;

    return { 0, 0, option.width, totalHeight };
}

// Ajusta límites/relación de aspecto del padre (plugin window o standalone)
void NeuraSynthAudioProcessorEditor::refreshParentConstraints(const juce::Rectangle<int>& targetBounds)
{
    if (constrainer != nullptr)
    {
        constrainer->setSizeLimits(targetBounds.getWidth(), targetBounds.getHeight(),
            targetBounds.getWidth(), targetBounds.getHeight());
        constrainer->setFixedAspectRatio(
            static_cast<double>(targetBounds.getWidth()) / static_cast<double>(targetBounds.getHeight()));
    }

    if (auto* parent = getTopLevelComponent())
    {
        if (parent != this)
        {
            if (auto* window = dynamic_cast<juce::ResizableWindow*>(parent))
            {
                window->setResizeLimits(targetBounds.getWidth(), targetBounds.getHeight(),
                    targetBounds.getWidth(), targetBounds.getHeight());
                window->setResizable(true, false);
                window->setConstrainer(constrainer.get());

                if (window->getWidth() != targetBounds.getWidth()
                    || window->getHeight() != targetBounds.getHeight())
                {
                    window->setSize(targetBounds.getWidth(), targetBounds.getHeight());
                }
            }
            else
            {
                parent->setSize(targetBounds.getWidth(), targetBounds.getHeight());
            }
        }
    }
}

// Aplica una opción de escala, actualiza combo (si procede), persiste en el processor y refresca límites
void NeuraSynthAudioProcessorEditor::applyScaleOption(int optionId, bool updateComboBoxSelection)
{
    const auto* chosen = findScaleOptionById(optionId);
    if (chosen == nullptr)
        chosen = &scaleOptions[1]; // 100% por defecto

    currentScaleOption = *chosen;

    auto targetBounds = calculateEditorBoundsForOption(*chosen);

    if (updateComboBoxSelection && sizeComboBox.getSelectedId() != chosen->id)
        sizeComboBox.setSelectedId(chosen->id, juce::dontSendNotification);

    // Evita bucles de resized
    const juce::ScopedValueSetter<bool> guard(isApplyingStoredSize, true);

    if (getWidth() != targetBounds.getWidth() || getHeight() != targetBounds.getHeight())
        setSize(targetBounds.getWidth(), targetBounds.getHeight());

    // Recalcular tras setSize por si cambia el tabDepth
    auto adjustedBounds = calculateEditorBoundsForOption(*chosen);
    if (adjustedBounds.getWidth() != targetBounds.getWidth()
        || adjustedBounds.getHeight() != targetBounds.getHeight())
    {
        targetBounds = adjustedBounds;
        if (getWidth() != targetBounds.getWidth() || getHeight() != targetBounds.getHeight())
            setSize(targetBounds.getWidth(), targetBounds.getHeight());
    }

    refreshParentConstraints(targetBounds);

    // Persistir
    audioProcessor.setStoredEditorScaleId(chosen->id);
    audioProcessor.setStoredEditorBounds(targetBounds);
}
