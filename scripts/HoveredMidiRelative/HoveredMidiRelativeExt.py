import json
import math
import re
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from TDStoreTools import StorageManager
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import

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


class HoveredMidiRelativeExt:
	"""
	TouchDesigner Extension for MIDI-controlled relativeparameter manipulation with VSN1 screen support
	"""
	
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		
		# Initialize TD operators
		self.activeMidi = self.ownerComp.op('midiin_active')
		self.resetMidi = self.ownerComp.op('midiin_reset')
		self.slotsLearnMidi = self.ownerComp.op('midiin_slots')
		self.websocket: websocketDAT = self.ownerComp.op('websocket1')
		
		# Initialize state
		self.hoveredPar: Optional[Par] = None
		
		# Initialize helper classes
		self.midi_handler = MidiMessageHandler(self)
		self.vsn1_manager = VSN1Manager(self)
		self.ui_manager = UIManager(self)
		self.display_manager = DisplayManager(self)

		# Initialize storage
		storedItems = [
			{
				'name': 'slotPars',
				'default': [],
				'readOnly': False,
				'property': True,
				'dependable': False
			},
			{
				'name': 'activeSlot',
				'default': None,
				'readOnly': False,
				'property': True,
				'dependable': False
			},
			{
				'name': 'currStep',
				'default': self.evalDefaultstepsize,
				'readOnly': False,
				'property': True,
				'dependable': False
			}
		]

		self.stored = StorageManager(self, ownerComp, storedItems)

		# Initialize screen
		self._initialize_VSN1()
	
	def _initialize_VSN1(self):
		"""Initialize VSN1 screen if enabled"""
		if not self.evalVsn1support:
			return
			
		self.display_manager.clear_screen()
		if self.activePar is not None:
			self.display_manager.update_parameter_display(self.activePar)
		else:
			self.display_manager.update_all_display(0.5, 0, 1, ScreenMessages.HOVER, 
													ScreenMessages.HOVER, compress=False)

		self.display_manager.update_all_slot_leds()
		# Set initial outline color based on current state
		if self.activeSlot is not None:
			self.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)  # Active slot
		else:
			self.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)  # Hover mode
		
# region properties
		
	@property
	def seqSteps(self):
		"""Get sequence steps from owner component"""
		return self.ownerComp.seq.Steps

	@property
	def seqSlots(self):
		"""Get sequence slots from owner component"""
		return self.ownerComp.seq.Slots

	@property
	def activePar(self) -> Optional[Par]:
		"""Get currently active parameter (slot takes priority over hovered)"""
		# Prioritize active slot parameters over hovered parameter
		if (self.activeSlot is not None and 
			self.activeSlot < len(self.slotPars) and 
			self.slotPars[self.activeSlot] is not None):
				return self.slotPars[self.activeSlot]
			
		if self.hoveredPar is not None:
			return self.hoveredPar
			
		return None

	# NOTE: Intermediary property since TD stored properties cannot have setters
	@property
	def _currStep(self) -> float:
		return self.currStep

	@_currStep.setter
	def _currStep(self, value: float):
		self.currStep = value
		self.display_manager.update_step_display(value)


	def onHoveredParChange(self, _op, _par, _expr, _bindExpr):
		"""TouchDesigner callback when hovered parameter changes"""
		self.hoveredPar = None

		if not self.evalActive:
			return
			
		# Validate inputs
		if _op is None or _par is None:
			return
			
		if not (_op := op(_op)):
			return
			
		if (_par := getattr(_op.par, _par)) is None:
			return
		
		# Handle invalid/unsupported parameters when no active slot
		if self.activeSlot is None:
			if not ParameterValidator.is_valid_parameter(_par):
				self.display_manager.update_all_display(0.5, 0, 1, _par.label, 
														ScreenMessages.EXPR, compress=True)
				
			
			if not ParameterValidator.is_supported_parameter_type(_par):
				self.display_manager.update_all_display(0.5, 0, 1, _par.label, 
														ScreenMessages.UNSUPPORTED, compress=True)
				


		self.hoveredPar = _par
		
		# Update screen if no active slot
		if self.activeSlot is None:
			self.display_manager.update_parameter_display(_par)

# endregion properties

