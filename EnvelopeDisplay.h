#pragma once
#include <JuceHeader.h>

class EnvelopeDisplay : public juce::Component
{
public:
    EnvelopeDisplay() {}
    ~EnvelopeDisplay() override {}

    void setADSR(float attackSecs, float decaySecs, float sustainLevel, float releaseSecs)
    {
        attack = attackSecs;
        decay = decaySecs;
        sustain = sustainLevel;
        release = releaseSecs;
        recalcEnvelopePath();
    }

    void paint(juce::Graphics& g) override
    {
        g.fillAll(juce::Colours::black);
        g.setColour(juce::Colours::white);
        g.strokePath(envelopePath, juce::PathStrokeType(2.0f));
    }

    void resized() override
    {
        recalcEnvelopePath();
    }

private:
    float attack = 0.1f;
    float decay = 0.1f;
    float sustain = 0.7f;
    float release = 0.2f;

    juce::Path envelopePath;

    void recalcEnvelopePath()
    {
        envelopePath.clear();
        if (getWidth() <= 0 || getHeight() <= 0)
        {
            repaint();
            return;
        }

        float sustainTime = 0.5f;
        float totalTime = attack + decay + release + sustainTime;
        if (totalTime < 1.0e-9f)
            totalTime = 1.0f;

        auto timeToX = [this, totalTime](float t) {
            return juce::jmap<float>(t, 0.0f, totalTime, 0.0f, (float)getWidth());
            };

        auto ampToY = [this](float amp) {
            return (float)getHeight() * (1.0f - amp);
            };

        envelopePath.startNewSubPath(timeToX(0.0f), ampToY(0.0f));
        float endAttackTime = attack;
        envelopePath.lineTo(timeToX(endAttackTime), ampToY(1.0f));
        float endDecayTime = attack + decay;
        envelopePath.lineTo(timeToX(endDecayTime), ampToY(sustain));
        float endSustainTime = endDecayTime + sustainTime;
        envelopePath.lineTo(timeToX(endSustainTime), ampToY(sustain));
        float endReleaseTime = endDecayTime + sustainTime + release;
        envelopePath.lineTo(timeToX(endReleaseTime), ampToY(0.0f));

        repaint();
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(EnvelopeDisplay)
};