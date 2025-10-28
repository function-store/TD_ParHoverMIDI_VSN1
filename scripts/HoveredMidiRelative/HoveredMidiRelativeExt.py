'''Info Header Start
Name : HoveredMidiRelativeExt
Author : Dan@DAN-4090
Saveversion : 2023.12120
Info Header End'''
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
from undo_manager import UndoManager



class HoveredMidiRelativeExt:
	"""
	TouchDesigner Extension for MIDI-controlled relativeparameter manipulation with VSN1 screen support
	"""
	
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		
		# Initialize TD operators
		self.midiOut = self.ownerComp.op('midiout1')

		self.websocket: websocketDAT = self.ownerComp.op('websocket1')

		# UI Mod init
		if _uimod := self.ownerComp.op('td_ui_mod'):
			if hasattr(_uimod, 'Install'):
				try:
					_uimod.Install()
				except Exception as error:
					pass
		
		# Initialize state - can be either a single Par or a ParGroup
		self.hoveredPar: Optional[Union[Par, ParGroup]] = None
		
		# Initialize helper classes
		self.midi_handler = MidiMessageHandler(self)
		self.vsn1_manager = VSN1Manager(self)
		self.ui_manager = UIManager(self)
		self.slot_manager = SlotManager(self)
		self.display_manager = DisplayManager(self)
		self.undo_manager = UndoManager(self)

		self.display_run_obj = None

		# Initialize storage
		storedItems = [
			{
				'name': 'slotPars',
				'default': [[None for _ in range(self.numSlots)] for _ in range(self.numBanks)],
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
				'default': 0.001,
				'readOnly': False,
				'property': True,
				'dependable': False
			},
			{
				'name': 'currBank',
				'default': 0,
				'property': True,
				'dependable': False
			},
			{
				'name': 'bankActiveSlots',
				'default': [None for _ in range(self.numBanks)],
				'readOnly': False,
				'property': True,
				'dependable': False
			},
			{
				'name': 'currentHoveredUIColor',
				'default': -1,
				'readOnly': False,
				'property': True,
				'dependable': False
			}
		]

		self.stored = StorageManager(self, ownerComp, storedItems)

		self.postInit()

	def postInit(self):
		# Needed to clear pickle errors due to missing parameters in storage, before we can even validate
		self._validate_storage()

		# Initialize screen
		self._initialize_VSN1()

		if self.activeSlot is None and self.evalColorhoveredui:
			self.ui_manager.set_hovered_ui_color(self.evalColorindex-1, force=True)
		else:
			self.ui_manager.set_hovered_ui_color(-1, force=True)

		# set UI stuff based on current evalStepmode
		self.ui_manager.set_stepmode_indicator(self.stepMode)


	def _validate_storage(self):
		"""Validate storage and ensure proper structure for dynamic bank changes"""
		# Ensure slotPars is properly structured as 2D array
		if not isinstance(self.slotPars, list):
			self.slotPars = []
		
		# Ensure bankActiveSlots is properly structured
		if not isinstance(self.bankActiveSlots, list):
			self.bankActiveSlots = []
		
		# Ensure we have at least as many banks as configured
		current_num_banks = self.numBanks
		
		# Extend slotPars if we have more banks than before
		while len(self.slotPars) < current_num_banks:
			self.slotPars.append([])
		
		# Extend bankActiveSlots if we have more banks than before
		while len(self.bankActiveSlots) < current_num_banks:
			self.bankActiveSlots.append(None)
		
		# Truncate if we have fewer banks than before (but preserve data)
		if len(self.slotPars) > current_num_banks:
			self.slotPars = self.slotPars[:current_num_banks]
		
		if len(self.bankActiveSlots) > current_num_banks:
			self.bankActiveSlots = self.bankActiveSlots[:current_num_banks]
		
		# Validate current bank index
		if self.currBank >= current_num_banks:
			self.currBank = 0
			self.activeSlot = None
		
		# Validate each bank's slots
		for _bank_idx in range(len(self.slotPars)):
			bank_slots = self.slotPars[_bank_idx]
			if not isinstance(bank_slots, list):
				self.slotPars[_bank_idx] = []
				continue
				
			for idx, _par_or_group in enumerate(bank_slots):
				if _par_or_group is not None:
					# Handle ParGroup
					if ParameterValidator.is_pargroup(_par_or_group):
						# Check if any parameters in the group are still valid
						has_valid = any(p.valid for p in _par_or_group if p is not None)
						if not has_valid:
							self.slotPars[_bank_idx][idx] = None
							if self.currBank == _bank_idx and self.activeSlot == idx:
								# Invalidate active slot
								self.activeSlot = None
								self.bankActiveSlots[_bank_idx] = None
					# Handle single Par
					elif not _par_or_group.valid:
						self.slotPars[_bank_idx][idx] = None
						if self.currBank == _bank_idx and self.activeSlot == idx:
							# Invalidate active slot
							self.activeSlot = None
							self.bankActiveSlots[_bank_idx] = None
	
	def _initialize_VSN1(self):
		"""Initialize VSN1 screen if enabled"""
		if not self.evalVsn1support:
			return
			
		self.display_manager.clear_screen()
		if self.activePar is not None:
			self.display_manager.update_parameter_display(self.activePar, force_knob_leds=True)
		else:
			self.display_manager.update_all_display(0, 0, 1, ScreenMessages.HOVER, 
													ScreenMessages.HOVER, compress=False)

		self.display_manager.update_all_slot_leds()
		self.display_manager.set_stepmode_indicator(self.stepMode)
		
		# Initialize UI button labels based on current slot assignments
		if hasattr(self, 'ui_manager'):
			# Set bank indicator
			self.display_manager.set_bank_indicator(self.currBank)
		
		# Set initial outline color based on current state
		if self.activeSlot is not None:
			self.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)  # Active slot
		else:
			self.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)  # Hover mode

		if self.knobLedUpdateMode in [KnobLedUpdateMode.STEPS]:
			step_idx = next((i for i, s in enumerate(self.seqSteps) if s.par.Step.eval() == self._currStep), 0)
			self.vsn1_manager.update_knob_leds_steps(step_idx)

		self.display_manager.update_all_display(1, 0, 1, 'TD Hover', '_INIT_', compress=False)
		
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
	def seqBanks(self):
		return self.ownerComp.seq.Banks

	@property
	def numBanks(self):
		return self.seqBanks.numBlocks

	@property
	def numSlots(self):
		return self.seqSlots.numBlocks

	@property
	def numSteps(self):
		return self.seqSteps.numBlocks

	@property
	def activePar(self) -> Optional[Union[Par, ParGroup]]:
		"""Get currently active parameter (slot takes priority over hovered)
		Can return a single Par or a ParGroup"""
		# Prioritize active slot parameters over hovered parameter
		if (self.activeSlot is not None and 
			self.activeSlot < self.numSlots and 
			self.currBank < self.numBanks and
			self.currBank < len(self.slotPars) and
			self.activeSlot < len(self.slotPars[self.currBank]) and
			self.slotPars[self.currBank][self.activeSlot] is not None):
				return self.slotPars[self.currBank][self.activeSlot]
			
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

	@property
	def secondaryMode(self) -> SecondaryMode:
		"""Get the current secondary mode from component parameter"""
		return SecondaryMode(self.evalSecondarymode)

	@property
	def secondaryPushState(self) -> bool:
		"""Get the current push state from component parameter"""
		return self.ownerComp.op('null_push')[0].eval()

	@property
	def stepMode(self) -> StepMode:
		"""Get the current relative step mode from component parameter"""
		return StepMode(self.evalStepmode)

	@stepMode.setter
	def stepMode(self, value: StepMode):
		self.evalStepmode = value.value

