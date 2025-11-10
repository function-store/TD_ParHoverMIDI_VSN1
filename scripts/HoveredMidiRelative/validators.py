
'''Info Header Start
Name : validators
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.179.toe
Saveversion : 2023.12120
Info Header End'''
from constants import *
from typing import Union


class ParameterValidator:
	"""Helper class for parameter validation"""
	
	@staticmethod
	def is_strmenu(par) -> bool:
		"""Check if parameter is a StrMenu (both isMenu and isString, or style == 'StrMenu')"""
		if par is None:
			return False
		# Check both old method (isMenu and isString) and new method (style == 'StrMenu')
		return (par.isMenu and par.isString) or getattr(par, 'style', None) == 'StrMenu'

	@staticmethod
	def _is_supported_parameter_type_single(par, allow_strmenus: bool = False) -> bool:
		"""Check if a single parameter is a supported type (internal helper)"""
		# Allow StrMenus (isMenu and isString both true, OR style == 'StrMenu') if the feature is enabled
		is_strmenu = (par.isMenu and par.isString) or getattr(par, 'style', None) == 'StrMenu'
		is_menu_type = par.isMenu or getattr(par, 'style', None) == 'Menu' or getattr(par, 'style', None) == 'StrMenu'

		# Check other supported types normally
		other_types_supported = any(getattr(par, f'is{type.value}') for type in SupportedParameterTypes if type.value not in ['Menu', 'StrMenu'])

		# Menu/StrMenu types get special handling with style checks
		menu_types_supported = is_menu_type and (not is_strmenu or allow_strmenus)

		return other_types_supported or menu_types_supported
	
	@staticmethod
	def is_pargroup(obj) -> bool:
		"""Check if object is a ParGroup"""
		return isinstance(obj, ParGroup)
	
	@staticmethod
	def is_valid_parameter(par_or_group: Union[Par, ParGroup]) -> bool:
		"""Check if a single parameter is valid for MIDI control
		Always checks individual parameters, not groups"""
		if par_or_group is None:
			return False
		
		# If it's a ParGroup, we should not validate the group itself
		# This method is for checking individual parameters only
		if ParameterValidator.is_pargroup(par_or_group):
			# Don't validate groups here - use has_valid_parameters instead
			return False
		valid_mode = par_or_group.mode in [ParMode.CONSTANT, ParMode.BIND]
		valid_valid = par_or_group.valid and par_or_group.enable and not par_or_group.readOnly
		# Handle single Par
		return valid_mode and valid_valid
	
	@staticmethod
	def has_valid_parameters(par_or_group: Union[Par, ParGroup]) -> bool:
		"""Check if parameter or ParGroup has at least one valid parameter
		
		For ParGroups: Returns True if ANY parameter is valid (not all)
		This allows ParGroups with mixed valid/invalid parameters to be used,
		with invalid ones being skipped during operations."""
		if par_or_group is None:
			return False
		
		# Handle ParGroup - returns True if at least ONE parameter is valid
		if ParameterValidator.is_pargroup(par_or_group):
			return any(ParameterValidator.is_valid_parameter(p) for p in par_or_group if p is not None)
		
		# Handle single Par
		return ParameterValidator.is_valid_parameter(par_or_group)
	
	@staticmethod
	def is_learnable_parameter(par_or_group: Union[Par, ParGroup]) -> bool:
		"""Check if parameter (or ParGroup) is learnable ie valid and empty
		For ParGroups, all parameters must be learnable"""
		# Handle ParGroup
		if ParameterValidator.is_pargroup(par_or_group):
			return all(
				ParameterValidator.is_valid_parameter(p) and not p.eval()
				for p in par_or_group if p is not None
			)
		
		# Handle single Par
		return ParameterValidator.is_valid_parameter(par_or_group) and not par_or_group.eval()

	@staticmethod
	def is_supported_parameter_type(par_or_group: Union[Par, ParGroup], allow_strmenus: bool = False) -> bool:
		"""Check if parameter (or ParGroup) is a supported type for MIDI control
		
		This checks the parameter TYPE only, not whether it's valid (has expressions, etc).
		For ParGroups, all parameters must be of supported and consistent types.
		
		Args:
			par_or_group: Parameter or ParGroup to check
			allow_strmenus: Whether to allow StrMenu parameters (isMenu and isString both true, or style == 'StrMenu')
		"""
		if par_or_group is None:
			return False
		
		# Handle ParGroup
		if ParameterValidator.is_pargroup(par_or_group):
			# Get all parameters from the group (regardless of validity)
			all_pars = [p for p in par_or_group if p is not None]
			
			if not all_pars:  # No parameters
				return False
			
			# Check all parameters are of supported types
			all_supported = all(
				ParameterValidator._is_supported_parameter_type_single(p, allow_strmenus)
				for p in all_pars
			)
			
			if not all_supported:
				return False
			
			# Check all parameters are of the same type (for consistent behavior)
			first_par = all_pars[0]
			for par in all_pars[1:]:
				# Compare parameter types using both methods for robustness
				if (first_par.isNumber != par.isNumber or
					first_par.isMenu != par.isMenu or
					first_par.isToggle != par.isToggle or
					first_par.isPulse != par.isPulse or
					first_par.isMomentary != par.isMomentary):
					return False  # Mixed types not supported

				# Additional check using style attribute if available
				first_style = getattr(first_par, 'style', None)
				par_style = getattr(par, 'style', None)
				if first_style is not None and par_style is not None and first_style != par_style:
					return False  # Mixed types not supported
			
			return True
		
		# Handle single Par - check if it's a supported type
		return ParameterValidator._is_supported_parameter_type_single(par_or_group, allow_strmenus)
	
	@staticmethod
	def get_validation_error(par_or_group: Union[Par, ParGroup], allow_strmenus: bool = False) -> str:
		"""Get validation error message for a parameter (or ParGroup).
		Returns ScreenMessages constant if invalid, None if valid.
		
		Args:
			par_or_group: Parameter or ParGroup to validate
			allow_strmenus: Whether to allow StrMenu parameters (isMenu and isString both true, or style == 'StrMenu')
		"""
		if not ParameterValidator.is_supported_parameter_type(par_or_group, allow_strmenus):
			return ScreenMessages.UNSUPPORTED
		if not ParameterValidator.has_valid_parameters(par_or_group):
			return ScreenMessages.EXPR
		return None
