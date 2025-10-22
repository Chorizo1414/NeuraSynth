#pragma once

#include <JuceHeader.h>

namespace BuiltInWavetables
{
    /** Returns the list of wavetable names (with the file extension) that are available as built-in resources. */
    const juce::StringArray& getAllNames();

    /** Returns a pointer to the audio buffer for the given wavetable name (including the .wav extension).
        The buffer matches the embedded .wav resource (channel count, length and frame layout).
        Returns nullptr if the wavetable is unknown. */
    const juce::AudioBuffer<float>* getWavetable(const juce::String& name);

    /** Convenience helper that returns true if the requested wavetable exists in the built-in table. */
    bool isAvailable(const juce::String& name);
}