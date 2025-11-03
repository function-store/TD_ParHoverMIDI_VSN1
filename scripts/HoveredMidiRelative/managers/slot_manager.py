
'''Info Header Start
Name : slot_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.189.toe
Saveversion : 2023.12120
Info Header End'''

from typing import Optional, Union
from constants import ScreenMessages, VSN1ColorIndex
from validators import ParameterValidator
from formatters import LabelFormatter

class SlotManager:
	"""Centralized slot management - handles all slot operations and state with bank support"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
	
	def assign_slot(self, slot_idx: int, parameter: Union[Par, ParGroup]) -> bool:
		"""Assign a parameter (or ParGroup) to a slot and activate it. Returns True if successful.
		
		Note: We allow saving parameters with expressions/exports. During manipulation,
		only valid parameters will be affected (invalid ones are skipped)."""
		# Only check if the parameter type is supported (not if it's valid/has expressions)
		if not ParameterValidator.is_supported_parameter_type(parameter):
			return False

		currBank = self.parent.currBank
		
		# Capture state before assignment (for undo)
		previous_parameter = self.parent.slotPars[currBank][slot_idx]
		previous_active_slot = self.parent.activeSlot
		previous_bank_active_slot = self.parent.bankActiveSlots[currBank]
		
		# Store previous active slot for LED updates
		old_active_slot = self.parent.activeSlot
		
		# Assign parameter (or ParGroup) to table
		self.parent.slotPars[currBank][slot_idx] = parameter

		# Set parexec to the first valid parameter for ParGroups, or the parameter itself for single pars
		if ParameterValidator.is_pargroup(parameter):
			# Find first valid parameter in the group
			for p in parameter:
				if p is not None and ParameterValidator.is_valid_parameter(p):
					self.parent._set_parexec_pars(p)
					break
			else:
				# No valid parameters found, set to None
				self.parent._set_parexec_pars(None)
		else:
			self.parent._set_parexec_pars(parameter)
		
		self.parent.activeSlot = slot_idx
		self.parent.bankActiveSlots[currBank] = slot_idx
		
		# Turn off hovered UI color when assigning a slot
		self.parent.ui_manager.set_hovered_ui_color(-1)
		
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
		

		# Add undo support if enabled
		self.parent.undo_manager.create_assign_slot_undo(
			slot_idx=slot_idx,
			bank_idx=currBank,
			new_parameter=parameter,
			previous_parameter=previous_parameter,
			previous_active_slot=previous_active_slot,
			previous_bank_active_slot=previous_bank_active_slot
		)
		
		return True
	
	def clear_slot(self, slot_idx: int):
		"""Clear a slot and return to hover mode"""
		currBank = self.parent.currBank
		
		# Check if slot has a parameter to clear
		previous_parameter = self.parent.slotPars[currBank][slot_idx]
		if previous_parameter is None:
			return  # Nothing to clear
		
		# Capture state before clearing (for undo)
		previous_active_slot = self.parent.activeSlot
		previous_bank_active_slot = self.parent.bankActiveSlots[currBank]
		
		# Clear the slot
		self.parent.slotPars[currBank][slot_idx] = None
		self.parent._set_parexec_pars(None)
		self.parent.activeSlot = None
		self.parent._activeSlotPar = None  # Clear cached active slot parameter
		self.parent.bankActiveSlots[currBank] = None
		
		# Restore hovered UI color if enabled (now in hover mode)
		if self.parent.evalColorhoveredui:
			self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
		else:
			self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Clear UI button label
		if hasattr(self.parent, 'ui_manager'):
			self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
		
		# Update display to hover mode
		self.parent.display_manager.update_all_display(
			0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
		
		# Update LEDs and outline color
		# Pass previous_slot to update the cleared slot's LED to show it's now free
		self.parent.display_manager.update_slot_leds(current_slot=None, previous_slot=slot_idx)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		
		# Add undo support if enabled
		self.parent.undo_manager.create_clear_slot_undo(
			slot_idx=slot_idx,
			bank_idx=currBank,
			previous_parameter=previous_parameter,
			previous_active_slot=previous_active_slot,
			previous_bank_active_slot=previous_bank_active_slot
		)
	
	def activate_slot(self, slot_idx: int) -> bool:
		"""Activate an existing slot. Returns True if successful."""

		currBank = self.parent.currBank
		slot_par = self.parent.slotPars[currBank][slot_idx]
		
		if slot_par is None:
			return False

		# Clear any unused captured values from previous slot
		if self.parent.activeSlot is not None:
			old_slot_par = self.parent.slotPars[currBank][self.parent.activeSlot]
			if old_slot_par is not None:
				self.parent.undo_manager.on_slot_deactivated(old_slot_par)
		
		old_active_slot = self.parent.activeSlot
		self.parent.activeSlot = slot_idx
		self.parent._activeSlotPar = slot_par  # Store directly for ultra-fast access
		self.parent.bankActiveSlots[currBank] = slot_idx
		
		# Turn off hovered UI color when activating a slot
		self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Update display with slot parameter
		if slot_par is not None:
			# Capture initial values for undo when slot is activated
			self.parent.undo_manager.on_slot_activated(slot_par)

			# Set parexec to the first valid parameter for ParGroups, or the parameter itself for single pars
			if ParameterValidator.is_pargroup(slot_par):
				# Find first valid parameter in the group
				for p in slot_par:
					if p is not None and ParameterValidator.is_valid_parameter(p):
						self.parent._set_parexec_pars(p)
						break
				else:
					# No valid parameters found, set to None
					self.parent._set_parexec_pars(None)
			else:
				self.parent._set_parexec_pars(slot_par)
			
			bottom_text = None
			if error_msg := ParameterValidator.get_validation_error(slot_par):
				bottom_text = error_msg
			self.parent.display_manager.update_parameter_display(slot_par, bottom_text=bottom_text)
		
			# Update LEDs and outline color
			self.parent.display_manager.update_slot_leds(current_slot=slot_idx, previous_slot=old_active_slot)
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
			return True
		
		return False

	def recall_bank(self, bank_idx: int):
		"""Switch to a different bank and recall its last active slot"""
		# Validate bank index
		if bank_idx < 0 or bank_idx >= self.parent.numBanks:
			return False
		
		# Clear any unused captured values from current bank's active slot
		old_bank = self.parent.currBank
		if self.parent.activeSlot is not None:
			old_slot_par = self.parent.slotPars[old_bank][self.parent.activeSlot]
			if old_slot_par is not None:
				self.parent.undo_manager.on_slot_deactivated(old_slot_par)
		
		# Save current active slot for current bank
		self.parent.bankActiveSlots[old_bank] = self.parent.activeSlot
		
		# Switch to new bank
		self.parent.currBank = bank_idx
		self.parent._activeSlotPar = None  # Clear cached active slot parameter
		
		# Ensure bank structure exists
		self.parent._validate_storage()
		
		# Recall previous active slot for this bank
		previous_slot = self.parent.bankActiveSlots[bank_idx]
		
		if previous_slot is not None:
			# Check if the slot still has a valid parameter
			slot_par = self.parent.slotPars[bank_idx][previous_slot]
			if slot_par is not None:
				self.parent.activeSlot = previous_slot
				self.parent._activeSlotPar = slot_par  # Store directly for ultra-fast access
				
				# Turn off hovered UI color when recalling a slot
				self.parent.ui_manager.set_hovered_ui_color(-1)
				
				# Capture initial values for undo when recalling slot
				self.parent.undo_manager.on_slot_activated(slot_par)
			else:
				self.parent.activeSlot = None
				self.parent.bankActiveSlots[bank_idx] = None
				
				# Restore hovered UI color if enabled (no active slot)
				if self.parent.evalColorhoveredui:
					self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
				else:
					self.parent.ui_manager.set_hovered_ui_color(-1)
		else:
			self.parent.activeSlot = None
			self.parent._activeSlotPar = None  # Clear cached active slot parameter
			
			# Restore hovered UI color if enabled (no active slot)
			if self.parent.evalColorhoveredui:
				self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
			else:
				self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Refresh display and UI for new bank
		self._refresh_bank_display()
		
		return True
	
	def _refresh_bank_display(self):
		"""Refresh all display elements when switching banks"""
		currBank = self.parent.currBank
		
		# Update bank indicator on both displays
		self.parent.display_manager.set_bank_indicator(currBank)
		
		# Update UI button labels and colors for the new bank (comprehensive refresh)
		if hasattr(self.parent, 'ui_manager'):
			self.parent.ui_manager.refresh_all_button_states()
		
		# Update VSN1 slot LEDs (UI colors already handled above)
		if hasattr(self.parent, 'vsn1_manager'):
			self.parent.vsn1_manager.update_all_slot_leds()
		
		# Update display based on active slot or hover mode
		if self.parent.activeSlot is not None:
			active_par = self.parent.slotPars[currBank][self.parent.activeSlot]

			if active_par is not None:
				# Set parexec to the first valid parameter for ParGroups, or the parameter itself for single pars
				if ParameterValidator.is_pargroup(active_par):
					# Find first valid parameter in the group
					for p in active_par:
						if p is not None and ParameterValidator.is_valid_parameter(p):
							self.parent._set_parexec_pars(p)
							break
					else:
						# No valid parameters found, set to None
						self.parent._set_parexec_pars(None)
				else:
					self.parent._set_parexec_pars(active_par)

				self.parent.display_manager.update_parameter_display(active_par)
				self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		else:
			# Return to hover mode
			if self.parent.hoveredPar is not None:
				# Check if hovered parameter is an expression and handle accordingly
				if error_msg := ParameterValidator.get_validation_error(self.parent.hoveredPar):
					self.parent.display_manager.show_parameter_error(self.parent.hoveredPar, error_msg)
					if error_msg == ScreenMessages.EXPR:
						self.parent._set_parexec_pars(self.parent.hoveredPar)
				else:
					# Valid parameter - update display normally
					self.parent.display_manager.update_parameter_display(self.parent.hoveredPar)
			else:
				self.parent.display_manager.update_all_display(
					0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False
				)
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
	
	def deactivate_current_slot(self):
		"""Deactivate current slot and return to hover mode"""
		if self.parent.activeSlot is None:
			return
		self.parent._set_parexec_pars(self.parent.hoveredPar)
		
		old_active_slot = self.parent.activeSlot
		currBank = self.parent.currBank
		
		# Clear active slot
		self.parent.activeSlot = None
		self.parent._activeSlotPar = None  # Clear cached active slot parameter
		self.parent._set_parexec_pars(None)
		self.parent.bankActiveSlots[currBank] = None
		
		# Restore hovered UI color if enabled (now in hover mode)
		if self.parent.evalColorhoveredui:
			self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
		else:
			self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Get label for hovered parameter (or ParGroup)
		if self.parent.hoveredPar is not None:
			# Use formatter to get proper label (handles both Par and ParGroup)
			label = LabelFormatter.get_label_for_parameter(self.parent.hoveredPar, self.parent.labelDisplayMode)
		else:
			label = ScreenMessages.HOVER

		if self.parent.hoveredPar is not None:
			# Check if hovered parameter is an expression and handle accordingly
			if error_msg := ParameterValidator.get_validation_error(self.parent.hoveredPar):
				self.parent.display_manager.show_parameter_error(self.parent.hoveredPar, error_msg)
				if error_msg == ScreenMessages.EXPR:
					self.parent._set_parexec_pars(self.parent.hoveredPar)
			else:
				# Valid parameter - update display normally
				self.parent.display_manager.update_parameter_display(self.parent.hoveredPar)

		else:
			self.parent.display_manager.update_all_display(0, 0, 1, label, ScreenMessages.HOVER, compress=False)

		# Update LEDs and outline color
		self.parent.display_manager.update_slot_leds(previous_slot=old_active_slot)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
	
	def get_slot_parameter(self, slot_idx: int, bank_idx: Optional[int] = None) -> Optional[Union[Par, ParGroup]]:
		"""Get the parameter (or ParGroup) assigned to a slot in the specified bank (defaults to current bank)"""
		return self.parent.slotPars[bank_idx][slot_idx]
	
	def is_slot_occupied(self, slot_idx: int, bank_idx: Optional[int] = None) -> bool:
		"""Check if a slot has a parameter (or ParGroup) assigned in the specified bank (defaults to current bank)"""
		return self.parent.slotPars[bank_idx][slot_idx] is not None
	
	def is_slot_active(self, slot_idx: int) -> bool:
		"""Check if a slot is currently active in the current bank"""
		return self.parent.activeSlot == slot_idx
	
	def get_active_slot_parameter(self) -> Optional[Union[Par, ParGroup]]:
		"""Get the parameter (or ParGroup) of the currently active slot"""
		if self.parent.activeSlot is None:
			return None
		return self.get_slot_parameter(self.parent.activeSlot)
	
	def find_slot_for_parameter(self, parameter: Union[Par, ParGroup], bank_idx: Optional[int] = None) -> Optional[int]:
		"""Find which slot contains the given parameter in the specified bank (defaults to current bank).
		Returns slot index if found, None otherwise."""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		# Get all slots for the bank and search
		all_slots = self.parent.slotPars[bank_idx]
		
		for slot_idx, slot_par in enumerate(all_slots):
			if slot_par is parameter:
				return slot_idx
		
		return None
	
	def clear_slot_in_bank(self, slot_idx: int, bank_idx: int):
		"""Clear a slot in a specific bank (internal method for invalidation, no undo support)"""
		# Clear the slot
		self.parent.slotPars[bank_idx][slot_idx] = None
		self.parent._set_parexec_pars(None)
		
		# If this was the active slot in this bank, deactivate it
		if self.parent.bankActiveSlots[bank_idx] == slot_idx:
			self.parent.activeSlot = None
			self.parent.bankActiveSlots[bank_idx] = None
			
		# If we're currently in this bank, update UI
		if bank_idx == self.parent.currBank:
			if self.parent.activeSlot == slot_idx:
				self.parent.activeSlot = None
				
				# Restore hovered UI color if enabled (now in hover mode)
				if self.parent.evalColorhoveredui:
					self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
				else:
					self.parent.ui_manager.set_hovered_ui_color(-1)
				
			# Clear UI button label
			if hasattr(self.parent, 'ui_manager'):
				self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
			
			# Update displays
			self.parent.display_manager.update_slot_leds(current_slot=None, previous_slot=slot_idx)
			if self.parent.activeSlot is None:
				self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)