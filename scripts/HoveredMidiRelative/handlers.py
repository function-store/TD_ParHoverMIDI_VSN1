
'''Info Header Start
Name : handlers
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.187.toe
Saveversion : 2023.12120
Info Header End'''
from constants import MidiConstants, ScreenMessages, StepMode, PushStepMode, MultiAdjustMode
from validators import ParameterValidator
from typing import Union

class MidiMessageHandler:
	"""Handles MIDI message processing logic"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext

	@property
	def shortcutPressed(self) -> bool:
		"""Used for checking if a bank off message coincides with a shortcuts
		since by default these share the same MIDI button
		"""
		mode_buttons = [
			'null_setdefault',
			'null_midibank', 
			'null_modesel',
			'null_resetpar',
			'null_setnormmin',
			'null_setnormmax',
			'null_setclamp'
		]
		return any(self.parent.ownerComp.op(button)[0].eval() for button in mode_buttons)
	

	def _clear_invalid_parameter_from_slots(self, active_par: Union['Par', 'ParGroup']) -> None:
		"""Clear invalid parameter from all slots across all banks and show error message"""
		if active_par is None or active_par.valid:
			return
		
		# Show error message on displays
		self.parent.display_manager.show_parameter_error(active_par, ScreenMessages.INVALID)
		
		# Check all banks for this parameter and clear any slots containing it
		for bank_idx in range(self.parent.numBanks):
			slot_idx = self.parent.slot_manager.find_slot_for_parameter(active_par, bank_idx)
			if slot_idx is not None:
				# Clear the slot containing this invalid parameter
				self.parent.slot_manager.clear_slot_in_bank(slot_idx, bank_idx)
	
	def _create_undo_for_parameter(self, active_par: Union['Par', 'ParGroup']):
		"""Create undo action for parameter or ParGroup (only if initial value was captured).
		Also handles multi-operator editing by capturing all parameters being adjusted together.
		
		Args:
			active_par: The parameter or ParGroup to create undo for
		"""
		# Handle ParGroup - create single undo block for all parameters
		if ParameterValidator.is_pargroup(active_par):
			self.parent.undo_manager.create_pargroup_undo(active_par)
		else:
			# Handle single Par
			# Check if multi-operator editing is active (hover mode + multi-adjust enabled)
			if self.parent.activeSlot is None:  # hover mode
				multi_mode = self.parent.evalMultiadjustmode
				if multi_mode != MultiAdjustMode.OFF.value:
					# Get matching parameters from other selected operators
					matching_pars = ParameterValidator.get_matching_selected_pars(active_par)
					if matching_pars:
						# Create grouped undo for main + matching parameters
						self.parent.undo_manager.create_multi_parameter_undo(active_par, matching_pars)
						return
			
			# Normal single parameter undo
			self.parent.undo_manager.create_parameter_undo(active_par)
	
	def handle_step_message(self, index: int, value: int) -> bool:
		"""Handle step change messages"""
		blocks = self.parent._index_to_blocks(index, self.parent.seqSteps)
		if self.shortcutPressed:
			return True
		if not blocks:
			return False
			
		block = blocks[0]
		if self.parent.evalPushstepmode == PushStepMode.FIXED.value and self.parent.knobPushState:
			self.parent.ownerComp.par.Pushstep.val = block.par.Step.eval()
			return True
		if not (self.parent.knobPushState):
			if value == 0:
				self.parent._currStep = block.par.Step.eval()
		return True
	
	def handle_knob_message(self, index: int, value: int, active_par) -> bool:
		"""Handle knob control messages
		
		Note: Validation happens when parameter becomes active (hover/slot activation).
		For maximum performance, we skip validation during knob turns.
		"""
		knob_index = self.parent._safe_get_midi_index(self.parent.evalKnobindex, default=-1)
		if index != knob_index:
			return False


		
		# Only process actual knob movement (not center/idle position)
		if value == MidiConstants.MIDI_CENTER_VALUE:
			return True

		# Only check if parameter exists - it was validated on activation
		if active_par is None:
			# Delegate zoom handling to zoom_manager (if zoom is enabled)
			enable_zoom = getattr(self.parent, 'evalEnablezoom', False)
			if enable_zoom:
				return self.parent.zoom_manager.handle_zoom_knob(value)
			else:
				# No zoom, no active parameter - nothing to do
				self.parent.zoom_manager.clear_target()
				return False
		
		# Parameter is active - clear any zoom state
		self.parent.zoom_manager.clear_target()
		
		# Create undo action on first knob movement
		self._create_undo_for_parameter(active_par)
		
		# Apply parameter change
		self._do_step(self.parent._currStep, value)
		
		# Restart timeout on every movement (resets the 2s timer)
		# After 2s of inactivity, will clear captured values for new undo checkpoint
		self.parent.undo_manager.start_undo_timeout(timeout_ms=self.parent.evalUndotimeout*1000)
		
		return True
	
	def handle_push_message(self, index: int, value: int, active_par) -> bool:
		"""Handle pulse button messages"""
		push_index = self.parent._safe_get_midi_index(self.parent.evalPushindex, default=-1)
		if index != push_index:
			return False
			
		if hasattr(self, 'pushed_for_jump') and value == 0 and self.pushed_for_jump:
			self.pushed_for_jump = False
			return True

		# Only check if parameter exists - validity check will happen naturally via exception
		if active_par is None or (active_par.owner == self.parent.ownerComp):
			return False

		# Handle ParGroup
		if ParameterValidator.is_pargroup(active_par):
			# Check if any valid parameter is from ownerComp
			valid_pars = [p for p in active_par if p is not None and ParameterValidator.is_valid_parameter(p)]
			if not valid_pars:
				return False
			if any(p.owner == self.parent.ownerComp for p in valid_pars):
				return False
			
			error_msg = ParameterValidator.get_validation_error(active_par, self.parent.should_allow_strmenus(active_par))
			if error_msg:
				self.parent.display_manager.show_parameter_error(active_par, error_msg)
				return True  # Parameter group is invalid, error message shown
			
			# Apply push action to all valid parameters in group
			if value == MidiConstants.MAX_VELOCITY:
				for par in active_par:
					# Skip invalid parameters within the group
					if par is None or not ParameterValidator.is_valid_parameter(par):
						continue
					elif par.isMomentary:
						par.val = True
			if value == 0:
				for par in active_par:
					# Skip invalid parameters within the group
					if par is None or not ParameterValidator.is_valid_parameter(par):
						continue
					elif par.isMomentary:
						par.val = False
					elif par.isToggle:
						par.val = not par.eval()
					elif par.isPulse:
						par.pulse()
			self.parent.display_manager.update_parameter_display(active_par)
			return True
		
		# Handle single Par

		error_msg = ParameterValidator.get_validation_error(active_par, self.parent.should_allow_strmenus(active_par))
		if error_msg:
			self.parent.display_manager.show_parameter_error(active_par, error_msg)
			return True  # Parameter is invalid, error message shown
		
		# Apply push action to main parameter
		self._apply_push_to_parameter(active_par, value, is_main_parameter=True)
		
		if self.parent.activeSlot is None: # hover mode
			# Multi-operator editing: Apply same change to other selected operators of same type
			# Only in hover mode (not slot mode)
			mulit_mode = self.parent.evalMultiadjustmode
			# For push operations we actually don't care about the mode other than off... I think...
			if mulit_mode != MultiAdjustMode.OFF.value:
				matching_pars = ParameterValidator.get_matching_selected_pars(active_par)
				if matching_pars:
					for other_par in matching_pars:
						try:
							# Get the same parameter on the other operator
							if other_par is None or not ParameterValidator.is_valid_parameter(other_par):
								continue
							
							self._apply_push_to_parameter(other_par, value, is_main_parameter=False)
						except:
							# If any error occurs with one operator, continue with others
							continue
		
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
		
		currBank = self.parent.currBank
		
		# Check if slot exists and has a parameter in current bank
		active_par = self.parent.repo_manager.get_slot_parameter(block_idx, currBank)
		if active_par is not None:
			# Validate parameter before activating
			try:
				is_valid = active_par.valid
			except:
				is_valid = False
			
			if not is_valid:
				# Parameter is invalid - queue invalidation check to show recovery dialog
				self.parent.slot_manager.queue_invalidation_check()
				return False

			# check if user is holding down the push button
			if self.parent.knobPushState:
				_parOwner = active_par.owner
				if _parOwner is not None:
					self.parent.jumpToOp.Jump(_parOwner)
					self.pushed_for_jump = True
					_parOwner.currentPage = active_par.page
					if not self.parent.evalActivateonjump:
						return

			
			# Check for validation errors

			ret = self.parent.slot_manager.activate_slot(block_idx)			
			error_msg = ParameterValidator.get_validation_error(active_par, self.parent.should_allow_strmenus(active_par))
			if error_msg:
				self.parent.display_manager.show_parameter_error(active_par, error_msg)
			# Activate the slot using slot_manager
			return ret
		else:
			# Deactivate slot (return to hover mode) using slot_manager
			self.parent.slot_manager.deactivate_current_slot()
			return True

	def handle_bank_message(self, index: int) -> bool:
		"""Handle bank change messages"""
		blocks = self.parent._index_to_blocks(index, self.parent.seqBanks)
		if not blocks:
			return False
		
		block = blocks[0]
		bank_idx = block.index
		
		# Switch to the requested bank
		return self.parent.slot_manager.recall_bank(bank_idx)

	def _do_step(self, step: float, value: int):
		"""Apply step value to active parameter (or ParGroup) based on MIDI input"""
		active_par = self.parent.activePar
		if active_par is None:
			return
		
		# Handle ParGroup
		if ParameterValidator.is_pargroup(active_par):
			self._do_step_pargroup(active_par, step, value)
			return
		
		# Handle single Par
		self._do_step_single(active_par, step, value)
	
	def _do_step_pargroup(self, par_group: ParGroup, step: float, value: int):
		"""Apply step value to all valid parameters in a ParGroup
		Only applies to parameters that pass individual validation"""
		# Apply step to each valid parameter in the group
		for par in par_group:
			# Skip invalid parameters within the group
			# Also skip unit parameters (e.g., tunit, runit, sunit) but not "unit" itself
			if par is not None and not (par.name.endswith('unit') and len(par.name) > 4) and ParameterValidator.is_valid_parameter(par):
				self._do_step_single(par, step, value, update_display=False)
		
		# Update display once after all valid parameters are updated
		self.parent.display_manager.update_parameter_display(par_group)
	
	
	def _apply_step_to_parameter(self, par: Par, step: float, diff: int, update_cached_change: bool = False):
		"""Apply a step adjustment to a single parameter.
		
		Args:
			par: The parameter to adjust
			step: The step size
			diff: The direction and magnitude of change (value - MIDI_CENTER_VALUE)
			update_cached_change: Whether to update lastCachedChange (only for main parameter)
		"""
		if par.isNumber:
			# Calculate step amount based on mode
			if self.parent.stepMode == StepMode.FIXED:
				step_amount = step * diff
			else:  # Adaptive mode - step scales with parameter range
				min_val, max_val = par.normMin, par.normMax
				step_amount = ((max_val - min_val) * step) * diff
			
			# Handle integer parameters with different step behavior
			if par.isInt:
				if self.parent.stepMode == StepMode.FIXED:
					step_amount = 1 if diff > 0 else -1
				else:
					min_val, max_val = par.normMin, par.normMax
					step_amount = max(1, ((max_val - min_val) * step)) * (1 if diff > 0 else -1)
			
			# Apply the step to current value
			par.val = par.eval() + step_amount
			
			if update_cached_change:
				self.parent.lastCachedChange = (f'{par.owner.path}:{par.name}', par.eval())
		
		elif (par.isMenu or getattr(par, 'style', None) in ['Menu', 'StrMenu']) and (getattr(par, 'style', None) != 'StrMenu' or self.parent.should_allow_strmenus(par)):
			# Handle menu parameters - step through menu options
			if abs(diff) >= 1:  # Only change on significant step
				current_index = par.menuIndex
				num_menu_items = len(par.menuNames)
				step_direction = 1 if diff > 0 else -1
				
				if self.parent.evalLoopmenus and current_index is not None:
					# Loop around when reaching the end
					new_index = (current_index + step_direction) % num_menu_items
				elif current_index is not None:
					# Clamp at the edges
					new_index = max(0, min(num_menu_items - 1, current_index + step_direction))
				else:
					new_index = 0
				
				par.menuIndex = new_index
		
		elif par.isToggle or par.isMomentary:
			# Handle toggle parameters - step through on/off states
			current_val = par.eval()
			if diff > 0 and not current_val:
				par.val = True
			elif diff < 0 and current_val:
				par.val = False
	
	def _apply_push_to_parameter(self, par: Par, value: int, is_main_parameter: bool = False):
		"""Apply a push button action to a single parameter.
		
		Args:
			par: The parameter to adjust
			value: The MIDI velocity value
			is_main_parameter: Whether this is the main hovered parameter (for pulse hack flag)
		"""
		if value == MidiConstants.MAX_VELOCITY:
			if par.isMomentary:
				par.val = not par.default
			if par.isPulse and is_main_parameter:
				# HACK: sorry (only for main parameter)
				self.is_from_pulsepush = 1
		elif value == 0:
			if par.isPulse:
				par.pulse()
				if is_main_parameter:
					# HACK: sorry (only for main parameter)
					self.is_from_pulsepush = 2
			elif par.isMomentary:
				par.val = par.default
			elif par.isToggle:
				par.val = not par.eval()
	
	def _do_step_single(self, active_par: Par, step: float, value: int, update_display: bool = True):
		"""Apply step value to a single parameter based on MIDI input
		
		In hover mode (not slot mode), if multiple operators of the same type are selected,
		the same parameter change will be applied to all of them."""
		# Validate parameter is editable (constant or bind mode, not expression/export)
		if not ParameterValidator.is_valid_parameter(active_par):
			# Parameter has expression or is in export mode - show error and skip
			if update_display:
				self.parent.display_manager.show_parameter_error(active_par, ScreenMessages.EXPR)
			return
		
		# Apply secondary step if active (for numbers)
		if self.parent.knobPushState:
			step = self._get_push_step(step)
		
		diff = value - MidiConstants.MIDI_CENTER_VALUE
		
		# Apply step to main parameter
		self._apply_step_to_parameter(active_par, step, diff, update_cached_change=True)
		
		if self.parent.activeSlot is None: # hover mode
			# Multi-operator editing: Apply same change to other selected operators of same type
			# Only in hover mode (not slot mode)
			mulit_mode = self.parent.evalMultiadjustmode
			if mulit_mode != MultiAdjustMode.OFF.value:
				matching_pars = ParameterValidator.get_matching_selected_pars(active_par)
				if matching_pars:
					for other_par in matching_pars:
						try:
							if other_par is None or not ParameterValidator.is_valid_parameter(other_par):
								continue
							
							if mulit_mode == MultiAdjustMode.SNAP.value:
								other_par.val = active_par.eval()
							elif mulit_mode == MultiAdjustMode.RELATIVE.value:
								# Apply the same step adjustment
								self._apply_step_to_parameter(other_par, step, diff, update_cached_change=False)
						except:
							# If any error occurs with one operator, continue with others
							continue
		
		# Update screen display (only if requested)
		if update_display:
			self.parent.display_manager.update_parameter_display(active_par)

	def _get_push_step(self, step: float) -> float:
		if self.parent.evalPushstepmode == PushStepMode.FIXED.value:
			return self.parent.evalPushstep
		elif self.parent.evalPushstepmode == PushStepMode.FINER.value:
			# gonna be lazy and just divide by 10
			# we could get the step from the sequence blocks, but this is simpler and faster
			return step / 10
		elif self.parent.evalPushstepmode == PushStepMode.COARSER.value:
			# gonna be lazy and just multiply by 10
			# we could get the step from the sequence blocks, but this is simpler and faster
			return step * 10
		return step