# endregion properties

# region helper methods

	def _manage_empty_operator_display(self, should_show: bool):
		"""Manage the delayed display message when no operator is hovered.
		
		Args:
			should_show: True to show the empty operator message, False to kill it
		"""
		if should_show:
			# Check if we need to show the empty operator message
			should_run = True
			try:
				should_run = self.display_run_obj is None or not self.display_run_obj.active
			except (AttributeError, tdError):
				pass
			
			if should_run:
				self.display_run_obj = run(
					"args[0].display_manager.update_all_display(0, 0, 1, 'TD Hover', args[1], compress=False)", 
					self, ScreenMessages.UNSUPPORTED, delayMilliSeconds=1000, delayRef=op.TDResources
				)
		else:
			# Kill any existing display run when we have a valid operator
			try:
				if self.display_run_obj is not None and self.display_run_obj.active:
					self.display_run_obj.kill()
			except (AttributeError, tdError):
				pass
	
# endregion helper methods

	def onHoveredParChange(self, _op, _parGroup, _par, _expr, _bindExpr):
		"""TouchDesigner callback when hovered parameter changes"""
		# Clear any captured initial values that never resulted in undo actions
		# (user hovered but didn't adjust)
		if self.hoveredPar is not None and self.evalEnableundo:
			self.undo_manager.on_parameter_unhovered(self.hoveredPar)
		
		self.hoveredPar = None

		if not self.evalActive:
			return

		if _op is None:
			# Only show empty operator message if we don't have an active valid parameter
			# (activePar already checks for active slot with valid parameter)
			has_active_param = self.activePar is not None and self.activePar.valid
			self._manage_empty_operator_display(should_show=not has_active_param)
			return
		else:
			self._manage_empty_operator_display(should_show=False)
		
		if not (_op := op(_op)):
			return
		
		# Detect if we're hovering over a ParGroup or a single Par
		par_group_obj = getattr(_op.parGroup, _parGroup, None) if _parGroup else None
		single_par = getattr(_op.par, _par, None) if _par else None
		
		# ParGroup detected: parGroup exists AND par doesn't (or is None)
		if par_group_obj is not None and single_par is None:
			# Edge case: if ParGroup has only 1 parameter, treat it as a single Par
			try:
				par_list = list(par_group_obj)
				if len(par_list) == 1:
					# Single parameter in group - treat as individual Par
					single_par = par_list[0]
					par_group_obj = None  # Clear group reference
			except (TypeError, AttributeError):
				pass  # Can't convert to list, continue with group
			
			# Store as ParGroup if it has multiple parameters
			if par_group_obj is not None:
				self.hoveredPar = par_group_obj
				
				# Handle invalid/unsupported parameters when no active slot
				if self.activeSlot is None:
					if error_msg := ParameterValidator.get_validation_error(par_group_obj):
						self.display_manager.show_parameter_error(par_group_obj, error_msg)
						return  # Parameter group is invalid, error message shown
					
				# Capture initial values for undo when hovering
				self.undo_manager.on_parameter_hovered(par_group_obj)
				
				# Update screen if no active slot (only for valid parameter groups)
				self.display_manager.update_parameter_display(par_group_obj)
				return  # Early return to avoid processing as single par
		
		# Single Par detected (or extracted from single-item ParGroup)
		if single_par is not None:
			self.hoveredPar = single_par
			
			# Handle invalid/unsupported parameters when no active slot
			if self.activeSlot is None:
				if error_msg := ParameterValidator.get_validation_error(single_par):
					self.display_manager.show_parameter_error(single_par, error_msg)
					return  # Parameter is invalid, error message shown
			

		# Update screen if no active slot (only for valid parameters)
		if self.activeSlot is None:
			# Capture initial value for undo when hovering
			self.undo_manager.on_parameter_hovered(single_par)
			self.display_manager.update_parameter_display(single_par)

	def onGridConnect(self):
		"""TouchDesigner callback when grid connects"""
		self._initialize_VSN1()
	
	def onGridDisconnect(self):
		"""TouchDesigner callback when grid disconnects"""
		pass

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
			# Handle step change messages
			if self.midi_handler.handle_step_message(index, value):
				self._manage_empty_operator_display(should_show=False)
				return
				
			# Handle pulse messages
			if self.midi_handler.handle_push_message(index, value, active_par):
				self._manage_empty_operator_display(should_show=False)
				return
		
			# Handle slot selection messages
			if self.midi_handler.handle_slot_message(index, value):
				self._manage_empty_operator_display(should_show=False)
				return
			
		elif message == MidiConstants.CONTROL_CHANGE:
			# Handle knob control messages
			if self.midi_handler.handle_knob_message(index, value, active_par):
				self._manage_empty_operator_display(should_show=False)
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
			if hovered_par in [self.parPushindex]:
				hovered_par.val = index
				
			if hovered_par in self.seqSteps.blockPars.Index:
				hovered_par.val = index
				self._set_step_parameter(hovered_par.sequenceBlock)
				
			elif hovered_par in self.seqSlots.blockPars.Index:
				hovered_par.val = index

			elif hovered_par in self.seqBanks.blockPars.Index:
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

	def onResetPar(self, force: bool = False):
		"""TouchDesigner callback to reset active parameter (or ParGroup)"""
		if self.activePar is None:
			return
		
		if force or self.secondaryMode == SecondaryMode.RESET:
			# Handle ParGroup
			if ParameterValidator.is_pargroup(self.activePar):
				self.undo_manager.create_reset_undo_for_pargroup(self.activePar)
			else:
				# Handle single Par
				self.undo_manager.create_reset_undo_for_parameter(self.activePar)
			
			self.display_manager.update_parameter_display(self.activePar)

	def onSetDefault(self):
		"""TouchDesigner callback to set default parameter value"""
		if self.activePar is None or not self.activePar.isCustom:
			return
		self.activePar.default = self.activePar.eval()
		# update display
		self.display_manager.update_parameter_display(self.activePar)

	def onSetNorm(self, min_max: str):
		"""TouchDesigner callback to set norm min or max value"""
		if self.activePar is None or not self.activePar.isCustom:
			return
		if min_max == 'min':
			_val = self.activePar.eval()
			if _val != self.activePar.normMax:
				self.activePar.normMin = _val
				self.activePar.min = _val
		else:
			_val = self.activePar.eval()
			if _val != self.activePar.normMin:
				self.activePar.normMax = _val
				self.activePar.max = _val
		# update display
		self.display_manager.update_parameter_display(self.activePar)

	def onSetClamp(self, min_max: str):
		"""TouchDesigner callback to set clamp min or max value"""
		if self.activePar is None or not self.activePar.isCustom:
			return
		if min_max == 'min' or min_max == 'both':
			self.activePar.clampMin = not self.activePar.clampMin
		if min_max == 'max' or min_max == 'both':
			self.activePar.clampMax = not self.activePar.clampMax


	def onReceiveMidiBankSel(self, index: int) -> None:
		"""TouchDesigner callback for bank selection MIDI input"""
		if not self.evalActive:
			return

		# Handle bank change message
		self.midi_handler.handle_bank_message(index)

	def onReceiveModeSel(self):
		"""TouchDesigner callback for mode selection MIDI input"""
		if not self.evalActive:
			return
		# set step mode to the opposite of the current step mode
		self.stepMode = StepMode.FIXED if self.stepMode == StepMode.ADAPTIVE else StepMode.ADAPTIVE
				

