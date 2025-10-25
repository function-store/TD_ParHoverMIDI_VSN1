
'''Info Header Start
Name : formatters
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.179.toe
Saveversion : 2023.12120
Info Header End'''
"""
Label and value formatting utilities for HoveredMidiRelative
"""
from typing import Any, Union, List
from constants import VSN1Constants, LabelDisplayMode, ScreenMessages


class LabelFormatter:
	"""Utility class for label compression and formatting"""

	@staticmethod
	def get_label_for_parameter(par_or_group: Union[Par, ParGroup], mode: LabelDisplayMode, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Get the label for a parameter or ParGroup
		For ParGroups, uses the ParGroup's name with > prefix"""
		if par_or_group is None:
			return ScreenMessages.HOVER
		
		# Handle ParGroup
		if isinstance(par_or_group, ParGroup):
			# Use ParGroup's name
			group_name = par_or_group.label
			
			# Extract sequence block prefix if it exists
			prefix = ""
			if len(par_or_group) > 0 and par_or_group[0] is not None:
				# Get sequence block from first parameter in the group
				if block := par_or_group[0].sequenceBlock:
					prefix = f"{block.index}"
			
			# Add ">" prefix to denote it's a ParGroup
			base_label = f">{group_name}"
			
			# Format the label with prefix preservation
			if prefix:
				formatted_label = LabelFormatter._format_label_with_prefix_suffix(base_label, prefix, "", mode, max_length)
			else:
				formatted_label = LabelFormatter.format_label(base_label, mode, max_length)
			return formatted_label
		
		# Handle single Par
		base_label = par_or_group.label
		
		# Extract prefix (sequence block index) and suffix (parameter group)
		prefix = ""
		suffix = ""
		
		if block := par_or_group.sequenceBlock:
			prefix = f"{block.index}"
		
		if len(par_or_group.parGroup) > 1 and not (isinstance(par_or_group.parGroup, ParGroupUnit) or isinstance(par_or_group.parGroup, ParGroupPulse)):
			# Only add suffix if all parameters in the group share the same base name
			# This is to display constantCHOP name parameter name correctly, or for new POP parameters that are "groups"
			# Get base names (name without last character) for all pars in group
			base_names = set(p.name[:-1] for p in par_or_group.parGroup.pars())
			# Only add suffix if all share the same base
			if len(base_names) == 1:
				suffix = f"{par_or_group.name[-1].capitalize()}"
		
		# Format with prefix and suffix preservation
		formatted_label = LabelFormatter._format_label_with_prefix_suffix(base_label, prefix, suffix, mode, max_length)
		return formatted_label
	
	@staticmethod
	def _format_label_with_prefix_suffix(base_label: str, prefix: str, suffix: str, mode: LabelDisplayMode, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Format label while preserving important prefix and suffix"""
		# If no prefix or suffix, use regular formatting
		if not prefix and not suffix:
			return LabelFormatter.format_label(base_label, mode, max_length)
		
		# Calculate available space for base label (reserve space for prefix and suffix)
		prefix_length = len(prefix)
		suffix_length = len(suffix)
		reserved_space = prefix_length + suffix_length
		available_for_base = max_length - reserved_space
		
		# If prefix + suffix are too long, prioritize them and truncate base severely
		if available_for_base < 1:
			# Keep at least 1 character of base + prefix + suffix
			base_part = LabelFormatter._sanitize_label(base_label)[:1] if base_label else "P"
			return (prefix + base_part + suffix)[:max_length]
		
		# Format the base label with available space
		if mode == LabelDisplayMode.COMPRESSED:
			formatted_base = LabelFormatter.compress_label(base_label, available_for_base)
		elif mode == LabelDisplayMode.TRUNCATED:
			formatted_base = LabelFormatter.truncate_label(base_label, available_for_base)
		else:
			formatted_base = LabelFormatter.compress_label(base_label, available_for_base)
		
		# Combine prefix + base + suffix
		return prefix + formatted_base + suffix
	
	@staticmethod
	def format_label(label: str, mode: LabelDisplayMode, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Format labels based on display mode - compression or truncation"""
		if mode == LabelDisplayMode.COMPRESSED:
			return LabelFormatter.compress_label(label, max_length)
		elif mode == LabelDisplayMode.TRUNCATED:
			return LabelFormatter.truncate_label(label, max_length)
		else:
			# Default to compression for unknown modes
			return LabelFormatter.compress_label(label, max_length)
	
	@staticmethod
	def compress_label(label: str, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Compress labels for display - removes whitespace and vowels if needed"""
		label = LabelFormatter._sanitize_label(label)
		
		if len(label) <= max_length:
			return label
		
		# Remove whitespace and underscores
		compressed = label.replace(' ', '').replace('_', '')
		
		# Remove vowels (keep first character)
		vowels = 'aeiouAEIOU'
		if len(compressed) > 1:
			compressed = compressed[0] + ''.join(c for c in compressed[1:] if c not in vowels)
		
		return compressed[:max_length]
	
	@staticmethod
	def truncate_label(label: str, max_length: int = VSN1Constants.MAX_LABEL_LENGTH) -> str:
		"""Simply truncate labels to max length"""
		label = LabelFormatter._sanitize_label(label)
		
		if len(label) <= max_length:
			return label
		
		return label[:max_length]
	
	@staticmethod
	def _sanitize_label(label: str) -> str:
		"""Remove characters that could cause issues in display systems"""
		if not label:
			return 'Param'
		
		sanitized = label.replace('"', '').replace("'", '').replace('\\', '').replace('\n', '').replace('\r', '')
		return sanitized if sanitized else 'Param'
	
	@staticmethod
	def format_value(value: Any, max_length: int = VSN1Constants.MAX_VALUE_LENGTH) -> str:
		"""Format values for display with length limit"""
		if isinstance(value, (int, float)):
			value = round(value, 6)
			if value % 1 == 0:
				value = int(value)
		return str(value)[:max_length]
