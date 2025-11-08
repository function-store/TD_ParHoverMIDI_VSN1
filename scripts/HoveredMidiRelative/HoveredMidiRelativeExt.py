'''Info Header Start
Name : HoveredMidiRelativeExt
Author : Dan@DAN-4090
SavSaveversion : 2023.12120
 Header End'''
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
from ui_manager import UIManager
from undo_manager import UndoManager
from repo_manager import RepoManager



class HoveredMidiRelativeExt:
	"""
	TouchDesigner Extension for MIDI-controlled relativeparameter manipulation with VSN1 screen support
	"""
	
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		
		# Initialize TD operators
		self.midiOut = self.ownerComp.op('midiout1')
		self.jumpToOp : JumpToOpExt = self.ownerComp.op('JumpToOp')
		self.websocket: websocketDAT = self.ownerComp.op('websocket1')
		self.popDialog : PopDialogExt = self.ownerComp.op('popDialog')

		# UI Mod init
		if _uimod := self.ownerComp.op('td_ui_mod'):
			if hasattr(_uimod, 'Install'):
				try:
					_uimod.Install()
				except Exception as error:
					pass
		
		# Initialize state - can be either a single Par or a ParGroup
		self.hoveredPar: Optional[Union[Par, ParGroup]] = None
		self._activeSlotPar: Optional[Union[Par, ParGroup]] = None  # Direct storage of active slot parameter
		
		# Initialize helper classes
		self.repo_manager = RepoManager(self)  # Initialize first as others may depend on it
		self.midi_handler = MidiMessageHandler(self)
		self.ui_manager = UIManager(self)
		self.display_manager = DisplayManager(self)  # Must be after ui_manager
		self.slot_manager = SlotManager(self)
		self.undo_manager = UndoManager(self)

		self.display_run_obj = None
		self.lastCachedChange = None
		self.slotPars = [[None for _ in range(self.numSlots)] for _ in range(self.numBanks)]
		self.bankActiveSlots = [None for _ in range(self.numBanks)]

		# Initialize storage (back to using slotPars and bankActiveSlots for performance)
		storedItems = [
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
				'name': 'currentHoveredUIColor',
				'default': -1,
				'readOnly': False,
				'property': True,
				'dependable': False
			}
		]


		self.stored = StorageManager(self, ownerComp, storedItems)
		
		# Load from tables on first run 
		self.repo_manager.load_from_tables_if_needed()

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
		run("args[0].onMidiError(args[1])", self, self.midiError, delayRef=op.TDResources, delayFrames=5)

	def onStart(self):
		if self.evalAutostartgrideditor:
			self._start_grid_editor()

		post_update = self.ownerComp.fetch('post_update', False)
		if post_update:
			#self.LoadAllFromJSON()
			self.ownerComp.unstore('post_update')
			# okay I really fucked this up, so mega-hack below
			#self.SaveAllToJSON()
			try:
				run(
					"args[0].open_changelog() if args[0] "
							"and hasattr(args[0], 'open_changelog') else None",
					self,
					endFrame=True,
					delayRef=op.TDResources
				)
			except:
				pass

	def open_changelog(self):
		try:
			ret = ui.messageBox(f'{self.ownerComp.name} updated', 'Would you like to see the changelog?', buttons=['No', 'Yes'])
			if ret == 1:
				ui.viewFile('https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest')
		except:
			pass

		

	def _start_grid_editor(self):
		import subprocess
		import os
		import sys

		try:
			if sys.platform == "win32":
				# Windows implementation
				result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Grid Editor.exe'],
										capture_output=True, text=True, shell=True)
				if 'Grid Editor.exe' not in result.stdout:
					# Try common Windows installation paths
					possible_paths = [
						os.path.expandvars(r"%LOCALAPPDATA%\Programs\grid-editor\Grid Editor.exe"),
						os.path.expandvars(r"%PROGRAMFILES%\Grid Editor\Grid Editor.exe"),
						os.path.expandvars(r"%PROGRAMFILES(X86)%\Grid Editor\Grid Editor.exe"),
						r"C:\Program Files\Grid Editor\Grid Editor.exe",
						r"C:\Program Files (x86)\Grid Editor\Grid Editor.exe"
					]
					
					grid_editor_path = None
					for path in possible_paths:
						if os.path.exists(path):
							grid_editor_path = path
							break
					
					if grid_editor_path:
						subprocess.Popen([grid_editor_path])
						debug("Grid Editor started from:", grid_editor_path)
					else:
						debug("Grid Editor executable not found. Tried paths:", possible_paths)
				else:
					debug("Grid Editor is already running")

			elif sys.platform == "darwin":
				# macOS implementation
				result = subprocess.run(['pgrep', '-f', 'Grid Editor'],
										capture_output=True, text=True)
				if result.returncode != 0:  # Process not found
					# Try common macOS application paths
					possible_paths = [
						"/Applications/Grid Editor.app",
						os.path.expanduser("~/Applications/Grid Editor.app"),
						"/Applications/grid-editor/Grid Editor.app",
						os.path.expanduser("~/Applications/grid-editor/Grid Editor.app")
					]

					app_path = None
					for path in possible_paths:
						if os.path.exists(path):
							app_path = path
							break

					if app_path:
						subprocess.Popen(["open", app_path])
						debug("Grid Editor started")
					else:
						debug("Grid Editor application not found in common locations:", possible_paths)
				else:
					debug("Grid Editor is already running")

			else:
				debug("Grid Editor launch not supported on this platform:", sys.platform)

		except Exception as e:
			debug("Error checking/starting Grid Editor:", str(e))
		return

	def _validate_storage(self):
		"""Validate storage and ensure proper structure for dynamic bank changes"""
		# Ensure storage has correct dimensions for current numBanks/numSlots
		# Resize slotPars if needed (preserve existing data where possible)
		if len(self.slotPars) != self.numBanks:
			old_slotPars = self.slotPars
			self.slotPars = [[None for _ in range(self.numSlots)] for _ in range(self.numBanks)]
			
			# Copy over existing data
			for bank_idx in range(min(len(old_slotPars), self.numBanks)):
				for slot_idx in range(min(len(old_slotPars[bank_idx]), self.numSlots)):
					self.slotPars[bank_idx][slot_idx] = old_slotPars[bank_idx][slot_idx]
		else:
			# Check if slot count changed
			for bank_idx in range(self.numBanks):
				if len(self.slotPars[bank_idx]) != self.numSlots:
					old_slots = self.slotPars[bank_idx]
					self.slotPars[bank_idx] = [None for _ in range(self.numSlots)]
					# Copy over existing data
					for slot_idx in range(min(len(old_slots), self.numSlots)):
						self.slotPars[bank_idx][slot_idx] = old_slots[slot_idx]
		
		# Resize bankActiveSlots if needed
		if len(self.bankActiveSlots) != self.numBanks:
			old_active = self.bankActiveSlots
			self.bankActiveSlots = [None for _ in range(self.numBanks)]
			# Copy over existing active slots
			for bank_idx in range(min(len(old_active), self.numBanks)):
				self.bankActiveSlots[bank_idx] = old_active[bank_idx]
		
		# Validate current bank index
		if self.currBank >= self.numBanks:
			self.currBank = 0
			self.activeSlot = None
			self._activeSlotPar = None
		
		# Validate all parameters in all banks and clear invalid ones
		self.repo_manager.validate_and_clean_all_banks()
		
		# Sync activeSlot with bankActiveSlots
		active_slot_idx = self.bankActiveSlots[self.currBank]
		if active_slot_idx is not None:
			self.activeSlot = active_slot_idx
			self._activeSlotPar = self.slotPars[self.currBank][active_slot_idx]
		else:
			self.activeSlot = None
			self._activeSlotPar = None
	
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
			self.display_manager.update_knob_leds_steps(step_idx)
		
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
		Can return a single Par or a ParGroup
		
		For performance, active slot parameter is stored directly in _activeSlotPar
		when a slot is activated, avoiding list lookups during MIDI handling.
		"""
		# Prioritize active slot parameter (stored directly for fast access)
		if self._activeSlotPar is not None:
			return self._activeSlotPar
			
		if self.hoveredPar is not None:
			return self.hoveredPar
			
		return None
	
	def should_allow_strmenus(self, par_to_check: Union[Par, ParGroup] = None) -> bool:
		"""Check if StrMenu parameters should be allowed
		
		StrMenus are allowed if:
		1. The global evalControlstrmenus flag is enabled, OR
		2. The parameter being checked is from an active slot (user explicitly assigned it)
		
		Args:
			par_to_check: Optional parameter to check. If None, checks the active parameter.
		
		Returns:
			True if StrMenus should be allowed for this parameter
		"""
		# Global flag enabled - allow StrMenus everywhere
		if self.evalControlstrmenus:
			return True
		
		# Check if parameter is from an active slot
		if self.activeSlot is not None and self._activeSlotPar is not None:
			# If no specific parameter provided, check the active one
			if par_to_check is None:
				par_to_check = self._activeSlotPar
			
			# Check if it's the active slot parameter (single Par)
			if par_to_check is self._activeSlotPar:
				return True
			
			# Check if it's part of an active slot ParGroup
			if ParameterValidator.is_pargroup(self._activeSlotPar):
				for p in self._activeSlotPar:
					if p is par_to_check:
						return True
		
		return False

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
	def knobPushState(self) -> bool:
		"""Get the current push state from component parameter"""
		return self.ownerComp.op('null_push')[0].eval()

	@property
	def stepMode(self) -> StepMode:
		"""Get the current relative step mode from component parameter"""
		return StepMode(self.evalStepmode)

	@stepMode.setter
	def stepMode(self, value: StepMode):
		self.evalStepmode = value.value

	@property
	def midiError(self) -> bool:
		return self.ownerComp.op('info_midi1')['warnings'].eval()

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
					"args[0].display_manager.update_all_display(0, 0, 1, args[1], args[1], compress=False)", 
					self, ScreenMessages.HOVER, delayMilliSeconds=1000, delayRef=op.TDResources
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
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return
		
		# Clear any captured initial values that never resulted in undo actions
		# (user hovered but didn't adjust)
		if self.hoveredPar is not None and self.evalEnableundo:
			self.undo_manager.on_parameter_unhovered(self.hoveredPar)
		
		self.hoveredPar = None

		if not self.evalActive or self.midiError:
			return

		if _op is None:
			# Only show empty operator message if we don't have an active valid parameter
			# (activePar already checks for active slot with valid parameter)
			has_active_param = self.activePar is not None and self.activePar.valid
			if not has_active_param:
				self._set_parexec_pars(None)
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
					if error_msg := ParameterValidator.get_validation_error(par_group_obj, self.evalControlstrmenus):
						self._set_parexec_pars(None)
						self.display_manager.show_parameter_error(par_group_obj, error_msg)
						return  # Parameter group is invalid, error message shown
					
				self._set_parexec_pars(None)
				# set first valid 
				# Capture initial values for undo when hovering
				self.undo_manager.on_parameter_hovered(par_group_obj)
				
				
				# Update screen if no active slot (only for valid parameter groups)
				if self.activeSlot is None:
					self.display_manager.update_parameter_display(par_group_obj)
				return  # Early return to avoid processing as single par
		
		# Single Par detected (or extracted from single-item ParGroup)
		if single_par is not None:
			self.hoveredPar = single_par
			
			# Handle invalid/unsupported parameters when no active slot
			if self.activeSlot is None:
				if error_msg := ParameterValidator.get_validation_error(single_par, self.evalControlstrmenus):
					self.display_manager.show_parameter_error(single_par, error_msg)
					if error_msg == ScreenMessages.EXPR:
						self._set_parexec_pars(single_par)
					return  # Parameter is invalid, error message shown
			

		# Update screen if no active slot (only for valid parameters)
		if self.activeSlot is None:
			# Capture initial value for undo when hovering
			self._set_parexec_pars(single_par)
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
		
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return
		
		try:
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
		except Exception as e:
			# Catch invalid parameter errors at top level
			if 'Invalid Par' not in str(e) and 'tdError' not in str(type(e).__name__):
				raise  # Re-raise unexpected errors
			
			# Queue up invalid parameters for sequential dialog-based recovery
			# This will show one dialog at a time, wait for response, then show the next
			self.slot_manager.queue_invalidation_check()
			
			# Clear invalid hovered parameter
			try:
				if self.hoveredPar and not self.hoveredPar.valid:
					self.hoveredPar = None
			except:
				self.hoveredPar = None


	def onReceiveMidiLearn(self, dat, rowIndex, message, channel, index, value, input, byteData):
		"""TouchDesigner callback for MIDI learning mode"""
		if channel != self.evalChannel or not self.evalActive:
			return
		
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
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
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return
		
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
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return None
		
		if self.activePar is None:
			return None

		try:
			# Handle ParGroup
			if ParameterValidator.is_pargroup(self.activePar):
				self.undo_manager.create_reset_undo_for_pargroup(self.activePar)
			else:
				# Handle single Par
				self.undo_manager.create_reset_undo_for_parameter(self.activePar)
			
			self.display_manager.update_parameter_display(self.activePar)
		except:
			# Parameter became invalid - queue invalidation check
			self.slot_manager.queue_invalidation_check()

	def onSetDefault(self):
		"""TouchDesigner callback to set default parameter value"""
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return None
		
		if self.activePar is None:
			return None
		
		try:
			if not self.activePar.isCustom:
				return None
			
			# Capture old value for undo
			old_default = self.activePar.default
			new_default = self.activePar.eval()
			
			# Apply the change
			self.activePar.default = new_default
			
			# Create undo action
			self.undo_manager.create_set_default_undo(self.activePar, old_default, new_default)
			
			# update display
			self.display_manager.update_parameter_display(self.activePar, bottom_text = '_DEF_')
		except:
			# Parameter became invalid - queue invalidation check
			self.slot_manager.queue_invalidation_check()

	def onSetNorm(self, min_max: str):
		"""TouchDesigner callback to set norm min or max value"""
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return None
		
		if self.activePar is None:
			return None
		
		try:
			if not self.activePar.isCustom:
				return None
			
			_val = self.activePar.eval()
			
			if min_max == 'min':
				# Check if valid (not equal to max)
				if _val != self.activePar.normMax:
					# Capture old values for undo
					old_norm = self.activePar.normMin
					old_minmax = self.activePar.min
					
					# Apply changes
					self.activePar.normMin = _val
					self.activePar.min = _val
					
					# Create undo action
					self.undo_manager.create_set_norm_undo(
						self.activePar, is_min=True,
						old_norm=old_norm, new_norm=_val,
						old_minmax=old_minmax, new_minmax=_val
					)
			else:
				# Check if valid (not equal to min)
				if _val != self.activePar.normMin:
					# Capture old values for undo
					old_norm = self.activePar.normMax
					old_minmax = self.activePar.max
					
					# Apply changes
					self.activePar.normMax = _val
					self.activePar.max = _val
					
					# Create undo action
					self.undo_manager.create_set_norm_undo(
						self.activePar, is_min=False,
						old_norm=old_norm, new_norm=_val,
						old_minmax=old_minmax, new_minmax=_val
					)
			
			# update display
			self.display_manager.update_parameter_display(self.activePar, bottom_text=f'_{min_max.upper()}_')
		except:
			# Parameter became invalid - queue invalidation check
			self.slot_manager.queue_invalidation_check()

	def onSetClamp(self, min_max: str):
		"""TouchDesigner callback to set clamp min or max value"""
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return None
		
		if self.activePar is None:
			return None
		
		try:
			if not self.activePar.isCustom:
				return None
			
			# Capture old values for undo
			old_clamp_min = self.activePar.clampMin
			old_clamp_max = self.activePar.clampMax
			
			# Determine what's changing
			changed_min = (min_max == 'min' or min_max == 'both')
			changed_max = (min_max == 'max' or min_max == 'both')
			
			# Apply changes
			if changed_min:
				self.activePar.clampMin = not self.activePar.clampMin
			if changed_max:
				self.activePar.clampMax = not self.activePar.clampMax
			
			# Create undo action
			self.undo_manager.create_set_clamp_undo(
				self.activePar,
				changed_min=changed_min,
				changed_max=changed_max,
				old_clamp_min=old_clamp_min,
				new_clamp_min=self.activePar.clampMin,
				old_clamp_max=old_clamp_max,
				new_clamp_max=self.activePar.clampMax
			)
			
			# update display
			self.display_manager.update_parameter_display(self.activePar, bottom_text='_CLAMP_')
		except:
			# Parameter became invalid - queue invalidation check
			self.slot_manager.queue_invalidation_check()


	def onReceiveMidiBankSel(self, index: int) -> None:
		"""TouchDesigner callback for bank selection MIDI input"""
		if not self.evalActive:
			return
		
		# Block all actions while invalidation is active (dialog or queue processing)
		if self.slot_manager.is_invalidation_active():
			return

		# Handle bank change message
		self.midi_handler.handle_bank_message(index)

	def onReceiveModeSel(self):
		"""TouchDesigner callback for mode selection MIDI input"""
		if not self.evalActive:
			return
		# set step mode to the opposite of the current step mode
		self.stepMode = StepMode.FIXED if self.stepMode == StepMode.ADAPTIVE else StepMode.ADAPTIVE

	def onCustomOpen(self):
		"""TouchDesigner callback when custom parameter is opened"""
		if not self.evalActive:
			return
			
		self.onReceiveModeSel() # we "undo" since this action is a long press of that
		# check if par group
		if (activePar := self.activePar) is None:
			# get selected OP
			_pane = ui.panes.current
			if _pane.type == PaneType.NETWORKEDITOR:
				_parent = _pane.owner
				_currentChild = _parent.currentChild
				if _currentChild and _currentChild.isCOMP:
					ui.openCOMPEditor(_currentChild)
					self.display_manager.update_all_display(0, 0, 1, _currentChild.name, display_text='_CUSTOM_')
			return
		if not activePar.isCustom:
			return
		if ParameterValidator.is_pargroup(activePar):
			activePar = activePar[0]
		self.ui_manager.open_comp_editor(activePar)
		run("args[0].display_manager.update_parameter_display(args[1], bottom_text='_CUSTOM_')", self, activePar, delayFrames=1)

	def onActiveValueChange(self, _par):
		try:
			# check if _par is a cached parameter and if the value matches the cached value do nothing
			if isinstance(_par, ParGroup):
				return None

			# Check if parameter is part of an active slot ParGroup
			if (self.activeSlot is not None and
				self.activePar is not None and
				ParameterValidator.is_pargroup(self.activePar)):
				# Check if _par is in the active ParGroup
				for par_in_group in self.activePar:
					if par_in_group.owner == _par.owner and par_in_group.name == _par.name:
						return None

			if self.lastCachedChange:#
				if f'{_par.owner.path}:{_par.name}' == self.lastCachedChange[0] and _par.eval() == self.lastCachedChange[1]:
					return None

			# update display with the new value
			self.display_manager.update_parameter_display(_par)
		except:
			# Parameter became invalid - queue invalidation check
			self.slot_manager.queue_invalidation_check()

	def _set_parexec_pars(self, _par: Par):
		"""For god knows what reason Dependency objects would not update!!!"""
		parExec = self.ownerComp.op('parexec2')
		parExec.par.op = _par.owner if _par is not None else None
		try:
			parExec.par.pars = _par.name if _par is not None else ''
		except Exception as e:
			parExec.par.pars = None
		parExec.cook(force=True)

	def onMidiError(self, isError: bool):
		if not self.evalActive:
			return
		if isError and 'MIDI' not in self.ownerComp.op('midiin_active').warnings():
			isError = False

		self.ownerComp.par.Midistatus.val = not isError
		if isError:
			# display midi error message
			self.display_manager.update_all_display(0, 0, 1, ScreenMessages.MIDI_ERROR, ScreenMessages.MIDI_ERROR)
		else:
			if self.activePar is not None:
				# update display with current parameter
				self.display_manager.update_parameter_display(self.activePar)
			else:
				# display default hover message
				self.display_manager.update_all_display(1, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER)
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
			self.display_manager.clear_all_slot_leds()
			self.display_manager.clear_screen()

	def onParMidistatus(self, val):
		if val:
			self.ownerComp.clearScriptErrors()

	def onParSlotsreporepo(self, val):
		# after slots repo changes, clear old data and load from new repo
		# Clear stored slotPars and bankActiveSlots to invalidate old data
		num_banks = self.numBanks
		num_slots = self.numSlots
		self.slotPars = [[None for _ in range(num_slots)] for _ in range(num_banks)]
		self.bankActiveSlots = [None for _ in range(num_banks)]
		self.activeSlot = None

		# Clear any cached active parameter
		if hasattr(self, '_activeSlotPar'):
			self._activeSlotPar = None

		# Now load from the new repo's tables
		self.repo_manager.load_from_tables()
		self.postInit()

	def onParStartgrideditor(self):
		self._start_grid_editor()

	def onParAutostartgrideditor(self, val):
		if val:
			self._start_grid_editor()


	def onParClear(self):
		"""TouchDesigner callback to clear all MIDI mappings"""
		# Clear all slot LEDs before resetting
		self.display_manager.clear_all_slot_leds()
		
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
			self.display_manager.update_knob_leds_steps(-1)
			self.display_manager.update_parameter_display(self.activePar, force_knob_leds=True)
		elif KnobLedUpdateMode(_val) in [KnobLedUpdateMode.OFF]:
			self.display_manager.update_knob_leds_gradual(0)
			self.display_manager.update_knob_leds_steps(-1)
		else:#
			step_idx = next((i for i, s in enumerate(self.seqSteps) if s.par.Step.eval() == self._currStep), None)
			self.display_manager.update_knob_leds_gradual(0)
			self.display_manager.update_knob_leds_steps(step_idx)

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
		setnormMinMidi = self.ownerComp.op('midiin_normmin')
		setnormMaxMidi = self.ownerComp.op('midiin_normmax')
		setclampMidi = self.ownerComp.op('midiin_setclamp')
		activeMidi.cook(force=True)
		pushMidi.cook(force=True)
		slotsLearnMidi.cook(force=True)
		bankMidi.cook(force=True)
		modeselMidi.cook(force=True)
		resetparMidi.cook(force=True)
		defaultMidi.cook(force=True)
		setnormMinMidi.cook(force=True)
		setnormMaxMidi.cook(force=True)
		setclampMidi.cook(force=True)

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

	def onValueChange(self, _par, _val):
		"""Generic TouchDesigner callback when parameter value changes"""
		if 'holdlength' in _par.name and 'Slot' not in _par.name:
			self.ownerComp.par.Bankswitchholdlength.val = max(self.ownerComp.par.Customizeholdlength.eval(), self.ownerComp.par.Resetholdlength.eval(), self.ownerComp.par.Minmaxclampholdlength.eval()) + 0.01
			
# endregion parameter callbacks
	def onProjectPreSave(self):
		"""TouchDesigner callback when project is pre-saved"""
		# Save runtime storage to tables for persistence
		self.repo_manager.save_to_tables()
# endregion