# region midi callbacks

	def onReceiveMidi(self, dat, rowIndex, message, channel, index, value, input, byteData):
		"""TouchDesigner callback for MIDI input processing"""
		if channel != self.evalChannel or not self.evalActive:
			return
		
		active_par = self.activePar
		hovered_par = self.hoveredPar
		index = int(index)

		# Process different message types using helper class
		if message == MidiConstants.NOTE_ON:
			# Handle step sequence messages
			if self.midi_handler.handle_step_message(index, value):
				return
				
			# Handle pulse messages
			if self.midi_handler.handle_pulse_message(index, value, active_par):
				return
		
			# Handle slot selection messages
			if self.midi_handler.handle_slot_message(index, value):
					return
			
		elif message == MidiConstants.CONTROL_CHANGE:
			# Handle knob control messages
			if self.midi_handler.handle_knob_message(index, value, active_par):
				return


	def onReceiveMidiLearn(self, dat, rowIndex, message, channel, index, value, input, byteData):
		"""TouchDesigner callback for MIDI learning mode"""
		if channel != self.evalChannel or not self.evalActive:
			return
		
		hovered_par = self.hoveredPar
		if (hovered_par is None or 
			not ParameterValidator.is_learnable_parameter(hovered_par)):
				return
		
		# Control Change: knob learning only
		if message == MidiConstants.CONTROL_CHANGE and hovered_par == self.parKnobindex:
			hovered_par.val = index

		# Note On: button and step learning
		elif message == MidiConstants.NOTE_ON:
			if hovered_par in [self.parPulseindex, self.parResetparindex]:
				hovered_par.val = index
				
			if hovered_par in self.seqSteps.blockPars.Index:
				hovered_par.val = index
				self._set_step_parameter(hovered_par.sequenceBlock)
				
			elif hovered_par in self.seqSlots.blockPars.Index:
				hovered_par.val = index


	def onReceiveMidiSlotLearn(self, index: int):
		"""TouchDesigner callback for slot learning"""
		hovered_par = self.hoveredPar

		blocks = self._index_to_blocks(index, self.seqSlots)
		if not blocks:
			return
			
		block = blocks[0]
		block_idx = block.index
		if hovered_par is not None and ParameterValidator.is_valid_parameter(hovered_par) and \
			ParameterValidator.is_supported_parameter_type(hovered_par):
			
			# Extend slot list if necessary
			while len(self.slotPars) <= block_idx:
				self.slotPars.append(None)
				
			# Assign parameter to slot and activate it
			old_active_slot = self.activeSlot
			self.slotPars[block_idx] = hovered_par
			self.activeSlot = block_idx  # Learning also activates the slot

			# Display updates
			self.display_manager.update_all_display(
				hovered_par.eval(), hovered_par.normMin, hovered_par.normMax, 
				hovered_par.label, ScreenMessages.LEARNED, compress=False)
			# Update LEDs: new active slot and previous active slot
			self.display_manager.update_slot_leds(current_slot=block_idx, previous_slot=old_active_slot)
			# Update outline color for active slot (learning activates the slot)
			self.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		else:
			self.activeSlot = None
			self.slotPars[block_idx] = None
			self.display_manager.update_all_display(
				0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
			# Update LED for the slot we just cleared
			self.display_manager.update_slot_leds(current_slot=block_idx)
			# Update outline color for hover mode (slot cleared)
			self.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)

	def onResetPar(self):
		"""TouchDesigner callback to reset active parameter"""
		if self.activePar is not None:
			self.activePar.reset()
			self.display_manager.update_parameter_display(self.activePar)

# endregion midi callbacks

