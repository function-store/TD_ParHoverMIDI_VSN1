import json
import math
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

class VSN1Constants:
	# VSN1 Hardware mappings
	STEP_BUTTONS = {42: 1, 43: 0.1, 44: 0.01, 45: 0.001}
	SLOT_INDICES = [33, 34, 35, 36, 37, 38, 39, 40]
	KNOB_INDEX = 41
	RESET_INDEX = 41
	PULSE_INDEX = 41
	
	# Screen constants
	MAX_LABEL_LENGTH = 9
	MAX_VALUE_LENGTH = 8

class ScreenMessages:
	HOVER = '_HOVER_'
	LEARNED = '_LEARNED_'
	STEP = '_STEP_'
	EXPR = '_EXPR_'


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
		self.screen_manager = ScreenManager(self)
		
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
		self._initialize_screen()
	
	def _initialize_screen(self):
		"""Initialize VSN1 screen if enabled"""
		if not self.evalVsn1screensupport:
			return
			
		self.screen_manager.clear_screen()
		if self.activePar is not None:
			self.screen_manager.update_parameter_display(self.activePar)
		else:
			self.screen_manager.update_all_display(0.5, 0, 1, ScreenMessages.HOVER, 
												  ScreenMessages.HOVER, compress=False)

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
		self.screen_manager.update_step_display(value)


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
		
		# Handle expression mode parameters
		if not ParameterValidator.is_valid_parameter(_par) and self.activeSlot is None:
			self.screen_manager.update_all_display(0.5, 0, 1, _par.label, 
													  ScreenMessages.EXPR, compress=True)
			return

		self.hoveredPar = _par

		# Update screen if no active slot
		if self.activeSlot is None:
			self.screen_manager.update_parameter_display(_par)

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
		
		if hovered_par is not None and ParameterValidator.is_valid_parameter(hovered_par):
			# Extend slot list if necessary
			while len(self.slotPars) <= block_idx:
				self.slotPars.append(None)
				
			# Assign parameter to slot
			self.slotPars[block_idx] = hovered_par
			self.screen_manager.update_all_display(
				hovered_par.eval(), hovered_par.normMin, hovered_par.normMax, 
				hovered_par.label, ScreenMessages.LEARNED, compress=False)
		else:
			self.activeSlot = None
			self.screen_manager.update_all_display(
				0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)

	def onResetPar(self):
		"""TouchDesigner callback to reset active parameter"""
		if self.activePar is not None:
			self.activePar.reset()
			self.screen_manager.update_parameter_display(self.activePar)

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
		self.screen_manager.update_parameter_display(active_par)

	def _set_step_parameter(self, block):
		"""Set step value for sequence block with logarithmic progression"""
		par_step = block.par.Step
		block_index = block.index
		
		# Set step progression: first block gets 1, then each gets /10
		step_value = 1.0 / (10 ** block_index)
		if par_step.eval() == 0:
			par_step.val = step_value

	def _index_to_blocks(self, index: int, sequence) -> List:
		"""Find all sequence blocks matching the given MIDI index"""
		blocks = []
		for block in sequence:
			if tdu.match(block.par.Index.eval(), [index]):
				blocks.append(block)
		return blocks

# endregion helper functions
# region parameter callbacks

	def onParClear(self):
		"""TouchDesigner callback to clear all MIDI mappings"""
		# Reset sequence blocks
		self.seqSteps.numBlocks = 1
		self.seqSteps[0].par.Index = ''
		self.seqSteps[0].par.Step.val = 1.0
		
		self.seqSlots.numBlocks = 1
		self.seqSlots[0].par.Index = ''
		
		# Clear MIDI indices
		self.parKnobindex.val = ''
		self.parResetparindex.val = ''
		self.parPulseindex.val = ''
		
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
		if int(index) != int(self.parent.evalKnobindex):
			return False
			
		if active_par is not None and active_par.owner != self.parent.ownerComp:
			self.parent._do_step(self.parent._currStep, value)
		return True
	
	def handle_pulse_message(self, index: int, value: int, active_par) -> bool:
		"""Handle pulse button messages"""
		if index != int(self.parent.evalPulseindex):
			return False
			
		if (active_par is not None and 
			active_par.owner != self.parent.ownerComp and 
			active_par.isPulse):
			if value == MidiConstants.MAX_VELOCITY:
				active_par.pulse()
			self.parent.screen_manager.update_parameter_display(active_par)
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
		
		if block_idx < len(self.parent.slotPars):
			self.parent.activeSlot = block_idx
			self.parent.screen_manager.update_parameter_display(self.parent.slotPars[block_idx])
		else:
			self.parent.activeSlot = None
			label = self.parent.hoveredPar.label if self.parent.hoveredPar else ScreenMessages.HOVER
			self.parent.screen_manager.update_all_display(0, 0, 1, label, ScreenMessages.HOVER, compress=False)
		return True

