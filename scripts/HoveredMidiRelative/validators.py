from constants import *


class ParameterValidator:
	"""Helper class for parameter validation"""
	
	@staticmethod
	def is_valid_parameter(par) -> bool:
		"""Check if parameter is valid for MIDI control"""
		if par is None:
			return False
		return par.mode in [ParMode.CONSTANT, ParMode.BIND]
	
	@staticmethod
	def is_learnable_parameter(par) -> bool:
		"""Check if parameter is learnable ie valid and empty"""
		return ParameterValidator.is_valid_parameter(par) and not par.eval()

	@staticmethod
	def is_supported_parameter_type(par) -> bool:
		"""Check if parameter is supported for MIDI control"""
		return any(getattr(par, f'is{type.value}') for type in SupportedParameterTypes)
