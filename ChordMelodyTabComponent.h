#include <JuceHeader.h>

//==============================================================================
/*
*/
class ChordMelodyTabComponent : public juce::Component
{
public:
	ChordMelodyTabComponent();
	~ChordMelodyTabComponent() override;
	
	void paint(juce::Graphics&) override;
	void resized() override;
	
private:
	JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ChordMelodyTabComponent)
};