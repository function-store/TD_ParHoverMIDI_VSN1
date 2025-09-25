'''Info Header Start
Name : constants
Author : root
Saveorigin : HoveredMidiRelative.179.toe
Saveversion : 2023.12120
Info Header End'''
from enum import Enum

# Constants
class MidiConstants:
	MIDI_MAX_VALUE = 127
	MIDI_MIN_VALUE = 0
	MIDI_CENTER_VALUE = 64  # 128/2
	NOTE_ON = 'Note On'
	NOTE_OFF = 'Note Off'
	CONTROL_CHANGE = 'Control Change'
	MAX_VELOCITY = 127
	MIDI_FEEDBACK_OFFSET = 80

class VSN1Constants:
	# VSN1 Hardware mappings
	STEP_BUTTONS = {42: 0.001, 43: 0.01, 44: 0.1, 45: 1}
	SLOT_INDICES = [33, 34, 35, 36, 37, 38, 39, 40]
	KNOB_INDEX = 41
	RESET_INDEX = 41
	PULSE_INDEX = 41
	
	# Screen constants
	MAX_LABEL_LENGTH = 9
	MAX_VALUE_LENGTH = 8

	KNOB_LED_IDXS = [0, 1, 2, 3, 4]

class SupportedParameterTypes(Enum):
	NUMBER = 'Number'
	MENU = 'Menu'
	TOGGLE = 'Toggle'
	PULSE = 'Pulse'

class VSN1ColorIndex(Enum):
	BLACK = 1
	WHITE = 2
	COLOR = 3

class ScreenMessages:
	HOVER = '_HOVER_'
	LEARNED = '_LEARNED_'
	STEP = '_STEP_'
	EXPR = '_EXPR_'
	UNSUPPORTED = '__'

class LabelDisplayMode(Enum):
	TRUNCATED = 'Truncated'
	COMPRESSED = 'Compressed'

class KnobLedUpdateMode(Enum):
	OFF = 'Off'
	VALUE = 'Value'
	STEPS = 'Step'
