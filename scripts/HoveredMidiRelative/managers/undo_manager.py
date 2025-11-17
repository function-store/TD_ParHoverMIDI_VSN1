
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

	@staticmethod
	def _par_path(par: 'Par') -> str:
		return f"{par.owner.path}:{par.name}"

	@staticmethod
	def _is_unit_parameter(par: 'Par') -> bool:
		return par.name.endswith('unit') and len(par.name) > 4

	def _iter_par_inputs(self, par_input):
		if par_input is None:
			return
		if ParameterValidator.is_pargroup(par_input):
			for par in par_input:
				yield par
			return
		if isinstance(par_input, (list, tuple, set)):
			for item in par_input:
				yield from self._iter_par_inputs(item)
			return
		yield par_input

	def _iter_filtered_pars(self, *par_inputs, skip_units=False, skip_pulse=True, require_custom=False, validator=None):
		for par_input in par_inputs:
			for par in self._iter_par_inputs(par_input):
				if par is None:
					continue
				if skip_units and self._is_unit_parameter(par):
					continue
				if skip_pulse and getattr(par, 'isPulse', False):
					continue
				if validator and not validator(par):
					continue
				if require_custom and not getattr(par, 'isCustom', False):
					continue
				yield par

	def _collect_pars_for_undo(self, pars_iterable):
		pars_to_undo = []
		for par in pars_iterable:
			par_path = self._par_path(par)
			if par_path not in self.parameterInitialValues:
				self.capture_initial_parameter_value(par)
			if par_path in self.parameterInitialValues and par_path not in self.parameterUndoCreated:
				pars_to_undo.append(par)
		return pars_to_undo

	def _create_grouped_parameter_undo(self, pars, block_name: str):
		if not pars:
			return
		if len(pars) == 1:
			self.create_parameter_undo(pars[0], skip_block=False)
			return
		ui.undo.startBlock(block_name)
		try:
			for par in pars:
				self.create_parameter_undo(par, skip_block=True)
		finally:
			ui.undo.endBlock()

	@staticmethod
	def _safe_group_name(par_group, default_name="ParGroup"):
		try:
			return next((p.owner.name for p in par_group if p is not None), default_name)
		except Exception:
			return default_name

	def _is_resettable_parameter(self, par: 'Par'):
		if par is None:
			return False
		# Skip readOnly or disabled parameters
		try:
			if par.readOnly or not par.enable:
				return False
		except Exception:
			pass
		try:
			if ParameterValidator.is_valid_parameter(par):
				return True
		except Exception:
			pass
		try:
			return par.mode in (ParMode.CONSTANT, ParMode.EXPRESSION, ParMode.EXPORT, ParMode.BIND)
		except Exception:
			return False
	
	def clear_unused_captured_values(self, par_or_group: Union['Par', 'ParGroup']):
		"""Clear captured initial values that never resulted in undo actions.
		Also clears matching parameters from multi-operator editing."""
		for par in self._iter_filtered_pars(par_or_group, skip_pulse=False):
			self._clear_parameter_and_matching(par)
	
	def _clear_parameter_and_matching(self, par: 'Par'):
		"""Clear a parameter and all its matching parameters (for multi-operator editing)."""
		par_path = self._par_path(par)
		
		# Clear main parameter
		if par_path in self.parameterInitialValues:
			del self.parameterInitialValues[par_path]
		if par_path in self.parameterUndoCreated:
			del self.parameterUndoCreated[par_path]
		
		# Clear matching parameters (for multi-operator editing)
		# Only if we're in hover mode (multi-adjust only works in hover mode)
		if self.parent.activeSlot is None:
			try:
				matching_pars = ParameterValidator.get_matching_selected_pars(par)
				if matching_pars:
					for matching_par in matching_pars:
						if matching_par is not None:
							matching_path = self._par_path(matching_par)
							if matching_path in self.parameterInitialValues:
								del self.parameterInitialValues[matching_path]
							if matching_path in self.parameterUndoCreated:
								del self.parameterUndoCreated[matching_path]
			except:
				# If we can't get matching parameters, just continue
				pass
	
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
		par_path = self._par_path(par)
		
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
		par_path = self._par_path(par)
		
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
		
		pars_to_undo = self._collect_pars_for_undo(
			self._iter_filtered_pars(
				par_group,
				skip_units=True,
				validator=ParameterValidator.is_valid_parameter
			)
		)
		if not pars_to_undo:
			return
		
		group_name = self._safe_group_name(par_group)
		self._create_grouped_parameter_undo(pars_to_undo, f'Change {group_name} ParGroup')
	
	def create_multi_parameter_undo(self, main_par: 'Par', additional_pars: list):
		"""Create a single undo action for multiple parameters (main + multi-operator editing).
		
		Args:
			main_par: The main parameter being adjusted
			additional_pars: List of additional parameters being adjusted simultaneously
		"""
		if not self.parent.evalEnableundo:
			return
		
		pars_to_undo = self._collect_pars_for_undo(
			self._iter_filtered_pars(
				main_par,
				additional_pars,
				validator=ParameterValidator.is_valid_parameter
			)
		)
		if not pars_to_undo:
			return
		
		self._create_grouped_parameter_undo(pars_to_undo, f'Change {main_par.name} (Multi-Op)')
	
	def create_pargroup_with_multi_undo(self, par_group: 'ParGroup', additional_pars: list):
		"""Create a single undo action for a ParGroup + multi-operator editing parameters.
		
		Args:
			par_group: The main ParGroup being adjusted
			additional_pars: List of additional parameters from other operators being adjusted simultaneously
		"""
		if not self.parent.evalEnableundo:
			return
		
		pargroup_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			validator=ParameterValidator.is_valid_parameter
		))
		additional = list(self._iter_filtered_pars(additional_pars))
		pars_to_undo = self._collect_pars_for_undo(pargroup_pars + additional)
		if not pars_to_undo:
			return
		
		group_name = self._safe_group_name(par_group)
		self._create_grouped_parameter_undo(pars_to_undo, f'Change {group_name} ParGroup (Multi-Op)')
	
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
		for par in self._iter_filtered_pars(slot_par, validator=ParameterValidator.is_valid_parameter, skip_pulse=False):
			self.capture_initial_parameter_value(par)
	
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
		for par in self._iter_filtered_pars(par_or_group, validator=ParameterValidator.is_valid_parameter, skip_pulse=False):
			self.capture_initial_parameter_value(par)
	
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
			# Check if the parameter is part of the active parameter (single Par or ParGroup)
			active_par = self.parent.activePar
			if active_par is not None:
				if active_par == par:
					# Direct match (single parameter)
					self.parent.display_manager.update_parameter_display(par)
				elif ParameterValidator.is_pargroup(active_par):
					# Check if this parameter is part of the active ParGroup
					# Iterate through ParGroup to check membership (same logic as onActiveValueChange)
					try:
						for par_in_group in active_par:
							if par_in_group.owner == par.owner and par_in_group.name == par.name:
								# Update display with the entire ParGroup (same as normal operation)
								self.parent.display_manager.update_parameter_display(active_par)
								break
					except:
						pass
			
		except Exception as e:
			pass
	
	def _capture_and_reset_parameter(self, par: 'Par'):
		"""Helper to capture state, reset parameter, and return reset info.
		
		Args:
			par: The parameter to reset
			
		Returns:
			Dict with reset info, or None if parameter should be skipped
		"""
		if par.isPulse:
			par.reset()
			return None
		
		# Skip readOnly or disabled parameters
		try:
			if par.readOnly or not par.enable:
				return None
		except Exception:
			pass
		
		# Capture current state before reset
		par_path = self._par_path(par)
		old_mode = par.mode
		old_expr = par.expr if par.mode == ParMode.EXPRESSION else None
		old_bind_expr = par.bindExpr if par.mode == ParMode.BIND else None
		
		if par.isMenu:
			current_value = par.menuIndex
		else:
			current_value = par.eval()
		
		# Perform the reset
		par.reset()
		
		# Get reset state
		new_mode = par.mode
		new_expr = par.expr if par.mode == ParMode.EXPRESSION else None
		new_bind_expr = par.bindExpr if par.mode == ParMode.BIND else None
		
		if par.isMenu:
			reset_value = par.menuIndex
		else:
			reset_value = par.eval()
		
		return {
			'par_path': par_path,
			'old_value': current_value,
			'new_value': reset_value,
			'old_mode': old_mode,
			'new_mode': new_mode,
			'old_expr': old_expr,
			'new_expr': new_expr,
			'old_bind_expr': old_bind_expr,
			'new_bind_expr': new_bind_expr,
			'is_menu': par.isMenu,
			'par_name': par.name
		}
	
	def reset_parameter_with_undo(self, par: 'Par'):
		"""Reset a parameter and create undo action.
		
		Args:
			par: The parameter to reset
		"""
		if not self.parent.evalEnableundo:
			try:
				if not (par.readOnly or not par.enable):
					par.reset()
			except Exception:
				pass
			return
		
		# Capture state, reset, and get info
		reset_info = self._capture_and_reset_parameter(par)
		if not reset_info:
			return
		
		# Create undo action
		ui.undo.startBlock(f'Reset {par.name}')
		try:
			ui.undo.addCallback(self._undo_reset_callback, reset_info)
		finally:
			ui.undo.endBlock()
	
	def reset_parameter_with_multi_undo(self, par: 'Par', additional_pars: list):
		"""Reset a parameter + additional parameters and create grouped undo.
		
		Args:
			par: The main parameter to reset
			additional_pars: List of additional parameters to reset simultaneously
		"""
		all_pars = list(self._iter_filtered_pars(par, additional_pars, skip_pulse=False))
		
		if not self.parent.evalEnableundo:
			# Reset all without undo
			for p in all_pars:
				try:
					if not (p.readOnly or not p.enable):
						p.reset()
				except Exception:
					pass
			return
		
		# Capture state and reset all parameters
		reset_info_list = []
		for p in all_pars:
			reset_info = self._capture_and_reset_parameter(p)
			if reset_info:
				reset_info_list.append(reset_info)
		
		if not reset_info_list:
			return
		
		# Create single undo block for all parameters
		if len(reset_info_list) == 1:
			block_name = f'Reset {par.name}'
		else:
			block_name = f'Reset {par.name} (Multi-Op)'
		
		ui.undo.startBlock(block_name)
		try:
			for reset_info in reset_info_list:
				ui.undo.addCallback(self._undo_reset_callback, reset_info)
		finally:
			ui.undo.endBlock()
	
	def reset_pargroup_with_multi_undo(self, par_group: 'ParGroup', additional_pars: list):
		"""Reset a ParGroup + additional parameters and create grouped undo.
		
		Args:
			par_group: The main ParGroup to reset
			additional_pars: List of additional parameters to reset simultaneously
		"""
		# Collect all parameters to reset (ParGroup + additionals)
		pargroup_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			validator=self._is_resettable_parameter,
			skip_pulse=False
		))
		additional = list(self._iter_filtered_pars(additional_pars, skip_pulse=False))
		all_pars = pargroup_pars + additional
		
		if not self.parent.evalEnableundo:
			# Reset all without undo
			for p in all_pars:
				try:
					if not (p.readOnly or not p.enable):
						p.reset()
				except Exception:
					pass
			return
		
		# Capture state and reset all parameters
		reset_info_list = []
		for p in all_pars:
			reset_info = self._capture_and_reset_parameter(p)
			if reset_info:
				reset_info_list.append(reset_info)
		
		if not reset_info_list:
			return
		
		# Get group name
		group_name = self._safe_group_name(par_group)
		
		# Create single undo block for all parameters
		ui.undo.startBlock(f'Reset {group_name} ParGroup (Multi-Op)')
		try:
			for reset_info in reset_info_list:
				ui.undo.addCallback(self._undo_reset_callback, reset_info)
		finally:
			ui.undo.endBlock()
	
	def reset_pargroup_with_undo(self, par_group: 'ParGroup'):
		"""Reset all parameters in a ParGroup and create undo action.
		
		Args:
			par_group: The ParGroup to reset
		"""
		valid_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			validator=self._is_resettable_parameter,
			skip_pulse=False
		))
		
		if not self.parent.evalEnableundo:
			for par in valid_pars:
				try:
					if not (par.readOnly or not par.enable):
						par.reset()
				except Exception:
					pass
			return
		
		# Capture state and reset all valid parameters
		reset_info_list = []
		for par in valid_pars:
			reset_info = self._capture_and_reset_parameter(par)
			if reset_info:
				reset_info_list.append(reset_info)
		
		if not reset_info_list:
			return
		
		group_name = self._safe_group_name(par_group)
		
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
			
			# Determine target state based on undo/redo
			if isUndo:
				# Restore old state
				target_value = info['old_value']
				target_mode = info['old_mode']
				target_expr = info['old_expr']
				target_bind_expr = info['old_bind_expr']
			else:
				# Restore reset state
				target_value = info['new_value']
				target_mode = info['new_mode']
				target_expr = info['new_expr']
				target_bind_expr = info['new_bind_expr']
			
			# Restore mode first
			par.mode = target_mode
			
			# Restore expression or bind expression if applicable
			if target_mode == ParMode.EXPRESSION and target_expr is not None:
				par.expr = target_expr
			elif target_mode == ParMode.EXPORT and target_bind_expr is not None:
				par.bindExpr = target_bind_expr
			elif target_mode == ParMode.CONSTANT or target_mode == ParMode.BIND:
				# Apply value for constant/bind modes
				if is_menu:
					par.menuIndex = target_value
				else:
					par.val = target_value
			
			# Update display if this is the active parameter
			# Check if the parameter is part of the active parameter (single Par or ParGroup)
			active_par = self.parent.activePar
			if active_par is not None:
				if active_par == par:
					# Direct match (single parameter)
					self.parent.display_manager.update_parameter_display(par)
				elif ParameterValidator.is_pargroup(active_par):
					# Check if this parameter is part of the active ParGroup
					# Iterate through ParGroup to check membership (same logic as onActiveValueChange)
					try:
						for par_in_group in active_par:
							if par_in_group.owner == par.owner and par_in_group.name == par.name:
								# Update display with the entire ParGroup (same as normal operation)
								self.parent.display_manager.update_parameter_display(active_par)
								break
					except:
						pass
			
		except Exception as e:
			pass
	
	def set_default_with_undo(self, par: 'Par'):
		"""Set parameter default to current value and create undo action.
		If parameter is in EXPRESSION mode, sets defaultMode and defaultExpr.
		If parameter is in BIND mode, sets defaultMode and defaultBindExpr.
		If parameter is in EXPORT mode, sets default value and defaultMode to CONSTANT.
		
		Args:
			par: The parameter to set default for
		"""
		if not par.isCustom:
			return
		
		# Check parameter mode
		is_expression_mode = par.mode == ParMode.EXPRESSION
		is_bind_mode = par.mode == ParMode.BIND
		is_export_mode = par.mode == ParMode.EXPORT
		
		# Capture old values
		old_default = par.default
		old_default_mode = par.defaultMode if hasattr(par, 'defaultMode') else None
		old_default_expr = par.defaultExpr if hasattr(par, 'defaultExpr') else None
		old_default_bind_expr = par.defaultBindExpr if hasattr(par, 'defaultBindExpr') else None
		
		# Capture new values before applying changes
		if is_expression_mode:
			new_default_expr = par.expr
		elif is_bind_mode:
			new_default_bind_expr = par.bindExpr
		elif is_export_mode:
			new_default = par.eval()  # For EXPORT, capture the evaluated value
		else:
			new_default = par.eval()
		
		# Apply the change
		if is_expression_mode:
			# Set defaultMode and defaultExpr for expression parameters
			par.defaultMode = ParMode.EXPRESSION
			par.defaultExpr = new_default_expr
		elif is_bind_mode:
			# Set defaultMode and defaultBindExpr for bind parameters
			par.defaultMode = ParMode.BIND
			par.defaultBindExpr = new_default_bind_expr
		elif is_export_mode:
			# For EXPORT mode, set default value and defaultMode to CONSTANT
			# (EXPORT cannot be set as default mode)
			par.default = new_default
			par.defaultMode = ParMode.CONSTANT
		else:
			# Set default value for constant parameters
			par.default = new_default
		
		if not self.parent.evalEnableundo:
			return
		
		# Create undo action
		par_path = f"{par.owner.path}:{par.name}"
		ui.undo.startBlock(f'Set Default {par.name}')
		try:
			if is_expression_mode:
				undo_info = {
					'par_path': par_path,
					'old_default': old_default,
					'new_default': old_default,  # Not used for expression mode
					'old_default_mode': old_default_mode,
					'new_default_mode': ParMode.EXPRESSION,
					'old_default_expr': old_default_expr,
					'new_default_expr': new_default_expr,
					'old_default_bind_expr': old_default_bind_expr,
					'new_default_bind_expr': None,
					'par_name': par.name,
					'is_expression_mode': True,
					'is_bind_mode': False
				}
			elif is_bind_mode:
				undo_info = {
					'par_path': par_path,
					'old_default': old_default,
					'new_default': old_default,  # Not used for bind mode
					'old_default_mode': old_default_mode,
					'new_default_mode': ParMode.BIND,
					'old_default_expr': old_default_expr,
					'new_default_expr': None,
					'old_default_bind_expr': old_default_bind_expr,
					'new_default_bind_expr': new_default_bind_expr,
					'par_name': par.name,
					'is_expression_mode': False,
					'is_bind_mode': True,
					'is_export_mode': False
				}
			elif is_export_mode:
				undo_info = {
					'par_path': par_path,
					'old_default': old_default,
					'new_default': new_default,
					'old_default_mode': old_default_mode,
					'new_default_mode': ParMode.CONSTANT,
					'old_default_expr': old_default_expr,
					'new_default_expr': None,
					'old_default_bind_expr': old_default_bind_expr,
					'new_default_bind_expr': None,
					'par_name': par.name,
					'is_expression_mode': False,
					'is_bind_mode': False,
					'is_export_mode': True
				}
			else:
				undo_info = {
					'par_path': par_path,
					'old_default': old_default,
					'new_default': new_default,
					'old_default_mode': old_default_mode,
					'new_default_mode': None,
					'old_default_expr': old_default_expr,
					'new_default_expr': None,
					'old_default_bind_expr': old_default_bind_expr,
					'new_default_bind_expr': None,
					'par_name': par.name,
					'is_expression_mode': False,
					'is_bind_mode': False,
					'is_export_mode': False
				}
			ui.undo.addCallback(self._undo_set_default_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_default_with_multi_undo(self, par: 'Par', additional_pars: list):
		"""Set default for parameter + additional parameters with grouped undo.
		If parameters are in EXPRESSION mode, sets defaultMode and defaultExpr.
		If parameters are in BIND mode, sets defaultMode and defaultBindExpr.
		If parameters are in EXPORT mode, sets default value and defaultMode to CONSTANT.
		
		Args:
			par: The main parameter
			additional_pars: List of additional parameters
		"""
		all_pars = list(self._iter_filtered_pars(par, additional_pars, require_custom=True, skip_pulse=False))
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			# Check parameter mode
			is_expression_mode = p.mode == ParMode.EXPRESSION
			is_bind_mode = p.mode == ParMode.BIND
			is_export_mode = p.mode == ParMode.EXPORT
			
			# Capture old values
			old_default = p.default
			old_default_mode = p.defaultMode if hasattr(p, 'defaultMode') else None
			old_default_expr = p.defaultExpr if hasattr(p, 'defaultExpr') else None
			old_default_bind_expr = p.defaultBindExpr if hasattr(p, 'defaultBindExpr') else None
			
			# Capture new values before applying changes
			if is_expression_mode:
				new_default_expr = p.expr
			elif is_bind_mode:
				new_default_bind_expr = p.bindExpr
			elif is_export_mode:
				new_default = p.eval()  # For EXPORT, capture the evaluated value
			else:
				new_default = p.eval()
			
			# Apply the change
			if is_expression_mode:
				# Set defaultMode and defaultExpr for expression parameters
				p.defaultMode = ParMode.EXPRESSION
				p.defaultExpr = new_default_expr
			elif is_bind_mode:
				# Set defaultMode and defaultBindExpr for bind parameters
				p.defaultMode = ParMode.BIND
				p.defaultBindExpr = new_default_bind_expr
			elif is_export_mode:
				# For EXPORT mode, set default value and defaultMode to CONSTANT
				# (EXPORT cannot be set as default mode)
				p.default = new_default
				p.defaultMode = ParMode.CONSTANT
			else:
				# Set default value for constant parameters
				p.default = new_default
			
			if self.parent.evalEnableundo:
				if is_expression_mode:
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': old_default,  # Not used for expression mode
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.EXPRESSION,
						'old_default_expr': old_default_expr,
						'new_default_expr': new_default_expr,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': True,
						'is_bind_mode': False
					})
				elif is_bind_mode:
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': old_default,  # Not used for bind mode
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.BIND,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': new_default_bind_expr,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': True,
						'is_export_mode': False
					})
				elif is_export_mode:
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': new_default,
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.CONSTANT,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': False,
						'is_export_mode': True
					})
				else:
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': new_default,
						'old_default_mode': old_default_mode,
						'new_default_mode': None,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': False,
						'is_export_mode': False
					})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Create grouped undo
		block_name = f'Set Default {par.name} (Multi-Op)' if len(undo_info_list) > 1 else f'Set Default {par.name}'
		ui.undo.startBlock(block_name)
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_default_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_default_pargroup_with_undo(self, par_group: 'ParGroup'):
		"""Set default for all parameters in a ParGroup and create undo action.
		If parameters are in EXPRESSION mode, sets defaultMode and defaultExpr.
		If parameters are in BIND mode, sets defaultMode and defaultBindExpr.
		If parameters are in EXPORT mode, sets default value and defaultMode to CONSTANT.
		
		Args:
			par_group: The ParGroup to set defaults for
		"""
		# Collect all custom parameters from ParGroup
		# Include ALL modes (CONSTANT, EXPRESSION, BIND, EXPORT) since we want to capture defaults for all
		all_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			require_custom=True,
			skip_pulse=False
		))
		
		if not all_pars:
			return
		
		# Set individual parameter defaults (each parameter can have its own defaultMode/defaultExpr/defaultBindExpr)
		# Treat each parameter separately - do NOT set ParGroup-level tuples as that would overwrite other parameters
		undo_info_list = []
		debug(f'all pars: {all_pars}')
		for p in all_pars:
			# Check parameter mode
			is_expression_mode = p.mode == ParMode.EXPRESSION
			is_bind_mode = p.mode == ParMode.BIND
			is_export_mode = p.mode == ParMode.EXPORT
			debug(f'checking mode for {p.name}: expression mode: {is_expression_mode}, bind mode: {is_bind_mode}, export mode: {is_export_mode}')
			# Capture old values for individual parameter undo
			old_default = p.default
			old_default_mode = p.defaultMode if hasattr(p, 'defaultMode') else None
			old_default_expr = p.defaultExpr if hasattr(p, 'defaultExpr') and is_expression_mode else None
			old_default_bind_expr = p.defaultBindExpr if hasattr(p, 'defaultBindExpr') and is_bind_mode else None
			
			# Set individual parameter defaults based on mode
			if is_expression_mode:
				# Set defaultMode and defaultExpr for expression parameters
				p.defaultMode = ParMode.EXPRESSION
				p.defaultExpr = p.expr
				debug(f'setting default mode and expr for {p.name}')
			elif is_bind_mode:
				# Set defaultMode and defaultBindExpr for bind/export parameters
				p.defaultMode = p.mode  # Keep the current mode (BIND or EXPORT)
				p.defaultBindExpr = p.bindExpr
				debug(f'setting default mode and bind expr for {p.name}')
			else:
				# Set default value for constant parameters
				p.default = p.eval()
			
			if self.parent.evalEnableundo:
				if is_expression_mode:
					new_default_expr = p.expr
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': old_default,  # Not used for expression mode
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.EXPRESSION,
						'old_default_expr': old_default_expr,
						'new_default_expr': new_default_expr,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': True,
						'is_bind_mode': False,
						'is_pargroup': True
					})
				elif is_bind_mode:
					new_default_bind_expr = p.bindExpr
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': old_default,  # Not used for bind mode
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.BIND,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': new_default_bind_expr,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': True,
						'is_export_mode': False,
						'is_pargroup': True
					})
				elif is_export_mode:
					new_default = p.eval()
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': new_default,
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.CONSTANT,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': False,
						'is_export_mode': True,
						'is_pargroup': True
					})
				else:
					new_default = p.eval()
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': new_default,
						'old_default_mode': old_default_mode,
						'new_default_mode': None,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': False,
						'is_export_mode': False,
						'is_pargroup': True
					})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Get group name
		group_name = self._safe_group_name(par_group)
		
		# Create grouped undo
		ui.undo.startBlock(f'Set Default {group_name} ParGroup')
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_default_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_default_pargroup_with_multi_undo(self, par_group: 'ParGroup', additional_pars: list):
		"""Set default for ParGroup + additional parameters and create grouped undo.
		If parameters are in EXPRESSION mode, sets defaultMode and defaultExpr.
		If parameters are in BIND mode, sets defaultMode and defaultBindExpr.
		If parameters are in EXPORT mode, sets default value and defaultMode to CONSTANT.
		
		Args:
			par_group: The main ParGroup to set defaults for
			additional_pars: List of additional parameters to set defaults simultaneously
		"""
		# Collect all custom parameters from ParGroup
		# Include ALL modes (CONSTANT, EXPRESSION, BIND, EXPORT) since we want to capture defaults for all
		pargroup_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			require_custom=True,
			skip_pulse=False
		))
		
		# Add additional custom parameters
		all_additional_pars = list(self._iter_filtered_pars(additional_pars, require_custom=True, skip_pulse=False))
		
		# Handle ParGroup defaults - set individual parameter defaults only
		# Do NOT set ParGroup-level tuples as that would overwrite other parameters in the group
		if pargroup_pars:
			for p in pargroup_pars:
				is_expression_mode = p.mode == ParMode.EXPRESSION
				is_export_mode = p.mode == ParMode.EXPORT
				is_bind_mode = p.mode == ParMode.BIND or is_export_mode
				
				if is_expression_mode:
					# Set defaultMode and defaultExpr for expression parameters
					p.defaultMode = ParMode.EXPRESSION
					p.defaultExpr = p.expr
				elif is_bind_mode:
					# Set defaultMode and defaultBindExpr for bind/export parameters
					p.defaultMode = p.mode  # Keep the current mode (BIND or EXPORT)
					p.defaultBindExpr = p.bindExpr
				else:
					# Set default value for constant parameters
					p.default = p.eval()
		
		# Handle additional parameters (individual Pars, not part of ParGroup)
		all_pars = pargroup_pars + all_additional_pars
		
		if not all_pars:
			return
		
		# Capture old values and create undo info for all parameters
		undo_info_list = []
		for p in all_pars:
			# Check parameter mode
			is_expression_mode = p.mode == ParMode.EXPRESSION
			is_export_mode = p.mode == ParMode.EXPORT
			is_bind_mode = p.mode == ParMode.BIND or is_export_mode
			
			# Capture old values
			old_default = p.default
			old_default_mode = p.defaultMode if hasattr(p, 'defaultMode') else None
			old_default_expr = p.defaultExpr if hasattr(p, 'defaultExpr') else None
			old_default_bind_expr = p.defaultBindExpr if hasattr(p, 'defaultBindExpr') else None
			
			# For ParGroup parameters, we already set defaults above
			# For additional parameters, set defaults now
			if p not in pargroup_pars:
				if is_expression_mode:
					p.defaultMode = ParMode.EXPRESSION
					p.defaultExpr = p.expr
				elif is_bind_mode:
					p.defaultMode = ParMode.BIND
					p.defaultBindExpr = p.bindExpr
				elif is_export_mode:
					# For EXPORT mode, set default value and defaultMode to CONSTANT
					# (EXPORT cannot be set as default mode)
					p.default = p.eval()
					p.defaultMode = ParMode.CONSTANT
				else:
					p.default = p.eval()
			
			if self.parent.evalEnableundo:
				if is_expression_mode:
					new_default_expr = p.expr
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': old_default,  # Not used for expression mode
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.EXPRESSION,
						'old_default_expr': old_default_expr,
						'new_default_expr': new_default_expr,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': True,
						'is_bind_mode': False,
						'is_pargroup': p in pargroup_pars
					})
				elif is_bind_mode:
					new_default_bind_expr = p.bindExpr
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': old_default,  # Not used for bind mode
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.BIND,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': new_default_bind_expr,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': True,
						'is_export_mode': False,
						'is_pargroup': p in pargroup_pars
					})
				elif is_export_mode:
					new_default = p.eval()
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': new_default,
						'old_default_mode': old_default_mode,
						'new_default_mode': ParMode.CONSTANT,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': False,
						'is_export_mode': True,
						'is_pargroup': p in pargroup_pars
					})
				else:
					new_default = p.eval()
					undo_info_list.append({
						'par_path': self._par_path(p),
						'old_default': old_default,
						'new_default': new_default,
						'old_default_mode': old_default_mode,
						'new_default_mode': None,
						'old_default_expr': old_default_expr,
						'new_default_expr': None,
						'old_default_bind_expr': old_default_bind_expr,
						'new_default_bind_expr': None,
						'par_name': p.name,
						'is_expression_mode': False,
						'is_bind_mode': False,
						'is_pargroup': p in pargroup_pars
					})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		group_name = self._safe_group_name(par_group)
		
		# Create single undo block for all parameters
		ui.undo.startBlock(f'Set Default {group_name} ParGroup (Multi-Op)')
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_default_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def _undo_set_default_callback(self, isUndo, info):
		"""Callback for undoing parameter default change.
		Handles regular defaults, expression mode defaults (defaultMode/defaultExpr),
		and bind mode defaults (defaultMode/defaultBindExpr).
		Also handles ParGroup defaults when applicable."""
		par_path = info['par_path']
		
		try:
			owner_path, par_name = par_path.rsplit(':', 1)
			owner_op = op(owner_path)
			
			if owner_op is None:
				return
			
			par = owner_op.par[par_name]
			if par is None or not par.isCustom:
				return
			
			# Check if this is part of a ParGroup
			is_pargroup = info.get('is_pargroup', False)
			
			# Note: For ParGroup parameters, we only restore individual parameter defaults
			# We do NOT restore ParGroup-level tuples to avoid overwriting other parameters
			
			# Check parameter mode
			is_expression_mode = info.get('is_expression_mode', False)
			is_bind_mode = info.get('is_bind_mode', False)
			is_export_mode = info.get('is_export_mode', False)
			
			# Set value based on undo/redo (for individual parameter)
			if is_expression_mode:
				# Handle expression mode defaults
				if isUndo:
					# Restore old defaultMode and defaultExpr
					if 'old_default_mode' in info:
						if info['old_default_mode'] is not None:
							par.defaultMode = info['old_default_mode']
					if 'old_default_expr' in info:
						if info['old_default_expr'] is not None:
							par.defaultExpr = info['old_default_expr']
				else:
					# Restore new defaultMode and defaultExpr
					if 'new_default_mode' in info and info['new_default_mode'] is not None:
						par.defaultMode = info['new_default_mode']
					if 'new_default_expr' in info and info['new_default_expr'] is not None:
						par.defaultExpr = info['new_default_expr']
			elif is_bind_mode:
				# Handle bind mode defaults
				if isUndo:
					# Restore old defaultMode and defaultBindExpr
					if 'old_default_mode' in info:
						if info['old_default_mode'] is not None:
							par.defaultMode = info['old_default_mode']
					if 'old_default_bind_expr' in info:
						if info['old_default_bind_expr'] is not None:
							par.defaultBindExpr = info['old_default_bind_expr']
				else:
					# Restore new defaultMode and defaultBindExpr
					if 'new_default_mode' in info and info['new_default_mode'] is not None:
						par.defaultMode = info['new_default_mode']
					if 'new_default_bind_expr' in info and info['new_default_bind_expr'] is not None:
						par.defaultBindExpr = info['new_default_bind_expr']
			elif is_export_mode:
				# Handle export mode defaults (stored as CONSTANT mode)
				if isUndo:
					par.default = info['old_default']
					if 'old_default_mode' in info:
						if info['old_default_mode'] is not None:
							par.defaultMode = info['old_default_mode']
				else:
					par.default = info['new_default']
					if 'new_default_mode' in info and info['new_default_mode'] is not None:
						par.defaultMode = info['new_default_mode']
			else:
				# Handle regular defaults
				if isUndo:
					par.default = info['old_default']
				else:
					par.default = info['new_default']
			
			# Update display if this is the active parameter
			# Check if the parameter is part of the active parameter (single Par or ParGroup)
			active_par = self.parent.activePar
			if active_par is not None:
				if active_par == par:
					# Direct match (single parameter)
					self.parent.display_manager.update_parameter_display(par)
				elif ParameterValidator.is_pargroup(active_par):
					# Check if this parameter is part of the active ParGroup
					# Iterate through ParGroup to check membership (same logic as onActiveValueChange)
					try:
						for par_in_group in active_par:
							if par_in_group.owner == par.owner and par_in_group.name == par.name:
								# Update display with the entire ParGroup (same as normal operation)
								self.parent.display_manager.update_parameter_display(active_par)
								break
					except:
						pass
			
		except Exception as e:
			pass
	
	def set_norm_with_undo(self, par: 'Par', is_min: bool):
		"""Set parameter norm min/max to current value and create undo action.
		
		Args:
			par: The parameter to set norm for
			is_min: True for normMin, False for normMax
		"""
		if not par.isCustom:
			return
		
		_val = par.eval()
		
		# Check if valid
		if is_min:
			if _val == par.normMax:
				return
			old_norm = par.normMin
			old_minmax = par.min
			par.normMin = _val
			par.min = _val
		else:
			if _val == par.normMin:
				return
			old_norm = par.normMax
			old_minmax = par.max
			par.normMax = _val
			par.max = _val
		
		if not self.parent.evalEnableundo:
			return
		
		# Create undo action
		par_path = f"{par.owner.path}:{par.name}"
		ui.undo.startBlock(f'Set {"Min" if is_min else "Max"} {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'is_min': is_min,
				'old_norm': old_norm,
				'new_norm': _val,
				'old_minmax': old_minmax,
				'new_minmax': _val,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_set_norm_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_norm_with_multi_undo(self, par: 'Par', additional_pars: list, is_min: bool):
		"""Set norm for parameter + additional parameters with grouped undo.
		
		Args:
			par: The main parameter
			additional_pars: List of additional parameters
			is_min: True for normMin, False for normMax
		"""
		all_pars = list(self._iter_filtered_pars(par, additional_pars, require_custom=True, skip_pulse=False))
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			_val = p.eval()
			
			# Check if valid and apply
			if is_min:
				if _val == p.normMax:
					continue
				old_norm = p.normMin
				old_minmax = p.min
				p.normMin = _val
				p.min = _val
			else:
				if _val == p.normMin:
					continue
				old_norm = p.normMax
				old_minmax = p.max
				p.normMax = _val
				p.max = _val
			
			if self.parent.evalEnableundo:
				undo_info_list.append({
					'par_path': self._par_path(p),
					'is_min': is_min,
					'old_norm': old_norm,
					'new_norm': _val,
					'old_minmax': old_minmax,
					'new_minmax': _val,
					'par_name': p.name
				})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Create grouped undo
		min_max_str = "Min" if is_min else "Max"
		block_name = f'Set {min_max_str} {par.name} (Multi-Op)' if len(undo_info_list) > 1 else f'Set {min_max_str} {par.name}'
		ui.undo.startBlock(block_name)
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_norm_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_norm_pargroup_with_undo(self, par_group: 'ParGroup', is_min: bool):
		"""Set norm min or max for all parameters in a ParGroup and create undo action.
		
		Args:
			par_group: The ParGroup to set norm for
			is_min: True for normMin, False for normMax
		"""
		# Collect all custom parameters from ParGroup
		all_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			require_custom=True,
			validator=ParameterValidator.is_valid_parameter,
			skip_pulse=False
		))
		
		if not all_pars:
			return
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			_val = p.eval()
			
			# Check if valid and apply
			if is_min:
				if _val == p.normMax:
					continue
				old_norm = p.normMin
				old_minmax = p.min
				p.normMin = _val
				p.min = _val
			else:
				if _val == p.normMin:
					continue
				old_norm = p.normMax
				old_minmax = p.max
				p.normMax = _val
				p.max = _val
			
			if self.parent.evalEnableundo:
				undo_info_list.append({
					'par_path': self._par_path(p),
					'is_min': is_min,
					'old_norm': old_norm,
					'new_norm': _val,
					'old_minmax': old_minmax,
					'new_minmax': _val,
					'par_name': p.name
				})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Get group name
		group_name = self._safe_group_name(par_group)
		
		# Create grouped undo
		min_max_str = "Min" if is_min else "Max"
		ui.undo.startBlock(f'Set {min_max_str} {group_name} ParGroup')
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_norm_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_norm_pargroup_with_multi_undo(self, par_group: 'ParGroup', additional_pars: list, is_min: bool):
		"""Set norm for ParGroup + additional parameters and create grouped undo.
		
		Args:
			par_group: The main ParGroup to set norm for
			additional_pars: List of additional parameters to set norm simultaneously
			is_min: True for normMin, False for normMax
		"""
		# Collect all custom parameters from ParGroup
		pargroup_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			require_custom=True,
			validator=ParameterValidator.is_valid_parameter,
			skip_pulse=False
		))
		additional = list(self._iter_filtered_pars(additional_pars, require_custom=True, skip_pulse=False))
		all_pars = pargroup_pars + additional
		
		if not all_pars:
			return
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			_val = p.eval()
			
			# Check if valid and apply
			if is_min:
				if _val == p.normMax:
					continue
				old_norm = p.normMin
				old_minmax = p.min
				p.normMin = _val
				p.min = _val
			else:
				if _val == p.normMin:
					continue
				old_norm = p.normMax
				old_minmax = p.max
				p.normMax = _val
				p.max = _val
			
			if self.parent.evalEnableundo:
				undo_info_list.append({
					'par_path': self._par_path(p),
					'is_min': is_min,
					'old_norm': old_norm,
					'new_norm': _val,
					'old_minmax': old_minmax,
					'new_minmax': _val,
					'par_name': p.name
				})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Get group name
		group_name = self._safe_group_name(par_group)
		
		# Create single undo block for all parameters
		min_max_str = "Min" if is_min else "Max"
		ui.undo.startBlock(f'Set {min_max_str} {group_name} ParGroup (Multi-Op)')
		try:
			for undo_info in undo_info_list:
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
			# Check if the parameter is part of the active parameter (single Par or ParGroup)
			active_par = self.parent.activePar
			if active_par is not None:
				if active_par == par:
					# Direct match (single parameter)
					self.parent.display_manager.update_parameter_display(par)
				elif ParameterValidator.is_pargroup(active_par):
					# Check if this parameter is part of the active ParGroup
					# Iterate through ParGroup to check membership (same logic as onActiveValueChange)
					try:
						for par_in_group in active_par:
							if par_in_group.owner == par.owner and par_in_group.name == par.name:
								# Update display with the entire ParGroup (same as normal operation)
								self.parent.display_manager.update_parameter_display(active_par)
								break
					except:
						pass
			
		except Exception as e:
			pass
	
	def set_clamp_with_undo(self, par: 'Par', min_max: str):
		"""Toggle parameter clamp and create undo action.
		
		Args:
			par: The parameter to toggle clamp for
			min_max: 'min', 'max', or 'both'
		"""
		if not par.isCustom:
			return
		
		# Capture old values
		old_clamp_min = par.clampMin
		old_clamp_max = par.clampMax
		
		# Determine what's changing
		changed_min = (min_max == 'min' or min_max == 'both')
		changed_max = (min_max == 'max' or min_max == 'both')
		
		# Apply changes
		if changed_min:
			par.clampMin = not par.clampMin
		if changed_max:
			par.clampMax = not par.clampMax
		
		if not self.parent.evalEnableundo:
			return
		
		# Create undo action
		par_path = f"{par.owner.path}:{par.name}"
		ui.undo.startBlock(f'Toggle Clamp {par.name}')
		try:
			undo_info = {
				'par_path': par_path,
				'changed_min': changed_min,
				'changed_max': changed_max,
				'old_clamp_min': old_clamp_min,
				'new_clamp_min': par.clampMin,
				'old_clamp_max': old_clamp_max,
				'new_clamp_max': par.clampMax,
				'par_name': par.name
			}
			ui.undo.addCallback(self._undo_set_clamp_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_clamp_with_multi_undo(self, par: 'Par', additional_pars: list, min_max: str):
		"""Toggle clamp for parameter + additional parameters with grouped undo.
		
		Args:
			par: The main parameter
			additional_pars: List of additional parameters
			min_max: 'min', 'max', or 'both'
		"""
		all_pars = list(self._iter_filtered_pars(par, additional_pars, require_custom=True, skip_pulse=False))
		
		# Determine what's changing
		changed_min = (min_max == 'min' or min_max == 'both')
		changed_max = (min_max == 'max' or min_max == 'both')
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			old_clamp_min = p.clampMin
			old_clamp_max = p.clampMax
			
			# Apply changes
			if changed_min:
				p.clampMin = not p.clampMin
			if changed_max:
				p.clampMax = not p.clampMax
			
			if self.parent.evalEnableundo:
				undo_info_list.append({
					'par_path': self._par_path(p),
					'changed_min': changed_min,
					'changed_max': changed_max,
					'old_clamp_min': old_clamp_min,
					'new_clamp_min': p.clampMin,
					'old_clamp_max': old_clamp_max,
					'new_clamp_max': p.clampMax,
					'par_name': p.name
				})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Create grouped undo
		block_name = f'Toggle Clamp {par.name} (Multi-Op)' if len(undo_info_list) > 1 else f'Toggle Clamp {par.name}'
		ui.undo.startBlock(block_name)
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_clamp_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_clamp_pargroup_with_undo(self, par_group: 'ParGroup', min_max: str):
		"""Toggle clamp for all parameters in a ParGroup and create undo action.
		
		Args:
			par_group: The ParGroup to toggle clamp for
			min_max: 'min', 'max', or 'both'
		"""
		# Collect all custom parameters from ParGroup
		all_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			require_custom=True,
			validator=ParameterValidator.is_valid_parameter,
			skip_pulse=False
		))
		
		if not all_pars:
			return
		
		# Determine what's changing
		changed_min = (min_max == 'min' or min_max == 'both')
		changed_max = (min_max == 'max' or min_max == 'both')
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			old_clamp_min = p.clampMin
			old_clamp_max = p.clampMax
			
			# Apply changes
			if changed_min:
				p.clampMin = not p.clampMin
			if changed_max:
				p.clampMax = not p.clampMax
			
			if self.parent.evalEnableundo:
				undo_info_list.append({
					'par_path': self._par_path(p),
					'changed_min': changed_min,
					'changed_max': changed_max,
					'old_clamp_min': old_clamp_min,
					'old_clamp_max': old_clamp_max,
					'new_clamp_min': p.clampMin,
					'new_clamp_max': p.clampMax,
					'par_name': p.name
				})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Get group name
		group_name = self._safe_group_name(par_group)
		
		# Create grouped undo
		ui.undo.startBlock(f'Toggle Clamp {group_name} ParGroup')
		try:
			for undo_info in undo_info_list:
				ui.undo.addCallback(self._undo_set_clamp_callback, undo_info)
		finally:
			ui.undo.endBlock()
	
	def set_clamp_pargroup_with_multi_undo(self, par_group: 'ParGroup', additional_pars: list, min_max: str):
		"""Toggle clamp for ParGroup + additional parameters and create grouped undo.
		
		Args:
			par_group: The main ParGroup to toggle clamp for
			additional_pars: List of additional parameters to toggle clamp simultaneously
			min_max: 'min', 'max', or 'both'
		"""
		# Collect all custom parameters from ParGroup
		pargroup_pars = list(self._iter_filtered_pars(
			par_group,
			skip_units=True,
			require_custom=True,
			validator=ParameterValidator.is_valid_parameter,
			skip_pulse=False
		))
		additional = list(self._iter_filtered_pars(additional_pars, require_custom=True, skip_pulse=False))
		all_pars = pargroup_pars + additional
		
		if not all_pars:
			return
		
		# Determine what's changing
		changed_min = (min_max == 'min' or min_max == 'both')
		changed_max = (min_max == 'max' or min_max == 'both')
		
		# Capture old values and apply changes
		undo_info_list = []
		for p in all_pars:
			old_clamp_min = p.clampMin
			old_clamp_max = p.clampMax
			
			# Apply changes
			if changed_min:
				p.clampMin = not p.clampMin
			if changed_max:
				p.clampMax = not p.clampMax
			
			if self.parent.evalEnableundo:
				undo_info_list.append({
					'par_path': self._par_path(p),
					'changed_min': changed_min,
					'changed_max': changed_max,
					'old_clamp_min': old_clamp_min,
					'old_clamp_max': old_clamp_max,
					'new_clamp_min': p.clampMin,
					'new_clamp_max': p.clampMax,
					'par_name': p.name
				})
		
		if not self.parent.evalEnableundo or not undo_info_list:
			return
		
		# Get group name
		group_name = self._safe_group_name(par_group)
		
		# Create single undo block for all parameters
		ui.undo.startBlock(f'Toggle Clamp {group_name} ParGroup (Multi-Op)')
		try:
			for undo_info in undo_info_list:
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
			# Check if the parameter is part of the active parameter (single Par or ParGroup)
			active_par = self.parent.activePar
			if active_par is not None:
				if active_par == par:
					# Direct match (single parameter)
					self.parent.display_manager.update_parameter_display(par)
				elif ParameterValidator.is_pargroup(active_par):
					# Check if this parameter is part of the active ParGroup
					# Iterate through ParGroup to check membership (same logic as onActiveValueChange)
					try:
						for par_in_group in active_par:
							if par_in_group.owner == par.owner and par_in_group.name == par.name:
								# Update display with the entire ParGroup (same as normal operation)
								self.parent.display_manager.update_parameter_display(active_par)
								break
					except:
						pass
			
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
			self.parent.repo_manager.set_slot_parameter(slot_idx, previous_parameter, bank_idx)
			self.parent._set_parexec_pars(previous_parameter)
			self.parent.repo_manager.set_active_slot(previous_bank_active_slot, bank_idx)
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				# Capture the current active slot before changing it
				old_active_slot = self.parent.activeSlot
				self.parent.activeSlot = previous_active_slot
				
				# Update cached active parameter
				if previous_active_slot is not None and previous_active_slot < len(self.parent.slotPars[bank_idx]):
					self.parent._activeSlotPar = self.parent.slotPars[bank_idx][previous_active_slot]
				else:
					self.parent._activeSlotPar = None
				
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
				
			# Update LEDs - update both the old active slot and the restored active slot
			self.parent.display_manager.update_slot_leds(current_slot=previous_active_slot, previous_slot=old_active_slot)
			
			# Also update the restored slot if it's different from the active slots
			if slot_idx != previous_active_slot and slot_idx != old_active_slot:
				self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
		else:
			# Redo: apply the assignment again
			new_parameter = info['new_parameter']
			
			self.parent.repo_manager.set_slot_parameter(slot_idx, new_parameter, bank_idx)
			self.parent._set_parexec_pars(new_parameter)
			self.parent.activeSlot = slot_idx
			self.parent._activeSlotPar = new_parameter  # Cache the active parameter
			self.parent.repo_manager.set_active_slot(slot_idx, bank_idx)
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				# Capture the current active slot before changing it
				old_active_slot = self.parent.activeSlot
				self.parent.activeSlot = slot_idx
				
				# Turn off hovered UI color when assigning a slot
				self.parent.ui_manager.set_hovered_ui_color(-1)
				
				# Update UI button label
				if hasattr(self.parent, 'ui_manager'):
					label = LabelFormatter.get_label_for_parameter(new_parameter, self.parent.labelDisplayMode)
					self.parent.ui_manager._set_button_label(slot_idx, label)
				
				# Update display
				self.parent.display_manager.update_parameter_display(new_parameter, bottom_text=ScreenMessages.LEARNED)
				
				# Update LEDs - update both the new active slot and the previously active slot
				self.parent.display_manager.update_slot_leds(current_slot=slot_idx, previous_slot=old_active_slot)
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
					if not ParameterValidator.is_supported_parameter_type(previous_parameter, self.parent.evalControlstrmenus):
						return
				# Handle single Par
				elif previous_parameter is None or not previous_parameter.valid:
					# Parameter no longer exists, cannot restore
					return
				# Check if single Par is still a supported type
				elif not ParameterValidator.is_supported_parameter_type(previous_parameter, self.parent.evalControlstrmenus):
					return
			except:
				# Parameter reference is completely invalid
				return
			
			self.parent.repo_manager.set_slot_parameter(slot_idx, previous_parameter, bank_idx)
			self.parent._set_parexec_pars(previous_parameter)
			self.parent.repo_manager.set_active_slot(previous_bank_active_slot, bank_idx)
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				# Capture the current active slot before changing it
				old_active_slot = self.parent.activeSlot
				self.parent.activeSlot = previous_active_slot
				
				# Update cached active parameter
				if previous_active_slot is not None and previous_active_slot < len(self.parent.slotPars[bank_idx]):
					self.parent._activeSlotPar = self.parent.slotPars[bank_idx][previous_active_slot]
				else:
					self.parent._activeSlotPar = None
				
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
				
				# Restore LEDs - update both the old active slot and the new/restored active slot
				self.parent.display_manager.update_slot_leds(current_slot=previous_active_slot, previous_slot=old_active_slot)
				
			# Also update the restored slot if it's different from the active slots
			if slot_idx != previous_active_slot and slot_idx != old_active_slot:
				self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
		else:
			# Redo: clear the slot again
			self.parent.repo_manager.clear_slot(slot_idx, bank_idx)
			self.parent._set_parexec_pars(None)
			self.parent.repo_manager.set_active_slot(None, bank_idx)
			
			# Only update UI/VSN1/activeSlot if we're currently viewing this bank
			if is_current_bank:
				# Capture the current active slot before changing it (for LED updates)
				old_active_slot = self.parent.activeSlot
				
				# Clear button label
				if hasattr(self.parent, 'ui_manager'):
					self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
				
				# If we're clearing the currently active slot, go to hover mode
				# Otherwise, keep the current active slot
				if slot_idx == old_active_slot:
					# Clearing the currently active slot -> go to hover mode
					self.parent.activeSlot = None
					self.parent._activeSlotPar = None
					
					# Restore hovered UI color if enabled (going to hover mode)
					if self.parent.evalColorhoveredui:
						self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
					else:
						self.parent.ui_manager.set_hovered_ui_color(-1)
					
					self.parent.display_manager.update_all_display(
						0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
					
					# Update slot LED
					self.parent.display_manager.update_slot_leds(current_slot=None, previous_slot=slot_idx)
					self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
				else:
					# Clearing a non-active slot -> keep current active slot
					
					# Update display based on current active slot
					if old_active_slot is not None:
						active_par = self.parent.repo_manager.get_slot_parameter(old_active_slot, bank_idx)
						if active_par is not None:
							# Keep displaying active parameter
							self.parent.display_manager.update_parameter_display(active_par)
							self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
						else:
							# Active slot is empty, go to hover
							self.parent.activeSlot = None
							self.parent._activeSlotPar = None
							self.parent.repo_manager.set_active_slot(None, bank_idx)
							if self.parent.evalColorhoveredui:
								self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
							else:
								self.parent.ui_manager.set_hovered_ui_color(-1)
							self.parent.display_manager.update_all_display(
								0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
							self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
					else:
						# No active slot, go to hover
						self.parent.activeSlot = None
						self.parent._activeSlotPar = None  # Clear cached active slot parameter
						self.parent.repo_manager.set_active_slot(None, bank_idx)
						if self.parent.evalColorhoveredui:
							self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
						else:
							self.parent.ui_manager.set_hovered_ui_color(-1)
						self.parent.display_manager.update_all_display(
							0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
						self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
					
					# Update slot LEDs - cleared slot (always) and old active slot if different
					self.parent.display_manager.update_slot_leds(current_slot=self.parent.activeSlot, previous_slot=old_active_slot)
					if slot_idx != self.parent.activeSlot and slot_idx != old_active_slot:
						self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
			else:
				# Not current bank - sync bank active slots
				if slot_idx == self.parent.repo_manager.get_active_slot(bank_idx):
					self.parent.repo_manager.set_active_slot(None, bank_idx)
		
		# Always refresh UI buttons for current bank to ensure correct state
		# (TouchDesigner's undo system may revert some UI states)
		if hasattr(self.parent, 'ui_manager') and self.parent.ui_manager:
			#self.parent.ui_manager.refresh_all_button_states()
			run("args[0].refresh_all_button_states()", self.parent.ui_manager, delayFrames=1)


