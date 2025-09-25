'''Info Header Start
Name : slot_manager
Author : root
Saveorigin : HoveredMidiRelative.182.toe
Saveversion : 2023.12120
Info Header End'''
from typing import Optional
from constants import ScreenMessages, VSN1ColorIndex
from validators import ParameterValidator
from formatters import LabelFormatter

class SlotManager:
	"""Centralized slot management - handles all slot operations and state"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
	
	def assign_slot(self, slot_idx: int, parameter: Par) -> bool:
		"""Assign a parameter to a slot and activate it. Returns True if successful."""
		if not ParameterValidator.is_valid_parameter(parameter) or \
		   not ParameterValidator.is_supported_parameter_type(parameter):
			return False
		
		# Extend slot list if necessary
		while len(self.parent.slotPars) <= slot_idx:
			self.parent.slotPars.append(None)
		
		# Store previous active slot for LED updates
		old_active_slot = self.parent.activeSlot
		
		# Assign parameter and activate slot
		self.parent.slotPars[slot_idx] = parameter
		self.parent.activeSlot = slot_idx
		
		# Update UI button label
		if hasattr(self.parent, 'ui_manager'):
			label = LabelFormatter.get_label_for_parameter(parameter, self.parent.labelDisplayMode)
			self.parent.ui_manager._set_button_label(slot_idx, label)
		
		# Update displays and feedback
		param_label = LabelFormatter.get_label_for_parameter(parameter, self.parent.labelDisplayMode)
		self.parent.display_manager.update_parameter_display(parameter, bottom_text=ScreenMessages.LEARNED)
		
		# Update LEDs and outline color
		self.parent.display_manager.update_slot_leds(current_slot=slot_idx, previous_slot=old_active_slot)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		
		return True
	
	def clear_slot(self, slot_idx: int):
		"""Clear a slot and return to hover mode"""
		if slot_idx >= len(self.parent.slotPars):
			return
			
		# Clear the slot
		self.parent.slotPars[slot_idx] = None
		self.parent.activeSlot = None
		
		# Clear UI button label
		if hasattr(self.parent, 'ui_manager'):
			self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
		
		# Update display to hover mode
		self.parent.display_manager.update_all_display(
			0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
		
		# Update LEDs and outline color
		self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
	
	def activate_slot(self, slot_idx: int) -> bool:
		"""Activate an existing slot. Returns True if successful."""
		if slot_idx >= len(self.parent.slotPars) or self.parent.slotPars[slot_idx] is None:
			return False
		
		old_active_slot = self.parent.activeSlot
		self.parent.activeSlot = slot_idx
		
		# Update display with slot parameter
		slot_par = self.parent.slotPars[slot_idx]
		self.parent.display_manager.update_parameter_display(slot_par)
		
		# Update LEDs and outline color
		self.parent.display_manager.update_slot_leds(current_slot=slot_idx, previous_slot=old_active_slot)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		
		return True
	
	def deactivate_current_slot(self):
		"""Deactivate current slot and return to hover mode"""
		if self.parent.activeSlot is None:
			return
		
		old_active_slot = self.parent.activeSlot
		self.parent.activeSlot = None
		
		# Update display to hover mode
		self.parent.display_manager.update_all_display(
			0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
		
		# Update LEDs and outline color
		self.parent.display_manager.update_slot_leds(previous_slot=old_active_slot)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
	
	def get_slot_parameter(self, slot_idx: int) -> Optional[Par]:
		"""Get the parameter assigned to a slot"""
		if slot_idx >= len(self.parent.slotPars):
			return None
		return self.parent.slotPars[slot_idx]
	
	def is_slot_occupied(self, slot_idx: int) -> bool:
		"""Check if a slot has a parameter assigned"""
		return self.get_slot_parameter(slot_idx) is not None
	
	def is_slot_active(self, slot_idx: int) -> bool:
		"""Check if a slot is currently active"""
		return self.parent.activeSlot == slot_idx
	
	def get_active_slot_parameter(self) -> Optional[Par]:
		"""Get the parameter of the currently active slot"""
		if self.parent.activeSlot is None:
			return None
		return self.get_slot_parameter(self.parent.activeSlot)