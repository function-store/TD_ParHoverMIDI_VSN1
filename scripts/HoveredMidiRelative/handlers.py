
'''Info Header Start
Name : handlers
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.187.toe
Saveversion : 2023.12120
Info Header End'''
from constants import MidiConstants, VSN1ColorIndex, ScreenMessages, SecondaryMode, StepMode
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
		for bank_idx in range(len(self.parent.slotPars)):
			slot_idx = self.parent.slot_manager.find_slot_for_parameter(active_par, bank_idx)
			if slot_idx is not None:
				# Clear the slot containing this invalid parameter
				self.parent.slot_manager.clear_slot_in_bank(slot_idx, bank_idx)
	
	def _create_undo_for_parameter(self, active_par: Union['Par', 'ParGroup']):
		"""Create undo action for parameter or ParGroup (only if initial value was captured).
		
		Args:
			active_par: The parameter or ParGroup to create undo for
		"""
		# Handle ParGroup - create single undo block for all parameters
		if ParameterValidator.is_pargroup(active_par):
			self.parent.undo_manager.create_pargroup_undo(active_par)
		else:
			# Handle single Par
			self.parent.undo_manager.create_parameter_undo(active_par)
	
	def handle_step_message(self, index: int, value: int) -> bool:
		"""Handle step change messages"""
		blocks = self.parent._index_to_blocks(index, self.parent.seqSteps)
		if not blocks:
			return False
			
		block = blocks[0]
		if not self.shortcutPressed:
			if value == 0:
				self.parent._currStep = block.par.Step.eval()
		return True
	
	def handle_knob_message(self, index: int, value: int, active_par) -> bool:
		"""Handle knob control messages"""
		knob_index = self.parent._safe_get_midi_index(self.parent.evalKnobindex, default=-1)
		if index != knob_index:
			return False

		if active_par is None or not active_par.valid or (active_par.owner == self.parent.ownerComp):
			# Clear invalid parameter from all slots
			self._clear_invalid_parameter_from_slots(active_par)
			return False
		
		if error_msg := ParameterValidator.get_validation_error(active_par):
			self.parent.display_manager.show_parameter_error(active_par, error_msg)
			return True  # Parameter is invalid, error message shown
		
		# Only process actual knob movement (not center/idle position)
		if value == MidiConstants.MIDI_CENTER_VALUE:
			return True
		
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
			
		if active_par is None or not active_par.valid or (active_par.owner == self.parent.ownerComp):
			# Clear invalid parameter from all slots
			self._clear_invalid_parameter_from_slots(active_par)
			return False

		# Handle ParGroup
		if ParameterValidator.is_pargroup(active_par):
			# Check if any valid parameter is from ownerComp
			valid_pars = [p for p in active_par if p is not None and ParameterValidator.is_valid_parameter(p)]
			if not valid_pars:
				return False
			if any(p.owner == self.parent.ownerComp for p in valid_pars):
				return False
			
			error_msg = ParameterValidator.get_validation_error(active_par)
			if error_msg:
				self.parent.display_manager.show_parameter_error(active_par, error_msg)
				return True  # Parameter group is invalid, error message shown
			
			# Apply push action to all valid parameters in group
			if value == MidiConstants.MAX_VELOCITY:
				for par in active_par:
					# Skip invalid parameters within the group
					if par is None or not ParameterValidator.is_valid_parameter(par):
						continue
					if par.isPulse:
						par.pulse()
					elif par.isMomentary:
						par.val = True
					elif par.isToggle:
						par.val = not par.eval()
			if value == 0:
				for par in active_par:
					# Skip invalid parameters within the group
					if par is None or not ParameterValidator.is_valid_parameter(par):
						continue
					if par.isMomentary:
						par.val = False
			self.parent.display_manager.update_parameter_display(active_par)
			return True
		
		# Handle single Par

		error_msg = ParameterValidator.get_validation_error(active_par)
		if error_msg:
			self.parent.display_manager.show_parameter_error(active_par, error_msg)
			return True  # Parameter is invalid, error message shown
			
		if value == MidiConstants.MAX_VELOCITY:
			if active_par.isPulse:
				active_par.pulse()
			elif active_par.isMomentary:
				active_par.val = not active_par.default
			elif active_par.isToggle:
				active_par.val = not active_par.eval()
		if value == 0:
			if active_par.isMomentary:
				active_par.val = active_par.default
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
		if (currBank < len(self.parent.slotPars) and 
			block_idx < len(self.parent.slotPars[currBank]) and 
			self.parent.slotPars[currBank][block_idx] is not None):
			
			# Validate parameter before activating
			active_par = self.parent.slotPars[currBank][block_idx]
			if not active_par.valid:
				# Clear invalid parameter from all slots
				self._clear_invalid_parameter_from_slots(active_par)
				return False
			
			# Check for validation errors
			error_msg = ParameterValidator.get_validation_error(active_par)
			if error_msg:
				self.parent.display_manager.show_parameter_error(active_par, error_msg)
				return True
			
			# Activate the slot using slot_manager
			return self.parent.slot_manager.activate_slot(block_idx)
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
			if par is not None and ParameterValidator.is_valid_parameter(par):
				self._do_step_single(par, step, value, update_display=False)
		
		# Update display once after all valid parameters are updated
		self.parent.display_manager.update_parameter_display(par_group)
	
	def _do_step_single(self, active_par: Par, step: float, value: int, update_display: bool = True):
		"""Apply step value to a single parameter based on MIDI input"""
		diff = value - MidiConstants.MIDI_CENTER_VALUE
		
		if active_par.isNumber:
			# Apply secondary step if active
			if self.parent.secondaryPushState and self.parent.secondaryMode == SecondaryMode.STEP:
				step = self.parent.evalSecondarystep or step
			
			# Calculate step amount based on mode
			if self.parent.stepMode == StepMode.FIXED:
				step_amount = step * diff
			else: # Adaptive mode - step scales with parameter range
				min_val, max_val = active_par.normMin, active_par.normMax
				step_amount = ((max_val - min_val) * step) * diff
			
			# Handle integer parameters with different step behavior
			if active_par.isInt:
				if self.parent.stepMode == StepMode.FIXED:
					# TODO: debatable if this fixed step is good for ints in fixed mode. What's the alternative?
					step_amount = 1 if diff > 0 else -1
				else:
					step_amount = max(1, ((max_val - min_val) * step)) * (1 if diff > 0 else -1)
				
			# Apply the step to current value
			active_par.val = active_par.eval() + step_amount
			
		elif active_par.isMenu and not active_par.isString:
			# NOTE: we don't act on string menus, if we need to, remove the not active_par.isString check
			# Handle menu parameters - step through menu options
			if abs(diff) >= 1:  # Only change on significant step
				current_index = active_par.menuIndex
				num_menu_items = len(active_par.menuNames)
				step_direction = 1 if diff > 0 else -1
				
				if self.parent.evalLoopmenus:
					# Loop around when reaching the end
					new_index = (current_index + step_direction) % num_menu_items
				else:
					# Clamp at the edges
					new_index = max(0, min(num_menu_items - 1, current_index + step_direction))
				
				active_par.menuIndex = new_index
					
		elif active_par.isToggle or active_par.isMomentary:
			# Handle toggle parameters - step through on/off states
			current_val = active_par.eval()
			if diff > 0 and not current_val:
				active_par.val = True
			elif diff < 0 and current_val:
				active_par.val = False
		else:
			# Unsupported parameter type
			return
		
		# Update screen display (only if requested)
		if update_display:
			self.parent.display_manager.update_parameter_display(active_par)