# region helper functions

	def _do_step(self, step: float, value: int):
		"""Apply step value to active parameter based on MIDI input"""
		active_par = self.activePar
		if active_par is None or not ParameterValidator.is_valid_parameter(active_par):
			return
			
		diff = value - MidiConstants.MIDI_CENTER_VALUE
		step_amount = step * diff
		
		if active_par.isNumber:
			# Handle numeric parameters (float/int)
			current_val = active_par.eval()
			# for ints step is always 1 # TODO: this is debatable
			if active_par.isInt:
				step_amount = 1 if step_amount > 0 else -1
			new_val = current_val + step_amount
			active_par.val = new_val
			
		elif active_par.isMenu:
			# Handle menu parameters - step through menu options
			if abs(diff) >= 1:  # Only change on significant step
				current_index = active_par.menuIndex
				step_direction = 1 if step_amount > 0 else -1
				new_index = current_index + step_direction
				active_par.menuIndex = new_index
				
		elif active_par.isToggle:
			# Handle toggle parameters - step through on/off states
			current_val = active_par.eval()
			if step_amount > 0 and not current_val:
				active_par.val = True
			elif step_amount < 0 and current_val:
				active_par.val = False
		else:
			# Unsupported parameter type
			return
			
		# Update screen display
		self.display_manager.update_parameter_display(active_par)

	def _set_step_parameter(self, block):
		"""Set step value for sequence block with logarithmic progression"""
		par_step = block.par.Step
		block_index = block.index
		
		# Set step progression: first block gets 1, then each gets /10
		step_value = 1.0 / (10 ** block_index)
		if par_step.eval() == 0:
			par_step.val = step_value

	def _safe_get_midi_index(self, index_param_or_value, default: int = None) -> Optional[int]:
		"""Safely convert a parameter value or string to MIDI index, handling empty strings and invalid values"""
		try:
			# Handle parameter objects
			if hasattr(index_param_or_value, 'eval'):
				value = index_param_or_value.eval()
			else:
				value = index_param_or_value
			
			# Check if empty or invalid
			if not value or not str(value).strip():
				return default
			
			# Convert to int
			midi_index = int(value)
			return midi_index if midi_index >= 0 else default
			
		except (ValueError, TypeError, AttributeError):
			return default
	
	def _index_to_blocks(self, index: int, sequence) -> List:
		"""Find all sequence blocks matching the given MIDI index"""
		blocks = []
		for block in sequence:
			if tdu.match(block.par.Index.eval(), [index]):
				blocks.append(block)
		return blocks
	
	def _clear_all_slot_leds(self):
		"""Turn off all slot LEDs"""
		if hasattr(self, 'vsn1_manager'):
			for i in range(len(self.seqSlots)):
				self.display_manager.send_slot_led_feedback(i, 0)


# endregion helper functions
# region parameter callbacks

	def onParClear(self):
		"""TouchDesigner callback to clear all MIDI mappings"""
		# Clear all slot LEDs before resetting
		self._clear_all_slot_leds()
		
		# Reset sequence blocks
		self.seqSteps.numBlocks = 1
		self.seqSteps[0].par.Index = ''
		self.seqSteps[0].par.Step.val = 0.001
		
		self.seqSlots.numBlocks = 1
		self.seqSlots[0].par.Index = ''
		
		# Clear MIDI indices
		self.parKnobindex.val = ''
		self.parResetparindex.val = ''
		self.parPulseindex.val = ''
		
		# Reset active slot
		self.activeSlot = None
		
		# Force cook MIDI operators
		self._force_cook_midi_operators()

	# TODO: These can be optimized using Dependency objects
	def onSeqStepsNIndex(self, _par, idx):
		"""TouchDesigner callback when sequence steps index changes"""
		self.activeMidi.cook(force=True)

	def onSeqSlotsNIndex(self, _par, idx):
		"""TouchDesigner callback when sequence slots index changes"""
		self.activeMidi.cook(force=True)
		self.slotsLearnMidi.cook(force=True)

	def onParKnobindex(self, _par, _val):
		"""TouchDesigner callback when knob index parameter changes"""
		self.activeMidi.cook(force=True)

	def onParResetparindex(self, _par, _val):
		"""TouchDesigner callback when reset parameter index changes"""
		self.resetMidi.cook(force=True)

	def onParPeriststep(self, _par, _val):
		"""TouchDesigner callback when persist step parameter changes"""
		if not _val:
			self._currStep = self.evalDefaultstepsize
			
	def onParDefaultstepsize(self, _par, _val):
		"""TouchDesigner callback when default step size parameter changes"""
		if not self.evalPersiststep:
			self._currStep = _val

	def onParUsedefaultsforvsn1(self):
		"""TouchDesigner callback to set VSN1 hardware defaults"""
		# Configure step buttons with their respective step values
		self.seqSteps.numBlocks = len(VSN1Constants.STEP_BUTTONS)
		for i, (button, step) in enumerate(VSN1Constants.STEP_BUTTONS.items()):
			self.seqSteps[i].par.Index.val = button
			self.seqSteps[i].par.Step.val = step

		# Configure slot indices
		self.seqSlots.numBlocks = len(VSN1Constants.SLOT_INDICES)
		for i, index in enumerate(VSN1Constants.SLOT_INDICES):
			self.seqSlots[i].par.Index.val = index

		# Set control indices
		self.parKnobindex.val = VSN1Constants.KNOB_INDEX
		self.parResetparindex.val = VSN1Constants.RESET_INDEX
		self.parPulseindex.val = VSN1Constants.PULSE_INDEX

		# Force cook MIDI operators
		self._force_cook_midi_operators()
	
	def _force_cook_midi_operators(self):
		"""Force cook all MIDI-related operators"""
		self.activeMidi.cook(force=True)
		self.resetMidi.cook(force=True)
		self.slotsLearnMidi.cook(force=True)

