
'''Info Header Start
Name : undo_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.187.toe
Saveversion : 2025.31310
Info Header End'''
from typing import Union, Optional

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
		from validators import ParameterValidator
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
		
		from validators import ParameterValidator
		
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
	
	def start_undo_timeout(self, timeout_ms: int = 2000):
		"""Start/restart timeout to clear captured parameter values after inactivity.
		
		Args:
			timeout_ms: Timeout in milliseconds before clearing captured values
		"""
		# Check if timeout is already running
		try:
			if self.undo_timeout_run_obj is not None and self.undo_timeout_run_obj.active:
				# Reset the timer by setting remainingMilliseconds
				self.undo_timeout_run_obj.remainingMilliseconds = timeout_ms
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
			from validators import ParameterValidator
			for par in par_group:
				if par is not None and ParameterValidator.is_valid_parameter(par):
					par.reset()
			return
		
		from validators import ParameterValidator
		
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

