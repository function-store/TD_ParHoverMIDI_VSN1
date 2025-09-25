import json
import math
import re
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from TDStoreTools import StorageManager
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import

# Import separated modules
from constants import *
from validators import ParameterValidator
from formatters import LabelFormatter
from handlers import MidiMessageHandler
from display_manager import DisplayManager
from slot_manager import SlotManager
from vsn1_manager import VSN1Manager
from ui_manager import UIManager



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
		self.slot_manager = SlotManager(self)
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
			self.display_manager.update_parameter_display(self.activePar, force_knob_leds=True)
		else:
			self.display_manager.update_all_display(0.5, 0, 1, ScreenMessages.HOVER, 
													ScreenMessages.HOVER, compress=False)



		self.display_manager.update_all_slot_leds()
		
		# Initialize UI button labels based on current slot assignments
		if hasattr(self, 'ui_manager'):
			for i, slot_par in enumerate(self.slotPars):
				if slot_par is not None:
					label = LabelFormatter.get_label_for_parameter(slot_par, self.labelDisplayMode)
					self.ui_manager._set_button_label(i, label)
				else:
					self.ui_manager._set_button_label(i, ScreenMessages.HOVER)
		
		# Set initial outline color based on current state
		if self.activeSlot is not None:
			self.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)  # Active slot
		else:
			self.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)  # Hover mode

		if self.knobLedUpdateMode in [KnobLedUpdateMode.STEPS]:
			step_idx = next((i for i, s in enumerate(self.seqSteps) if s.par.Step.eval() == self._currStep), 0)
			self.vsn1_manager.update_knob_leds_steps(step_idx)
		
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

	@property
	def labelDisplayMode(self) -> LabelDisplayMode:
		"""Get the current label display mode from component parameter"""
		# covert text to enum
		return LabelDisplayMode(self.evalLabeldisplaymode)

	@property
	def knobLedUpdateMode(self) -> KnobLedUpdateMode:
		"""Get the current knob LED update mode from component parameter"""
		return KnobLedUpdateMode(self.evalKnobledupdate)


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
		
		self.hoveredPar = _par
		# Handle invalid/unsupported parameters when no active slot
		if self.activeSlot is None:
			if not ParameterValidator.is_valid_parameter(_par):
				param_label = LabelFormatter.get_label_for_parameter(_par, self.labelDisplayMode)
				self.display_manager.update_all_display(0.5, 0, 1, param_label, 
														ScreenMessages.EXPR, compress=True)
				return  # Don't proceed to normal parameter display
			
			if not ParameterValidator.is_supported_parameter_type(_par):
				param_label = LabelFormatter.get_label_for_parameter(_par, self.labelDisplayMode)
				self.display_manager.update_all_display(0.5, 0, 1, param_label, 
														ScreenMessages.UNSUPPORTED, compress=True)
				return  # Don't proceed to normal parameter display

		# Update screen if no active slot (only for valid parameters)
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
		
		if hovered_par is not None:
			# Try to assign parameter to slot
			success = self.slot_manager.assign_slot(block_idx, hovered_par)
			if not success:
				# Invalid parameter - clear the slot instead
				self.slot_manager.clear_slot(block_idx)
		else:
			# No hovered parameter - clear the slot
			self.slot_manager.clear_slot(block_idx)

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

	def onParKnobledupdate(self, _par, _val):
		"""TouchDesigner callback when knob LED update mode parameter changes"""
		if KnobLedUpdateMode(_val) in [KnobLedUpdateMode.VALUE, KnobLedUpdateMode.OFF]:
			self.display_manager.update_parameter_display(self.activePar, force_knob_leds=True)
		else:
			step_idx = next((i for i, s in enumerate(self.seqSteps) if s.par.Step.eval() == self._currStep), None)
			self.vsn1_manager.update_knob_leds_steps(step_idx)

	def onParVsn1support(self, _par, _val):
		"""TouchDesigner callback when VSN1 support parameter changes"""
		if _val:
			self.ownerComp.par.Resetcomm.pulse()

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





