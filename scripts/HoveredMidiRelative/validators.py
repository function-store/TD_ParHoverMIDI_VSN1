
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
		
		# Handle single Par
		return par_or_group.mode in [ParMode.CONSTANT, ParMode.BIND]
	
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
	def is_supported_parameter_type(par_or_group: Union[Par, ParGroup]) -> bool:
		"""Check if parameter (or ParGroup) is a supported type for MIDI control
		
		This checks the parameter TYPE only, not whether it's valid (has expressions, etc).
		For ParGroups, all parameters must be of supported and consistent types."""
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
				any(getattr(p, f'is{type.value}') for type in SupportedParameterTypes) and not p.isString
				for p in all_pars
			)
			
			if not all_supported:
				return False
			
			# Check all parameters are of the same type (for consistent behavior)
			first_par = all_pars[0]
			for par in all_pars[1:]:
				# Compare parameter types
				if (first_par.isNumber != par.isNumber or
					first_par.isMenu != par.isMenu or
					first_par.isToggle != par.isToggle or
					first_par.isPulse != par.isPulse or
					first_par.isMomentary != par.isMomentary):
					return False  # Mixed types not supported
			
			return True
		
		# Handle single Par - just check if it's a supported type
		return any(getattr(par_or_group, f'is{type.value}') for type in SupportedParameterTypes) and not par_or_group.isString
	
	@staticmethod
	def get_validation_error(par_or_group: Union[Par, ParGroup]) -> str:
		"""Get validation error message for a parameter (or ParGroup).
		Returns ScreenMessages constant if invalid, None if valid."""
		if not ParameterValidator.is_supported_parameter_type(par_or_group):
			return ScreenMessages.UNSUPPORTED
		if not ParameterValidator.has_valid_parameters(par_or_group):
			return ScreenMessages.EXPR
		return None