# endregion parameter callbacks

# endregion

class ParameterValidator:
	"""Helper class for parameter validation"""
	
	@staticmethod
	def is_valid_parameter(par) -> bool:
		"""Check if parameter is valid for MIDI control"""
		if par is None:
			return False
		return par.mode in [ParMode.CONSTANT, ParMode.BIND]
	
	@staticmethod
	def is_learnable_parameter(par) -> bool:
		"""Check if parameter is learnable ie valid and empty"""
		return ParameterValidator.is_valid_parameter(par) and not par.eval()

	@staticmethod
	def is_supported_parameter_type(par) -> bool:
		"""Check if parameter is supported for MIDI control"""
		return any(getattr(par, f'is{type.value}') for type in SupportedParameterTypes)

class MidiMessageHandler:
	"""Handles MIDI message processing logic"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
	
	
	def handle_step_message(self, index: int, value: int) -> bool:
		"""Handle step change messages"""
		blocks = self.parent._index_to_blocks(index, self.parent.seqSteps)
		if not blocks:
			return False
			
		block = blocks[0]
		if value == MidiConstants.MAX_VELOCITY:
			self.parent._currStep = block.par.Step.eval()
		elif not self.parent.evalPersiststep and value == 0:
			self.parent._currStep = self.parent.evalDefaultstepsize
		return True
	
	def handle_knob_message(self, index: int, value: int, active_par) -> bool:
		"""Handle knob control messages"""
		knob_index = self.parent._safe_get_midi_index(self.parent.evalKnobindex, default=-1)
		if int(index) != knob_index:
			return False
			
		if active_par is not None and active_par.owner != self.parent.ownerComp:
			self.parent._do_step(self.parent._currStep, value)
		return True
	
	def handle_pulse_message(self, index: int, value: int, active_par) -> bool:
		"""Handle pulse button messages"""
		pulse_index = self.parent._safe_get_midi_index(self.parent.evalPulseindex, default=-1)
		if index != pulse_index:
			return False
			
		if (active_par is not None and 
			active_par.owner != self.parent.ownerComp and 
			active_par.isPulse):
			if value == MidiConstants.MAX_VELOCITY:
				active_par.pulse()
			self.parent.display_manager.update_parameter_display(active_par)
		return True
	
	def handle_slot_message(self, index: int, value: int) -> bool:
		"""Handle slot selection messages"""
		if value != MidiConstants.MAX_VELOCITY:
			return False
			
		blocks = self.parent._index_to_blocks(index, self.parent.seqSlots)
		if not blocks:
			return False
			
		block = blocks[0]
		block_idx = block.index
		
		# Get previous slot index for LED feedback
		prev_slot_index = self.parent.activeSlot
		
		if block_idx < len(self.parent.slotPars) and self.parent.slotPars[block_idx] is not None:
			# Activate slot
			old_active_slot = self.parent.activeSlot
			self.parent.activeSlot = block_idx
			self.parent.display_manager.update_parameter_display(self.parent.slotPars[block_idx])
			# Update LEDs: previous slot and new active slot
			self.parent.display_manager.update_slot_leds(current_slot=block_idx, previous_slot=old_active_slot)
			# Update outline color for active slot
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		else:
			# Deactivate slot (return to hover mode)
			old_active_slot = self.parent.activeSlot
			self.parent.activeSlot = None
			label = self.parent.hoveredPar.label if self.parent.hoveredPar is not None else ScreenMessages.HOVER
			compress = False if label == ScreenMessages.HOVER else True
			self.parent.display_manager.update_all_display(0.5, 0, 1, label, ScreenMessages.HOVER, compress=compress)
			# Update LED: turn off the previously active slot
			self.parent.display_manager.update_slot_leds(previous_slot=old_active_slot)
			# Update outline color for hover mode
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		return True


class DisplayManager:
	"""Unified display manager that handles ALL display logic and delegates to renderers"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.vsn1_renderer = parent_ext.vsn1_manager
		self.ui_renderer = parent_ext.ui_manager
	
	def clear_screen(self):
		"""Clear all displays"""
		self.vsn1_renderer.clear_screen()
		self.ui_renderer.clear_screen()
	
	def update_all_display(self, val, norm_min, norm_max, 
						  label: str, display_text: Optional[str] = None, step_indicator = None, compress: bool = True):
		"""Update all displays with parameter info - handles ALL logic here"""
		# Process label with optional compression
		if compress and self.parent.evalUsecompressedlabels:
			processed_label = LabelFormatter.compress_label(label)
		else:
			processed_label = LabelFormatter.format_value(label)
		
		# Calculate circle fill percentage - handle both numeric and string values
		try:
			val_num = float(val)
			norm_min_num = float(norm_min) 
			norm_max_num = float(norm_max)
			
			if norm_max_num != norm_min_num:
				percentage = (val_num - norm_min_num) / (norm_max_num - norm_min_num)
			else:
				percentage = 0.5
		except (ValueError, TypeError):
			percentage = 0.5
		
		# Use display_text if provided, otherwise format the value
		if display_text is not None:
			bottom_text = display_text
		else:
			bottom_text = LabelFormatter.format_value(val)
		
		# Delegate to renderers with processed data
		self.vsn1_renderer.render_display(val, norm_min, norm_max, processed_label, bottom_text, percentage, step_indicator)
		self.ui_renderer.render_display(val, norm_min, norm_max, processed_label, bottom_text, percentage, step_indicator)
	
	def update_parameter_display(self, par):
		"""Update displays for a specific parameter - handles ALL logic here"""
		if par is None:
			return
			
		# Handle different parameter types - ALL logic here
		if par.isMenu:
			val = par.menuIndex
			min_val, max_val = 0, len(par.menuNames) - 1
			display_text = str(par.menuLabels[par.menuIndex])
			if self.parent.evalUsecompressedlabels:
				display_text = LabelFormatter.compress_label(display_text)
		elif par.isToggle:
			val = 1 if par.eval() else 0
			min_val, max_val = 0, 1
			display_text = "On" if val else "Off"
		elif par.isPulse:
			val = 1 if par.eval() else 0
			min_val, max_val = 0, 1
			display_text = "Pulse"
		else:
			val = par.eval()
			min_val, max_val = par.normMin, par.normMax
			display_text = None

		label = par.label
		if not label and (block := par.sequenceBlock):
			name = par.name
			name = re.split(r'\d+', name)[-1]
			if name:
				if isinstance(block.owner, constantCHOP):
					label = block.par.name.eval()
				else:
					label = name.capitalize()
		
		# Use the unified display logic
		self.update_all_display(val, min_val, max_val, label, display_text, compress=True)
	
	def update_step_display(self, step: float):
		"""Update displays with current step value - handles ALL logic here"""
		seq = self.parent.seqSteps
		if len(seq) == 0:
			return
			
		# Calculate step display values
		min_step = min(s.par.Step.eval() for s in seq)
		max_step = max(s.par.Step.eval() for s in seq)
		
		# Map step to 0-1 range for display
		if max_step != min_step:
			mapped_step = (step - min_step) / (max_step - min_step)
		else:
			mapped_step = 0.5
		
		# Find step index for indicator
		index = next((i for i, s in enumerate(seq) if s.par.Step.eval() == step), None)
		
		self.update_all_display(mapped_step, max_step, min_step, ScreenMessages.STEP, 
							   display_text=str(step), step_indicator=index, compress=False)
	
	# VSN1-specific methods that also update UI equivalents
	def update_all_slot_leds(self):
		"""Update all slot LEDs and UI equivalents"""
		self.vsn1_renderer.update_all_slot_leds()
		self.ui_renderer.update_all_slot_indicators()
	
	def update_slot_leds(self, current_slot=None, previous_slot=None):
		"""Update specific slot LEDs and UI equivalents"""
		self.vsn1_renderer.update_slot_leds(current_slot, previous_slot)
		self.ui_renderer.update_slot_indicators(current_slot, previous_slot)
	
	def update_outline_color_index(self, color_index: int):
		"""Update outline color and UI equivalent"""
		self.vsn1_renderer.update_outline_color_index(color_index)
		self.ui_renderer.update_outline_color(color_index)
	
	def send_slot_led_feedback(self, slot_idx: int, value: int):
		"""Send slot feedback to both displays"""
		self.vsn1_renderer.send_slot_led_feedback(slot_idx, value)
		self.ui_renderer.send_slot_feedback(slot_idx, value)


