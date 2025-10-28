
'''Info Header Start
Name : undo_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.187.toe
Saveversion : 2023.12120
Info Header End'''

from typing import Union, Optional
from validators import ParameterValidator
from formatters import LabelFormatter
from constants import ScreenMessages, VSN1ColorIndex

class UndoManager:
	"""Manages undo/redo functionality for parameter changes and resets"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
		
		# Tracking for undo actions
		self.parameterInitialValues = {}  # Maps parameter path to initial value
		self.parameterUndoCreated = {}  # Maps parameter path to True if undo was created
		self.undo_timeout_run_obj = None  # Run object for undo timeout
	
	def clear_unused_captured_values(self, par_or_group: Union['Par', 'ParGroup']):
		"""Clear captured initial values that never resulted in undo actions."""
		if ParameterValidator.is_pargroup(par_or_group):
			for par in par_or_group:
				if par is not None:
					par_path = f"{par.owner.path}:{par.name}"
					if par_path in self.parameterInitialValues:
						del self.parameterInitialValues[par_path]
					if par_path in self.parameterUndoCreated:
						del self.parameterUndoCreated[par_path]
		else:
			par_path = f"{par_or_group.owner.path}:{par_or_group.name}"
			if par_path in self.parameterInitialValues:
				del self.parameterInitialValues[par_path]
			if par_path in self.parameterUndoCreated:
				del self.parameterUndoCreated[par_path]
	
	def capture_initial_parameter_value(self, par: 'Par'):
		"""Capture the initial value of a parameter (lightweight, no undo action yet).
		
		Args:
			par: The parameter to capture initial value for
		"""
		if not self.parent.evalEnableundo:
			return
		
		# Skip pulse parameters (momentary actions don't need undo)
		if par.isPulse:
			return
		
		# Use parameter path as unique key
		par_path = f"{par.owner.path}:{par.name}"
		
		# Only capture if we don't already have one for this parameter
		if par_path in self.parameterInitialValues:
			return
		
		# Store initial value based on parameter type (just capture, don't create undo yet)
		if par.isMenu:
			initial_value = par.menuIndex
		else:
			initial_value = par.eval()
		
		self.parameterInitialValues[par_path] = initial_value
	
	def create_parameter_undo(self, par: 'Par', skip_block: bool = False):
		"""Create undo action for parameter using previously captured initial value.
		
		Args:
			par: The parameter to create undo for
			skip_block: If True, don't create startBlock/endBlock (for use in ParGroup)
		
		Returns:
			True if undo was created, False otherwise
		"""
		if not self.parent.evalEnableundo:
			return False
		
		# Skip pulse parameters (momentary actions don't need undo)
		if par.isPulse:
			return False
		
		# Use parameter path as unique key
		par_path = f"{par.owner.path}:{par.name}"
		
		# If no initial value captured (e.g., after timeout), capture current value as new checkpoint
		if par_path not in self.parameterInitialValues:
			self.capture_initial_parameter_value(par)
			return False  # Don't create undo yet, wait for next movement
		
		# Skip if we already created an undo for this parameter (ongoing adjustment)
		if par_path in self.parameterUndoCreated:
			return False
		
		initial_value = self.parameterInitialValues[par_path]
		
		# Create undo action
		if not skip_block:
			ui.undo.startBlock(f'Change {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'initial_value': initial_value,
				'is_menu': par.isMenu,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_parameter_change_callback, undo_info)
		finally:
			if not skip_block:
				ui.undo.endBlock()
		
		# Mark that undo was created (keep in dict for timeout management)
		self.parameterUndoCreated[par_path] = True
		return True
	
	def create_pargroup_undo(self, par_group: 'ParGroup'):
		"""Create a single undo action for all parameters in a ParGroup.
		
		Args:
			par_group: The ParGroup to create undo for
		"""
		if not self.parent.evalEnableundo:
			return
		
		# Collect all valid parameters that need undo
		pars_to_undo = []
		for par in par_group:
			if par is not None and ParameterValidator.is_valid_parameter(par) and not par.isPulse:
				par_path = f"{par.owner.path}:{par.name}"
				# Check if we have captured initial value and haven't created undo yet
				if par_path in self.parameterInitialValues and par_path not in self.parameterUndoCreated:
					pars_to_undo.append(par)
		
		# If no parameters need undo, check if we need to capture initial values
		if not pars_to_undo:
			for par in par_group:
				if par is not None and ParameterValidator.is_valid_parameter(par) and not par.isPulse:
					par_path = f"{par.owner.path}:{par.name}"
					if par_path not in self.parameterInitialValues:
						self.capture_initial_parameter_value(par)
			return
		
		# Get group name safely
		try:
			group_name = next((p.owner.name for p in pars_to_undo if p is not None), "ParGroup")
		except:
			group_name = "ParGroup"
		
		# Create single undo block for all parameters in the group
		ui.undo.startBlock(f'Change {group_name} ParGroup')
		try:
			for par in pars_to_undo:
				self.create_parameter_undo(par, skip_block=True)
		finally:
			ui.undo.endBlock()
	
	def start_undo_timeout(self, timeout_ms: float = None):
		"""Start/restart timeout to clear captured parameter values after inactivity.
		
		Args:
			timeout_ms: Timeout in milliseconds before clearing captured values
		"""
		# Check if timeout is already running
		if timeout_ms is None:
			timeout_ms = self.parent.evalUndotimeout*1000
		
		try:
			if self.undo_timeout_run_obj is not None and self.undo_timeout_run_obj.active:
				# Reset the timer by setting remainingMilliseconds
				self.undo_timeout_run_obj.remainingMilliseconds = int(timeout_ms)
				return
		except (AttributeError, tdError):
			pass
		
		# Start new timeout if not already running
		self.undo_timeout_run_obj = run(
			"args[0].undo_manager.clear_all_captured_values()",
			self.parent,
			delayMilliSeconds=timeout_ms,
			delayRef=op.TDResources
		)
	
	def kill_undo_timeout(self):
		"""Kill the undo timeout if it's running."""
		try:
			if self.undo_timeout_run_obj is not None and self.undo_timeout_run_obj.active:
				self.undo_timeout_run_obj.kill()
		except (AttributeError, tdError):
			pass
	
	def clear_all_captured_values(self):
		"""Clear all captured initial values (called after timeout)."""
		self.parameterInitialValues.clear()
		self.parameterUndoCreated.clear()
	
	def on_slot_activated(self, slot_par: Union['Par', 'ParGroup']):
		"""Handle undo operations when a slot is activated.
		
		Args:
			slot_par: The parameter or ParGroup assigned to the activated slot
		"""
		
		# Capture initial values for undo when slot is activated
		if ParameterValidator.is_pargroup(slot_par):
			for par in slot_par:
				if par is not None and ParameterValidator.is_valid_parameter(par):
					self.capture_initial_parameter_value(par)
		else:
			self.capture_initial_parameter_value(slot_par)
	
	def on_slot_deactivated(self, slot_par: Union['Par', 'ParGroup']):
		"""Handle undo operations when a slot is deactivated.
		
		Args:
			slot_par: The parameter or ParGroup assigned to the deactivated slot
		"""
		# Clear any unused captured values from the deactivated slot
		self.clear_unused_captured_values(slot_par)
	
	def on_parameter_hovered(self, par_or_group: Union['Par', 'ParGroup']):
		"""Handle undo operations when a parameter is hovered.
		
		Args:
			par_or_group: The parameter or ParGroup that was hovered
		"""
		
		# Capture initial values for undo when hovering
		if ParameterValidator.is_pargroup(par_or_group):
			for par in par_or_group:
				if par is not None and ParameterValidator.is_valid_parameter(par):
					self.capture_initial_parameter_value(par)
		else:
			self.capture_initial_parameter_value(par_or_group)
	
	def on_parameter_unhovered(self, par_or_group: Union['Par', 'ParGroup']):
		"""Handle undo operations when a parameter is no longer hovered.
		
		Args:
			par_or_group: The parameter or ParGroup that was unhovered
		"""
		# Clear any unused captured values if user didn't actually adjust the parameter
		self.clear_unused_captured_values(par_or_group)
	
	def _undo_parameter_change_callback(self, isUndo, info):
		"""Callback for undoing parameter value changes.
		
		Args:
			isUndo: True if undoing, False if redoing
			info: Dictionary containing undo information
		"""
		par_path = info['par_path']
		is_menu = info['is_menu']
		
		# Parse parameter path
		try:
			owner_path, par_name = par_path.rsplit(':', 1)
			owner_op = op(owner_path)
			
			if owner_op is None:
				return
			
			par = owner_op.par[par_name]
			if par is None:
				return
			
			# Get current value
			if is_menu:
				current_value = par.menuIndex
			else:
				current_value = par.eval()
			
			# Swap with stored initial value for undo/redo
			if isUndo:
				target_value = info['initial_value']
				info['initial_value'] = current_value  # Store current for redo
			else:
				target_value = info['initial_value']
				info['initial_value'] = current_value  # Store current for next undo
			
			# Apply value
			if is_menu:
				par.menuIndex = target_value
			else:
				par.val = target_value
			
			# Update display if this parameter is currently active
			if self.parent.activePar == par:
				self.parent.display_manager.update_parameter_display(par)
			
		except Exception as e:
			pass
	
	def create_reset_undo_for_parameter(self, par: 'Par'):
		"""Create undo action for resetting a parameter.
		
		Args:
			par: The parameter to reset
		"""
		if not self.parent.evalEnableundo:
			par.reset()
			return
		
		# Skip pulse parameters
		if par.isPulse:
			par.reset()
			return
		
		# Capture current value before reset
		par_path = f"{par.owner.path}:{par.name}"
		if par.isMenu:
			current_value = par.menuIndex
		else:
			current_value = par.eval()
		
		# Perform the reset
		par.reset()
		
		# Get reset value
		if par.isMenu:
			reset_value = par.menuIndex
		else:
			reset_value = par.eval()
		
		# Create undo action
		ui.undo.startBlock(f'Reset {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'old_value': current_value,
				'new_value': reset_value,
				'is_menu': par.isMenu,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_reset_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def create_reset_undo_for_pargroup(self, par_group: 'ParGroup'):
		"""Create undo action for resetting all parameters in a ParGroup.
		
		Args:
			par_group: The ParGroup to reset
		"""
		if not self.parent.evalEnableundo:
			# Reset without undo
			for par in par_group:
				if par is not None and ParameterValidator.is_valid_parameter(par):
					par.reset()
			return
		
		# Capture current values for all valid parameters
		reset_info_list = []
		for par in par_group:
			if par is not None and ParameterValidator.is_valid_parameter(par) and not par.isPulse:
				par_path = f"{par.owner.path}:{par.name}"
				if par.isMenu:
					current_value = par.menuIndex
				else:
					current_value = par.eval()
				
				# Perform the reset
				par.reset()
				
				# Get reset value
				if par.isMenu:
					reset_value = par.menuIndex
				else:
					reset_value = par.eval()
				
				reset_info_list.append({
					'par_path': par_path,
					'old_value': current_value,
					'new_value': reset_value,
					'is_menu': par.isMenu,
					'par_name': par.name
				})
		
		if not reset_info_list:
			return
		
		# Get group name
		try:
			group_name = next((p.owner.name for p in par_group if p is not None), "ParGroup")
		except:
			group_name = "ParGroup"
		
		# Create single undo block for all parameters
		ui.undo.startBlock(f'Reset {group_name} ParGroup')
		try:
			for reset_info in reset_info_list:
				ui.undo.addCallback(self._undo_reset_callback, reset_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_reset_callback(self, isUndo, info):
		"""Callback for undoing parameter reset.
		
		Args:
			isUndo: True if undoing, False if redoing
			info: Dictionary containing reset information
		"""
		par_path = info['par_path']
		is_menu = info['is_menu']
		
		# Parse parameter path
		try:
			owner_path, par_name = par_path.rsplit(':', 1)
			owner_op = op(owner_path)
			
			if owner_op is None:
				return
			
			par = owner_op.par[par_name]
			if par is None:
				return
			
			# Set value based on undo/redo
			if isUndo:
				# Restore old value
				target_value = info['old_value']
			else:
				# Restore reset value
				target_value = info['new_value']
			
			# Apply value
			if is_menu:
				par.menuIndex = target_value
			else:
				par.val = target_value
			
			# Update display if this is the active parameter
			if self.parent.activePar == par:
				self.parent.display_manager.update_parameter_display(par)
			
		except Exception as e:
			pass
	
	def create_set_default_undo(self, par: 'Par', old_default: float, new_default: float):
		"""Create undo action for setting parameter default value.
		
		Args:
			par: The parameter whose default was set
			old_default: The previous default value
			new_default: The new default value
		"""
		if not self.parent.evalEnableundo:
			return
		
		par_path = f"{par.owner.path}:{par.name}"
		
		ui.undo.startBlock(f'Set Default {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'old_default': old_default,
				'new_default': new_default,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_set_default_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_set_default_callback(self, isUndo, info):
		"""Callback for undoing parameter default change."""
		par_path = info['par_path']
		
		try:
			owner_path, par_name = par_path.rsplit(':', 1)
			owner_op = op(owner_path)
			
			if owner_op is None:
				return
			
			par = owner_op.par[par_name]
			if par is None or not par.isCustom:
				return
			
			# Set value based on undo/redo
			if isUndo:
				par.default = info['old_default']
			else:
				par.default = info['new_default']
			
			# Update display if this is the active parameter
			if self.parent.activePar == par:
				self.parent.display_manager.update_parameter_display(par)
			
		except Exception as e:
			pass
	
	def create_set_norm_undo(self, par: 'Par', is_min: bool, 
	                          old_norm: float, new_norm: float, 
	                          old_minmax: float, new_minmax: float):
		"""Create undo action for setting parameter norm and min/max values.
		
		Args:
			par: The parameter whose norm was set
			is_min: True if setting min, False if setting max
			old_norm: The previous normMin or normMax value
			new_norm: The new normMin or normMax value
			old_minmax: The previous min or max value
			new_minmax: The new min or max value
		"""
		if not self.parent.evalEnableundo:
			return
		
		par_path = f"{par.owner.path}:{par.name}"
		
		ui.undo.startBlock(f'Set {"Min" if is_min else "Max"} {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'is_min': is_min,
				'old_norm': old_norm,
				'new_norm': new_norm,
				'old_minmax': old_minmax,
				'new_minmax': new_minmax,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_set_norm_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_set_norm_callback(self, isUndo, info):
		"""Callback for undoing parameter norm/min/max change."""
		par_path = info['par_path']
		is_min = info['is_min']
		
		try:
			owner_path, par_name = par_path.rsplit(':', 1)
			owner_op = op(owner_path)
			
			if owner_op is None:
				return
			
			par = owner_op.par[par_name]
			if par is None or not par.isCustom:
				return
			
			# Set values based on undo/redo
			if isUndo:
				if is_min:
					par.normMin = info['old_norm']
					par.min = info['old_minmax']
				else:
					par.normMax = info['old_norm']
					par.max = info['old_minmax']
			else:
				if is_min:
					par.normMin = info['new_norm']
					par.min = info['new_minmax']
				else:
					par.normMax = info['new_norm']
					par.max = info['new_minmax']
			
			# Update display if this is the active parameter
			if self.parent.activePar == par:
				self.parent.display_manager.update_parameter_display(par)
			
		except Exception as e:
			pass
	
	def create_set_clamp_undo(self, par: 'Par', changed_min: bool, changed_max: bool,
	                           old_clamp_min: bool, new_clamp_min: bool,
	                           old_clamp_max: bool, new_clamp_max: bool):
		"""Create undo action for toggling parameter clamp values.
		
		Args:
			par: The parameter whose clamp was toggled
			changed_min: True if clampMin was changed
			changed_max: True if clampMax was changed
			old_clamp_min: The previous clampMin value
			new_clamp_min: The new clampMin value
			old_clamp_max: The previous clampMax value
			new_clamp_max: The new clampMax value
		"""
		if not self.parent.evalEnableundo:
			return
		
		par_path = f"{par.owner.path}:{par.name}"
		
		ui.undo.startBlock(f'Toggle Clamp {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'changed_min': changed_min,
				'changed_max': changed_max,
				'old_clamp_min': old_clamp_min,
				'new_clamp_min': new_clamp_min,
				'old_clamp_max': old_clamp_max,
				'new_clamp_max': new_clamp_max,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_set_clamp_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_set_clamp_callback(self, isUndo, info):
		"""Callback for undoing parameter clamp change."""
		par_path = info['par_path']
		
		try:
			owner_path, par_name = par_path.rsplit(':', 1)
			owner_op = op(owner_path)
			
			if owner_op is None:
				return
			
			par = owner_op.par[par_name]
			if par is None or not par.isCustom:
				return
			
			# Set values based on undo/redo
			if isUndo:
				if info['changed_min']:
					par.clampMin = info['old_clamp_min']
				if info['changed_max']:
					par.clampMax = info['old_clamp_max']
			else:
				if info['changed_min']:
					par.clampMin = info['new_clamp_min']
				if info['changed_max']:
					par.clampMax = info['new_clamp_max']
			
			# Update display if this is the active parameter
			if self.parent.activePar == par:
				self.parent.display_manager.update_parameter_display(par)
			
		except Exception as e:
			pass
	
	def create_assign_slot_undo(self, slot_idx: int, bank_idx: int, new_parameter: Union['Par', 'ParGroup'],
	                             previous_parameter: Union['Par', 'ParGroup', None],
	                             previous_active_slot: Optional[int], previous_bank_active_slot: Optional[int]):
		"""Create undo action for slot assignment.
		
		Args:
			slot_idx: Index of the slot being assigned
			bank_idx: Index of the bank containing the slot
			new_parameter: The parameter (or ParGroup) being assigned to the slot
			previous_parameter: The parameter that was previously in the slot (or None)
			previous_active_slot: The active slot index before assignment
			previous_bank_active_slot: The bank's active slot before assignment
		"""
		if not self.parent.evalEnableundo:
			return
		
		ui.undo.startBlock(f'Assign Slot {slot_idx} in Bank {bank_idx}')
		try:
			undo_info = {
				'slot_idx': slot_idx,
				'bank_idx': bank_idx,
				'new_parameter': new_parameter,
				'previous_parameter': previous_parameter,
				'previous_active_slot': previous_active_slot,
				'previous_bank_active_slot': previous_bank_active_slot
			}
			ui.undo.addCallback(self._undo_assign_slot_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_assign_slot_callback(self, isUndo, info):
		"""Undo callback to restore previous state or redo assignment"""		
		slot_idx = info['slot_idx']
		bank_idx = info['bank_idx']
		is_current_bank = self.parent.currBank == bank_idx
		
		if isUndo:
			# Restore the previous state (before assignment)
			previous_parameter = info['previous_parameter']
			previous_active_slot = info['previous_active_slot']
			previous_bank_active_slot = info['previous_bank_active_slot']
			
			# Restore the slot to its previous state
			self.parent.slotPars[bank_idx][slot_idx] = previous_parameter
			self.parent.bankActiveSlots[bank_idx] = previous_bank_active_slot
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				self.parent.activeSlot = previous_active_slot
				
				# Update hovered UI color based on restored active slot
				if previous_active_slot is None:
					# Restoring to hover mode
					if self.parent.evalColorhoveredui:
						self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
					else:
						self.parent.ui_manager.set_hovered_ui_color(-1)
				else:
					# Restoring to slot mode
					self.parent.ui_manager.set_hovered_ui_color(-1)
				
				# Update UI button label
				if hasattr(self.parent, 'ui_manager'):
					if previous_parameter is not None:
						label = LabelFormatter.get_label_for_parameter(previous_parameter, self.parent.labelDisplayMode)
					else:
						label = ScreenMessages.HOVER
					self.parent.ui_manager._set_button_label(slot_idx, label)
				
				# Update display
				if previous_active_slot == slot_idx and previous_parameter is not None:
					self.parent.display_manager.update_parameter_display(previous_parameter)
					self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
				elif previous_active_slot is None:
					# Return to hover mode
					self.parent.display_manager.update_all_display(
						0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
					self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
				
				# Update LEDs
				self.parent.display_manager.update_slot_leds(current_slot=previous_active_slot)
		else:
			# Redo: apply the assignment again
			new_parameter = info['new_parameter']
			
			self.parent.slotPars[bank_idx][slot_idx] = new_parameter
			self.parent.activeSlot = slot_idx
			self.parent.bankActiveSlots[bank_idx] = slot_idx
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			# Turn off hovered UI color when assigning a slot
			if is_current_bank:
				self.parent.ui_manager.set_hovered_ui_color(-1)
			
			if is_current_bank:
				# Update UI button label
				if hasattr(self.parent, 'ui_manager'):
					label = LabelFormatter.get_label_for_parameter(new_parameter, self.parent.labelDisplayMode)
					self.parent.ui_manager._set_button_label(slot_idx, label)
				
				# Update display
				self.parent.display_manager.update_parameter_display(new_parameter, bottom_text=ScreenMessages.LEARNED)
				
				# Update LEDs
				self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
				self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		
		# Always refresh UI buttons for current bank
		if hasattr(self.parent, 'ui_manager') and self.parent.ui_manager:
			run("args[0].refresh_all_button_states()", self.parent.ui_manager, delayFrames=1)
	
	def create_clear_slot_undo(self, slot_idx: int, bank_idx: int, previous_parameter: Union['Par', 'ParGroup'],
	                            previous_active_slot: Optional[int], previous_bank_active_slot: Optional[int]):
		"""Create undo action for slot clearing.
		
		Args:
			slot_idx: Index of the slot being cleared
			bank_idx: Index of the bank containing the slot
			previous_parameter: The parameter that was in the slot before clearing
			previous_active_slot: The active slot index before clearing
			previous_bank_active_slot: The bank's active slot before clearing
		"""
		if not self.parent.evalEnableundo:
			return
		
		ui.undo.startBlock(f'Clear Slot {slot_idx} in Bank {bank_idx}')
		try:
			undo_info = {
				'slot_idx': slot_idx,
				'bank_idx': bank_idx,
				'previous_parameter': previous_parameter,
				'previous_active_slot': previous_active_slot,
				'previous_bank_active_slot': previous_bank_active_slot
			}
			ui.undo.addCallback(self._undo_clear_slot_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_clear_slot_callback(self, isUndo, info):
		"""Undo callback to restore or re-clear a slot"""		
		slot_idx = info['slot_idx']
		bank_idx = info['bank_idx']
		is_current_bank = self.parent.currBank == bank_idx
		
		if isUndo:
			# Restore the slot
			previous_parameter = info['previous_parameter']
			previous_active_slot = info['previous_active_slot']
			previous_bank_active_slot = info['previous_bank_active_slot']
			
			# Validate parameter (or ParGroup) still exists and is of supported type
			# (We allow parameters with expressions/exports, so don't check validity - just existence and type)
			try:
				# Handle ParGroup
				if ParameterValidator.is_pargroup(previous_parameter):
					# Check if any parameters in the group still exist
					has_existing = any(p.valid for p in previous_parameter if p is not None)
					if not has_existing:
						# ParGroup no longer exists, cannot restore
						return
					# Check if it's still a supported type
					if not ParameterValidator.is_supported_parameter_type(previous_parameter):
						return
				# Handle single Par
				elif previous_parameter is None or not previous_parameter.valid:
					# Parameter no longer exists, cannot restore
					return
				# Check if single Par is still a supported type
				elif not ParameterValidator.is_supported_parameter_type(previous_parameter):
					return
			except:
				# Parameter reference is completely invalid
				return
			
			self.parent.slotPars[bank_idx][slot_idx] = previous_parameter
			self.parent.bankActiveSlots[bank_idx] = previous_bank_active_slot
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				self.parent.activeSlot = previous_active_slot
				
				# Update hovered UI color based on restored active slot
				if previous_active_slot is None:
					# Restoring to hover mode
					if self.parent.evalColorhoveredui:
						self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
					else:
						self.parent.ui_manager.set_hovered_ui_color(-1)
				else:
					# Restoring to slot mode
					self.parent.ui_manager.set_hovered_ui_color(-1)
				
				# Restore UI button label
				if hasattr(self.parent, 'ui_manager'):
					label = LabelFormatter.get_label_for_parameter(previous_parameter, self.parent.labelDisplayMode)
					self.parent.ui_manager._set_button_label(slot_idx, label)
				
				# Restore display
				if previous_active_slot == slot_idx:
					self.parent.display_manager.update_parameter_display(previous_parameter)
					self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
				else:
					# Return to hover mode if slot wasn't active
					self.parent.display_manager.update_all_display(
						0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
					self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
				
				# Restore LEDs
				self.parent.display_manager.update_slot_leds(current_slot=previous_active_slot)
		else:
			# Redo: clear the slot again
			self.parent.slotPars[bank_idx][slot_idx] = None
			self.parent.bankActiveSlots[bank_idx] = None
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				self.parent.activeSlot = None
				
				# Restore hovered UI color if enabled (redoing clear)
				if self.parent.evalColorhoveredui:
					self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
				else:
					self.parent.ui_manager.set_hovered_ui_color(-1)
				
				if hasattr(self.parent, 'ui_manager'):
					self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
				
				self.parent.display_manager.update_all_display(
					0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
				
				self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
				self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		
		# Always refresh UI buttons for current bank to ensure correct state
		# (TouchDesigner's undo system may revert some UI states)
		if hasattr(self.parent, 'ui_manager') and self.parent.ui_manager:
			#self.parent.ui_manager.refresh_all_button_states()
			run("args[0].refresh_all_button_states()", self.parent.ui_manager, delayFrames=1)


