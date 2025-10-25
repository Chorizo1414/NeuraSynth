#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "LayoutConstants.h"
#include "BinaryData.h"

#include <array>

// Opciones de escala disponibles (id, etiqueta, ancho base)
// El alto se calcula dinámicamente a partir de LayoutConstants y la altura del TabBar.
const std::array<NeuraSynthAudioProcessorEditor::ScaleOption, 3>
NeuraSynthAudioProcessorEditor::scaleOptions{ {
    { 1, "75%",  900 },
    { 2, "100%", 1000 },
    { 3, "125%", 1200 },
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

    applyStandaloneWindowBranding();
}

NeuraSynthAudioProcessorEditor::~NeuraSynthAudioProcessorEditor()
{
    tabbedComponent.setLookAndFeel(nullptr);
}

void NeuraSynthAudioProcessorEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colours::black);

    if (audioProcessor.isStandaloneApp())
        paintStandaloneBranding(g);
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

    applyStandaloneWindowBranding();
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

    const int bottomMargin = audioProcessor.isStandaloneApp()
        ? LayoutConstants::KEYBOARD_BOTTOM_MARGIN
        : 0;

    const int contentHeight = juce::roundToInt(
        scale * (LayoutConstants::DESIGN_SYNTH_HEIGHT
            + LayoutConstants::KEYBOARD_HEIGHT
            + bottomMargin));

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
                window->setResizable(true, false);
                window->setConstrainer(constrainer.get());

                if (auto* windowConstrainer = window->getConstrainer())
                {
                    windowConstrainer->setSizeLimits(targetBounds.getWidth(), targetBounds.getHeight(), targetBounds.getWidth(), targetBounds.getHeight());
                    windowConstrainer->setFixedAspectRatio(static_cast<double>(targetBounds.getWidth()) / static_cast<double>(targetBounds.getHeight()));
                }
                else
                {
                    window->setResizeLimits(targetBounds.getWidth(), targetBounds.getHeight(), targetBounds.getWidth(), targetBounds.getHeight());
                }

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

void NeuraSynthAudioProcessorEditor::paintStandaloneBranding(juce::Graphics& g)
{
    auto bounds = getLocalBounds().toFloat();
    const float headerHeight = juce::jlimit(80.0f, 200.0f, bounds.getHeight() * 0.22f);
    auto headerArea = bounds.removeFromTop(headerHeight);

    juce::ColourGradient gradient(
        juce::Colour::fromRGB(12, 17, 27), headerArea.getTopLeft(),
        juce::Colour::fromRGB(5, 8, 14), headerArea.getBottomLeft(), false);
    gradient.addColour(0.4, juce::Colour::fromRGB(16, 26, 41));
    gradient.addColour(0.85, juce::Colour::fromRGB(8, 13, 23));

    g.setGradientFill(gradient);
    g.fillRect(headerArea);

    auto accentLine = headerArea.withHeight(1.0f).withY(headerArea.getBottom() - 1.0f);
    g.setColour(juce::Colour::fromFloatRGBA(1.0f, 1.0f, 1.0f, 0.08f));
    g.fillRect(accentLine);

    auto innerArea = headerArea.reduced(headerArea.getWidth() * 0.08f, headerArea.getHeight() * 0.28f);

    const float middleWidth = juce::jlimit(80.0f, 180.0f, innerArea.getWidth() * 0.18f);
    const float sideWidth = (innerArea.getWidth() - middleWidth) * 0.5f;

    auto leftArea = innerArea.removeFromLeft(sideWidth);
    auto middleArea = innerArea.removeFromLeft(middleWidth);
    auto rightArea = innerArea;

    juce::Font logoFont(juce::Font::getDefaultSansSerifFontName(), headerHeight * 0.42f, juce::Font::bold);
    logoFont.setExtraKerningFactor(0.15f);

    g.setColour(juce::Colours::white);
    g.setFont(logoFont);
    g.drawText("NEURA", leftArea, juce::Justification::centredRight);
    g.drawText("SYNTH", rightArea, juce::Justification::centredLeft);

    auto pulseArea = middleArea.reduced(middleArea.getWidth() * 0.08f, middleArea.getHeight() * 0.15f);
    drawStandaloneHeartbeat(g, pulseArea);
}

void NeuraSynthAudioProcessorEditor::applyStandaloneWindowBranding()
{
    if (!audioProcessor.isStandaloneApp())
        return;

    auto iconImage = juce::ImageCache::getFromMemory(BinaryData::app_icon_png, BinaryData::app_icon_pngSize);
    if (!iconImage.isValid())
        return;

    if (auto* window = dynamic_cast<juce::TopLevelWindow*>(getTopLevelComponent()))
    {
        if (auto* peer = window->getPeer())
            peer->setIcon(iconImage);
    }
}

void NeuraSynthAudioProcessorEditor::drawStandaloneHeartbeat(juce::Graphics& g, juce::Rectangle<float> area) const
{
    juce::Path heartbeat;
    const auto baseX = area.getX();
    const auto baseY = area.getY();
    const auto width = area.getWidth();
    const auto height = area.getHeight();
    const auto midY = baseY + height * 0.5f;

    heartbeat.startNewSubPath(baseX, midY);
    heartbeat.lineTo(baseX + 0.18f * width, midY);
    heartbeat.lineTo(baseX + 0.30f * width, baseY + 0.75f * height);
    heartbeat.lineTo(baseX + 0.45f * width, baseY + 0.25f * height);
    heartbeat.lineTo(baseX + 0.60f * width, baseY + 0.70f * height);
    heartbeat.lineTo(baseX + 0.72f * width, baseY + 0.10f * height);
    heartbeat.lineTo(baseX + 0.85f * width, midY);
    heartbeat.lineTo(baseX + width, midY);

    auto accent = juce::Colour::fromRGB(108, 229, 255);
    juce::DropShadow shadow(accent.darker(0.7f), juce::roundToInt(height * 0.08f), { 0, juce::roundToInt(height * 0.05f) });
    shadow.drawForPath(g, heartbeat);

    g.setColour(accent);
    g.strokePath(heartbeat, juce::PathStrokeType(juce::jmax(2.0f, height * 0.12f), juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
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
