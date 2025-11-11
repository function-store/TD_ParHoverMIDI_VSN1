
'''Info Header Start
Name : constants
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.188.toe
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
	CHANNEL = 16
	STEP_BUTTONS = {10: 0.001, 11: 0.01, 12: 0.1, 13: 1}
	BANK_BUTTONS = [10, 11, 12, 13]
	SLOT_INDICES = [1, 2, 3, 4, 5, 6, 7, 8]
	KNOB_INDEX = 9
	PUSH_INDEX = 9
	ROTARY_LED_FEEDBACK_INDEX = 128
	
	# Screen constants
	MAX_LABEL_LENGTH = 11
	MAX_VALUE_LENGTH = 10

	KNOB_LED_IDXS = [0, 1, 2, 3, 4]

class SupportedParameterTypes(Enum):
	NUMBER = 'Number'
	MENU = 'Menu'
	TOGGLE = 'Toggle'
	PULSE = 'Pulse'
	MOMENTARY = 'Momentary'

class VSN1ColorIndex(Enum):
	BLACK = 1
	WHITE = 2
	COLOR = 3

class ScreenMessages:
	HOVER = '_HOVER_'
	LEARNED = '_LEARNED_'
	STEP = '_STEP_'
	EXPR = '_EXPR_'
	UNSUPPORTED = '___'
	INVALID = '_INVALID_'
	EXPR_PREFIX = 'E('
	MIDI_ERROR = '_MIDIERR_'

class LabelDisplayMode(Enum):
	TRUNCATED = 'Truncated'
	COMPRESSED = 'Compressed'

class KnobLedUpdateMode(Enum):
	OFF = 'Off'
	VALUE = 'Value'
	STEPS = 'Step'

class StepMode(Enum):
	FIXED = 'Fixed'
	ADAPTIVE = 'Adaptive'

class PushStepMode(Enum):
	FIXED = 'Fixed'
	FINER = 'Finer'
	COARSER = 'Coarser'

class MultiAdjustMode(Enum):
	OFF = 'Off'
	SNAP = 'Snap'
	RELATIVE = 'Relative'

class OverrideUIElements:
	"""
	List of parameters to override in the UI.
	These are the parameters that are used to display the UI elements.
	Notes:
		- .selected.loc is darkest
		- .selected is middle (+ 0.025)
		- .loc is lightest (+ 0.05) of .selected, (+ 0.075) of .selected.loc
		- for menubar, button it's the opposite (.sel is darker)
		- toggle thumb on is 0.65 lighter than off
	"""
	PARMS = \
		[
			'parms.button.bg.loc',
			'parms.button.bg.sel',
			'parms.field.numeric.bg.loc',
			'parms.field.numeric.bg.selected.loc',
			'parms.slider.thumb.loc',
			'parms.menubar.bg.loc',
			'parms.menubar.bg.sel',
			'parms.toggle.thumb.off.loc',
			'parms.toggle.thumb.on.loc',
			'parms.label.fg.loc',
			'parms.dialog.fg'
		]