class VSN1Manager:
	"""Manages VSN1 hardware integration - screen updates and LED feedback"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.grid_comm : IntechGridCommExt = self.parent.ownerComp.op('IntechGridComm').ext.IntechGridCommExt
	
	def is_vsn1_enabled(self) -> bool:
		return self.parent.evalVsn1support
	
	def render_display(self, val, norm_min, norm_max, processed_label: str, bottom_text: str, percentage: float, step_indicator = None):
		"""Render display data to VSN1 screen - ONLY the Lua output, no logic"""
		if not self.is_vsn1_enabled():
			return
			
		# Simple Lua function call - ONLY difference from UI renderer
		lua_code = f"update_param({val}, {norm_min}, {norm_max}, '{processed_label}', '{bottom_text}', {step_indicator})"
		self.grid_comm.SendLua(lua_code)
	
	def clear_screen(self):
		"""Clear the VSN1 screen"""
		lua_code = "--[[@cb]] lcd:ldaf(0,0,319,239,c[1])lcd:ldrr(3,3,317,237,10,c[2])"
		self.grid_comm.SendLua(lua_code)
	
	def set_step_indicator(self, index: int):
		"""Set step indicator on VSN1 display"""
		# Handled by main render_display
		pass
		
	
	def _send_slot_led(self, slot_idx: int, value: int):
		"""Send LED command for a specific slot"""
		if not self.is_vsn1_enabled():
			return
		self.grid_comm.SendLua(f'set_led({10+slot_idx},1,{int(value)})')
	
	def send_slot_led_feedback(self, slot_index: int, value: int, prev_slot_index: int = None):
		"""Send LED feedback to VSN1 controller using slot indices (0-based)"""
		if not self.is_vsn1_enabled():
			return
		
		# Send LED command using slot index directly (0-based)
		self._send_slot_led(slot_index, value)
		
		# Turn off previous LED if specified
		if prev_slot_index is not None and prev_slot_index != slot_index:
			self._send_slot_led(prev_slot_index, 0)
	
	def update_all_slot_leds(self):
		"""Update all slot LEDs based on current state: 0=free, 30=occupied, 255=active (initialization only)"""
		if not self.is_vsn1_enabled():
			return
			
		# Update LEDs for all possible slots (used only during initialization)
		for slot_idx in range(len(VSN1Constants.SLOT_INDICES)):
			led_value = self._get_slot_led_value(slot_idx)
			self._send_slot_led(slot_idx, led_value)
	
	def update_slot_leds(self, current_slot: int = None, previous_slot: int = None):
		"""Update only current and previous slot LEDs for efficiency"""
		if not self.is_vsn1_enabled():
			return
		
		# Update previous slot LED (if specified)
		if previous_slot is not None:
			prev_led_value = self._get_slot_led_value(previous_slot)
			self._send_slot_led(previous_slot, prev_led_value)
		
		# Update current slot LED (if specified)
		if current_slot is not None:
			curr_led_value = self._get_slot_led_value(current_slot)
			self._send_slot_led(current_slot, curr_led_value)
	
	def _get_slot_led_value(self, slot_idx: int) -> int:
		"""Get LED value for a slot: 0=free (hover), 30=occupied, 255=active"""
		# Check if slot is active
		if self.parent.activeSlot == slot_idx:
			return 255  # Active slot
			
		# Check if slot is occupied
		if slot_idx < len(self.parent.slotPars) and self.parent.slotPars[slot_idx] is not None:
			return 30   # Occupied slot
			
		return 0  # Free slot (hover mode)

	def update_outline_color_index(self, color_index: int):
		self.grid_comm.SendLua(f'rc={color_index};lcd:ldrr(3,3,317,237,10,c[rc])lcd:ldsw()')

###


class UIManager:
	"""Manager for UI elements"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.ui = self.parent.ownerComp.op('UI')

	@property
	def ui_enabled(self) -> bool:
		return self.parent.evalEnableui

	def _set_top_text(self, text: str):
		self.ui.par.Toptext.val = text

	def _set_bottom_text(self, text: str):
		self.ui.par.Bottomtext.val = text

	def _set_circle_fill(self, percentage: float):
		self.ui.par.Circlefill = tdu.clamp(tdu.remap(percentage, 0, 1, 0.05, 1), 0.05, 1)

	
	def render_display(self, val, norm_min, norm_max, processed_label: str, bottom_text: str, percentage: float, step_indicator = None):
		"""Render display data to UI - ONLY the UI parameter updates, no logic"""
		if not self.ui_enabled:
			return
		# Set UI parameters - ONLY difference from VSN1 renderer
		self._set_circle_fill(percentage)
		self._set_top_text(processed_label)
		self._set_bottom_text(bottom_text)
		
		# Set step indicator if provided
		if step_indicator is not None:
			self.set_step_indicator(step_indicator)
	
	def clear_screen(self):
		"""Clear the UI display - ONLY the UI parameter updates"""
		if not self.ui_enabled:
			return
		self._set_circle_fill(0.5)
		self._set_top_text("")
		self._set_bottom_text("")

	def set_step_indicator(self, index: int):
		if not self.ui_enabled:
			return
		#self.ui.par.StepIndicator.val = index
		pass
	
	# UI equivalents for VSN1 features
	def update_all_slot_indicators(self):
		"""Update all slot indicators in UI"""
		if not self.ui_enabled:
			return
		# TODO: Implement UI slot indicators
		pass
	
	def update_slot_indicators(self, current_slot=None, previous_slot=None):
		"""Update specific slot indicators in UI"""
		if not self.ui_enabled:
			return
		# TODO: Implement UI slot indicator updates
		pass
	
	def update_outline_color(self, color_index: int):
		"""Update UI outline/border color equivalent"""
		if not self.ui_enabled:
			return
		# TODO: Implement UI outline color changes
		pass
	
	def send_slot_feedback(self, slot_idx: int, value: int):
		"""Send slot feedback to UI equivalent"""
		if not self.ui_enabled:
			return
		# TODO: Implement UI slot feedback
		pass

		
class LabelFormatter:
	"""Utility class for label compression and formatting"""
	
	@staticmethod
	def compress_label(label: str, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Compress labels for display - removes whitespace and vowels if needed"""
		label = LabelFormatter._sanitize_label(label)
		
		if len(label) <= max_length:
			return label
		
		# Remove whitespace and underscores
		compressed = label.replace(' ', '').replace('_', '')
		
		# Remove vowels (keep first character)
		vowels = 'aeiouAEIOU'
		if len(compressed) > 1:
			compressed = compressed[0] + ''.join(c for c in compressed[1:] if c not in vowels)
		
		return compressed[:max_length]
	
	@staticmethod
	def _sanitize_label(label: str) -> str:
		"""Remove characters that could cause issues in display systems"""
		if not label:
			return 'Param'
		
		sanitized = label.replace('"', '').replace("'", '').replace('\\', '').replace('\n', '').replace('\r', '')
		return sanitized if sanitized else 'Param'
	
	@staticmethod
	def format_value(value: Any, max_length: int = VSN1Constants.MAX_VALUE_LENGTH) -> str:
		"""Format values for display with length limit"""
		if isinstance(value, (int, float)):
			value = round(value, 6)
		return str(value)[:max_length]
