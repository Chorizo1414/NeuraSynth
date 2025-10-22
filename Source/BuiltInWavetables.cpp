#include "BuiltInWavetables.h"
#include "BinaryData.h"

#include <array>
#include <map>
#include <memory>

namespace
{
    struct ResourceWav
    {
        const char* fileName;
        const void* data;
        int dataSize;
    };

    juce::AudioBuffer<float> loadBufferFromResource(const ResourceWav& resource)
    {
        juce::AudioBuffer<float> buffer;

        juce::WavAudioFormat wavFormat;
        auto stream = std::make_unique<juce::MemoryInputStream>(resource.data, static_cast<size_t>(resource.dataSize), false);

        if (auto reader = std::unique_ptr<juce::AudioFormatReader>(wavFormat.createReaderFor(stream.release(), true)))
        {
            buffer.setSize((int)reader->numChannels, (int)reader->lengthInSamples);
            reader->read(&buffer, 0, (int)reader->lengthInSamples, 0, true, true);
        }
        else
        {
            DBG("No se pudo cargar el wavetable integrado: " << resource.fileName);
        }

        return buffer;
    }

    const std::array<ResourceWav, 27> builtInResources{ {
        { "analog_mix_destroyer_ak.wav", BinaryData::analog_mix_destroyer_ak_wav, BinaryData::analog_mix_destroyer_ak_wavSize },
        { "analog_stacked_saws_pad.wav", BinaryData::analog_stacked_saws_pad_wav, BinaryData::analog_stacked_saws_pad_wavSize },
        { "analog_substation_harmony_ak.wav", BinaryData::analog_substation_harmony_ak_wav, BinaryData::analog_substation_harmony_ak_wavSize },
        { "analog_wave_bass.wav", BinaryData::analog_wave_bass_wav, BinaryData::analog_wave_bass_wavSize },
        { "bass_mix_destroyer.wav", BinaryData::bass_mix_destroyer_wav, BinaryData::bass_mix_destroyer_wavSize },
        { "bass_sin_er.wav", BinaryData::bass_sin_er_wav, BinaryData::bass_sin_er_wavSize },
        { "bass_sine_additive_fold.wav", BinaryData::bass_sine_additive_fold_wav, BinaryData::bass_sine_additive_fold_wavSize },
        { "bass_yab.wav", BinaryData::bass_yab_wav, BinaryData::bass_yab_wavSize },
        { "bell_picking_a_string.wav", BinaryData::bell_picking_a_string_wav, BinaryData::bell_picking_a_string_wavSize },
        { "bells_and_crickets.wav", BinaryData::bells_and_crickets_wav, BinaryData::bells_and_crickets_wavSize },
        { "layered.wav", BinaryData::layered_wav, BinaryData::layered_wavSize },
        { "lead_voice.wav", BinaryData::lead_voice_wav, BinaryData::lead_voice_wavSize },
        { "marbles_bell.wav", BinaryData::marbles_bell_wav, BinaryData::marbles_bell_wavSize },
        { "pendulumphase.wav", BinaryData::pendulumphase_wav, BinaryData::pendulumphase_wavSize },
        { "pulse.wav", BinaryData::pulse_wav, BinaryData::pulse_wavSize },
        { "pwm.wav", BinaryData::pwm_wav, BinaryData::pwm_wavSize },
        { "rmi_piano.wav", BinaryData::rmi_piano_wav, BinaryData::rmi_piano_wavSize },
        { "saw.wav", BinaryData::saw_wav, BinaryData::saw_wavSize },
        { "sen.wav", BinaryData::sen_wav, BinaryData::sen_wavSize },
        { "senHarmonic.wav", BinaryData::senHarmonic_wav, BinaryData::senHarmonic_wavSize },
        { "simple_bass.wav", BinaryData::simple_bass_wav, BinaryData::simple_bass_wavSize },
        { "slope.wav", BinaryData::slope_wav, BinaryData::slope_wavSize },
        { "square.wav", BinaryData::square_wav, BinaryData::square_wavSize },
        { "squeezy_keys.wav", BinaryData::squeezy_keys_wav, BinaryData::squeezy_keys_wavSize },
        { "triangle.wav", BinaryData::triangle_wav, BinaryData::triangle_wavSize },
        { "whitenoise.wav", BinaryData::whitenoise_wav, BinaryData::whitenoise_wavSize },
        { "zionoid_pad.wav", BinaryData::zionoid_pad_wav, BinaryData::zionoid_pad_wavSize },
    } };

    const std::map<juce::String, juce::AudioBuffer<float>, std::less<>>& getBuiltInTables()
    {
        static const auto tables = []()
            {
                std::map<juce::String, juce::AudioBuffer<float>, std::less<>> map;

                for (const auto& resource : builtInResources)
                {
                    auto buffer = loadBufferFromResource(resource);
                    if (buffer.getNumSamples() > 0)
                    {
                        map.emplace(resource.fileName, std::move(buffer));
                    }
                    else
                    {
                        DBG("Se omitio un wavetable integrado por no poder leerse: " << resource.fileName);
                    }
                }

                return map;
            }();

        return tables;
    }

    const juce::StringArray& getBuiltInNames()
    {
        static const juce::StringArray names = []
            {
                juce::StringArray arr;
                for (const auto& entry : getBuiltInTables())
                    arr.add(entry.first);
                return arr;
            }();

        return names;
    }
}

namespace BuiltInWavetables
{
    const juce::StringArray& getAllNames()
    {
        return getBuiltInNames();
    }

    const juce::AudioBuffer<float>* getWavetable(const juce::String& name)
    {
        const auto& tables = getBuiltInTables();
        if (auto it = tables.find(name); it != tables.end())
            return &it->second;
        return nullptr;
    }

    bool isAvailable(const juce::String& name)
    {
        const auto& tables = getBuiltInTables();
        return tables.find(name) != tables.end();
    }
}