class ScreenManager:
	"""Manages VSN1 screen updates"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
	
	def is_screen_enabled(self) -> bool:
		return self.parent.evalVsn1screensupport
	
	def compress_label(self, label: str, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Compress labels only if longer than max_length"""
		label = self._sanitize_label_for_lua(label)
		
		if len(label) <= max_length:
			return label
		
		# Remove whitespace and underscores
		compressed = label.replace(' ', '').replace('_', '')
		
		# Remove vowels (keep first character)
		vowels = 'aeiouAEIOU'
		if len(compressed) > 1:
			compressed = compressed[0] + ''.join(c for c in compressed[1:] if c not in vowels)
		
		return compressed[:max_length]
	
	def _sanitize_label_for_lua(self, label: str) -> str:
		"""Remove characters that could break Lua string syntax"""
		if not label:
			return 'Param'
		
		sanitized = label.replace('"', '').replace("'", '').replace('\\', '').replace('\n', '').replace('\r', '')
		return sanitized if sanitized else 'Param'
	
	def _format_value(self, value: Any, max_length: int = VSN1Constants.MAX_VALUE_LENGTH) -> str:
		"""Format values for display"""
		if isinstance(value, (int, float)):
			value = round(value, 6)
		return str(value)[:max_length]
	
	def update_all_display(self, val: float, norm_min: float, norm_max: float, 
						  label: str, display_text: Optional[str] = None, compress: bool = True):
		"""Update screen with all parameter info"""
		if not self.is_screen_enabled():
			return
		
		# Process label
		if self.parent.evalUsecompressedlabels and compress:
			processed_label = self.compress_label(label)
		else:
			processed_label = self._format_value(label)
		
		# Format values
		val_formatted = self._format_value(val)
		min_formatted = self._format_value(norm_min)
		max_formatted = self._format_value(norm_max)
		
		display_str = display_text if display_text is not None else val_formatted
		lua_code = f"update_param({val_formatted}, {min_formatted}, {max_formatted}, '{processed_label}', '{display_str}')"
		
		self._send_to_screen(lua_code)
	
	def update_parameter_display(self, par):
		"""Update screen for a specific parameter"""
		if not self.is_screen_enabled() or par is None:
			return
		
		if par.isMenu:
			val = par.menuIndex
			min_val, max_val = 0, len(par.menuNames) - 1
			display_text = str(par.menuLabels[par.menuIndex])
			if self.parent.evalUsecompressedlabels:
				display_text = self.compress_label(display_text)
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
		
		self.update_all_display(val, min_val, max_val, par.label, display_text, compress=True)
	
	def update_step_display(self, step: float):
		"""Update screen with current step value"""
		seq = self.parent.seqSteps
		min_step = seq[-1].par.Step.eval()
		max_step = seq[0].par.Step.eval()
		
		# Logarithmic mapping
		mapped_step = min_step + (max_step - min_step) * (
			(math.log(step) - math.log(min_step)) / (math.log(max_step) - math.log(min_step))
		)
		
		self.update_all_display(mapped_step, min_step, max_step, ScreenMessages.STEP, 
							   display_text=str(step), compress=False)
	
	def clear_screen(self):
		"""Clear the VSN1 screen"""
		lua_code = "--[[@cb]] lcd:ldaf(0,0,319,239,c[1])lcd:ldrr(3,3,317,237,10,c[2])"
		self._send_to_screen(lua_code)
	
	def _send_to_screen(self, lua_code: str):
		"""Send Lua code to screen via websocket"""
		package = {
			'type': 'execute-code',
			'script': lua_code
		}
		self.parent.websocket.sendText(json.dumps(package))

###