# endregion midi callbacks

# region helper functions

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
	
# endregion helper functions
# region parameter callbacks

	def onParActive(self, val):
		if val:
			self.postInit()
		else:
			self.ui_manager.set_hovered_ui_color(-1)
			self.vsn1_manager.clear_all_slot_leds()
			self.display_manager.clear_screen()


	def onParClear(self):
		"""TouchDesigner callback to clear all MIDI mappings"""
		# Clear all slot LEDs before resetting
		self.vsn1_manager.clear_all_slot_leds()
		
		# Reset sequence blocks
		self.seqSteps.numBlocks = 1
		self.seqSteps[0].par.Index = ''
		self.seqSteps[0].par.Step.val = 0.001
		
		self.seqSlots.numBlocks = 1
		self.seqSlots[0].par.Index = ''
		
		# Clear MIDI indices
		self.parKnobindex.val = ''
		self.parPushindex.val = ''
		
		# Reset active slot
		self.activeSlot = None
		
		# Force cook MIDI operators
		self._force_cook_midi_operators()

	# TODO: These can be optimized using Dependency objects
	def onSeqStepsNIndex(self, _par, idx):
		"""TouchDesigner callback when sequence steps index changes"""
		self._force_cook_midi_operators()

	def onSeqSlotsNIndex(self, _par, idx):
		"""TouchDesigner callback when sequence slots index changes"""
		self._force_cook_midi_operators()

	def onSeqBanksNIndex(self, _par, idx):
		"""TouchDesigner callback when sequence banks index changes"""
		self._force_cook_midi_operators()

	def onParKnobindex(self, _par, _val):
		"""TouchDesigner callback when knob index parameter changes"""
		self._force_cook_midi_operators()

	def onParKnobledupdate(self, _val):
		"""TouchDesigner callback when knob LED update mode parameter changes"""
		if KnobLedUpdateMode(_val) in [KnobLedUpdateMode.VALUE]:
			self.vsn1_manager.update_knob_leds_steps(-1)
			self.display_manager.update_parameter_display(self.activePar, force_knob_leds=True)
		elif KnobLedUpdateMode(_val) in [KnobLedUpdateMode.OFF]:
			self.vsn1_manager.update_knob_leds_gradual(0)
			self.vsn1_manager.update_knob_leds_steps(-1)
		else:#
			step_idx = next((i for i, s in enumerate(self.seqSteps) if s.par.Step.eval() == self._currStep), None)
			self.vsn1_manager.update_knob_leds_gradual(0)
			self.vsn1_manager.update_knob_leds_steps(step_idx)

	def onParVsn1support(self, _par, _val):
		"""TouchDesigner callback when VSN1 support parameter changes"""
		if _val:
			self.ownerComp.par.Resetcomm.pulse()

	def onParUsedefaultsforvsn1(self):
		"""TouchDesigner callback to set VSN1 hardware defaults"""
		# Set default channel
		self.evalChannel = VSN1Constants.CHANNEL
		# Configure step buttons with their respective step values
		self.seqSteps.numBlocks = len(VSN1Constants.STEP_BUTTONS)
		for i, (button, step) in enumerate(VSN1Constants.STEP_BUTTONS.items()):
			self.seqSteps[i].par.Index.val = button
			self.seqSteps[i].par.Step.val = step

		# Configure bank buttons
		self.seqBanks.numBlocks = len(VSN1Constants.BANK_BUTTONS)
		for i, button in enumerate(VSN1Constants.BANK_BUTTONS):
			self.seqBanks[i].par.Index.val = button

		# Configure slot indices
		self.seqSlots.numBlocks = len(VSN1Constants.SLOT_INDICES)
		for i, index in enumerate(VSN1Constants.SLOT_INDICES):
			self.seqSlots[i].par.Index.val = index

		# Set control indices
		self.parKnobindex.val = VSN1Constants.KNOB_INDEX
		self.parPushindex.val = VSN1Constants.PUSH_INDEX

		# Force cook MIDI operators
		self._force_cook_midi_operators()

	def onParColorhoveredui(self, _val):
		if _val and self.activeSlot is None:
			self.ui_manager.set_hovered_ui_color(self.evalColorindex-1)
		else:
			self.ui_manager.set_hovered_ui_color(-1)

	def onParColorindex(self, _val):
		if self.activeSlot is None and self.evalColorhoveredui:
			self.ui_manager.set_hovered_ui_color(self.evalColorindex-1)
		else:
			self.ui_manager.set_hovered_ui_color(-1)

	def _force_cook_midi_operators(self):
		"""Force cook all MIDI-related operators"""		
		activeMidi = self.ownerComp.op('midiin_active')
		pushMidi = self.ownerComp.op('midiin_push')
		slotsLearnMidi = self.ownerComp.op('midiin_slots')
		bankMidi = self.ownerComp.op('midiin_bank')
		modeselMidi = self.ownerComp.op('midiin_modesel')
		resetparMidi = self.ownerComp.op('midiin_resetpar')
		defaultMidi = self.ownerComp.op('midiin_default')
		setnormMinMidi = self.ownerComp.op('midiin_setnormmin')
		setnormMaxMidi = self.ownerComp.op('midiin_setnormmax')
		activeMidi.cook(force=True)
		pushMidi.cook(force=True)
		slotsLearnMidi.cook(force=True)
		bankMidi.cook(force=True)
		modeselMidi.cook(force=True)
		resetparMidi.cook(force=True)
		defaultMidi.cook(force=True)
		setnormMinMidi.cook(force=True)
		setnormMaxMidi.cook(force=True)

	def onSeqBanksNumBlocks(self, _par, _val):
		"""TouchDesigner callback when number of banks changes"""
		# Revalidate storage to handle bank count changes
		self._validate_storage()
		
		# If current bank is now invalid, switch to bank 0
		if self.currBank >= self.numBanks:
			self.slot_manager.recall_bank(0)
		else:
			# Refresh current bank display to ensure UI is updated
			self.slot_manager._refresh_bank_display()

	def onParStepmode(self, _par, _val):
		"""TouchDesigner callback when relative step mode parameter changes"""
		self.display_manager.set_stepmode_indicator(StepMode(_val))

	def onParShowbuiltin(self, _val):
		self.ownerComp.showCustomOnly  = not _val

# endregion parameter callbacks
	def onProjectPreSave(self):
		"""TouchDesigner callback when project is pre-saved"""
		# Validate all banks and all slot parameters
		for bank_idx in range(len(self.slotPars)):
			for slot_idx in range(len(self.slotPars[bank_idx])):
				par = self.slotPars[bank_idx][slot_idx]
				if par is not None and not par.valid:
					# Clear invalid parameters silently during save
					self.slot_manager.clear_slot_in_bank(slot_idx, bank_idx)
# endregion
