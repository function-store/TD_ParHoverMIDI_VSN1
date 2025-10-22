
'''Info Header Start
Name : slot_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.189.toe
Saveversion : 2025.31310
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

		# Extend number of banks if necessary
		
		# Extend slot list if necessary
		currBank = self.parent.currBank
		while len(self.parent.slotPars) <= currBank:
			self.parent.slotPars.append([])

		while len(self.parent.slotPars[currBank]) <= slot_idx:
			# Extend current bank with empty slots as needed
			self.parent.slotPars[currBank].append(None)
		
		# Store previous active slot for LED updates
		old_active_slot = self.parent.activeSlot
		
		# Assign parameter (or ParGroup) and activate slot
		self.parent.slotPars[currBank][slot_idx] = parameter
		self.parent.activeSlot = slot_idx
		self.parent.bankActiveSlots[currBank] = slot_idx
		
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
						0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
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
				
				if hasattr(self.parent, 'ui_manager'):
					self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
				
				self.parent.display_manager.update_all_display(
					0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
				
				self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
				self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		
		# Always refresh UI buttons for current bank to ensure correct state
		# (TouchDesigner's undo system may revert some UI states)
		if hasattr(self.parent, 'ui_manager') and self.parent.ui_manager:
			#self.parent.ui_manager.refresh_all_button_states()
			run("args[0].refresh_all_button_states()", self.parent.ui_manager, delayFrames=1)
	
	def clear_slot(self, slot_idx: int):
		"""Clear a slot and return to hover mode"""
		currBank = self.parent.currBank
		if (currBank >= len(self.parent.slotPars) or 
			slot_idx >= len(self.parent.slotPars[currBank])):
			return
		
		# Check if slot has a parameter to clear
		previous_parameter = self.parent.slotPars[currBank][slot_idx]
		if previous_parameter is None:
			return  # Nothing to clear
		
		# Capture state before clearing (for undo)
		previous_active_slot = self.parent.activeSlot
		previous_bank_active_slot = self.parent.bankActiveSlots[currBank]
		
		# Clear the slot
		self.parent.slotPars[currBank][slot_idx] = None
		self.parent.activeSlot = None
		self.parent.bankActiveSlots[currBank] = None
		
		# Clear UI button label
		if hasattr(self.parent, 'ui_manager'):
			self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
		
		# Update display to hover mode
		self.parent.display_manager.update_all_display(
			0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False)
		
		# Update LEDs and outline color
		self.parent.display_manager.update_slot_leds(current_slot=slot_idx)
		self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		
		# Add undo support if enabled
		if self.parent.evalEnableundo:
			ui.undo.startBlock(f'Clear Slot {slot_idx} in Bank {currBank}')
			try:
				undo_info = {
					'slot_idx': slot_idx,
					'bank_idx': currBank,
					'previous_parameter': previous_parameter,
					'previous_active_slot': previous_active_slot,
					'previous_bank_active_slot': previous_bank_active_slot
				}
				ui.undo.addCallback(self._undo_clear_slot_callback, undo_info)
			finally:
				ui.undo.endBlock()
	
	def activate_slot(self, slot_idx: int) -> bool:
		"""Activate an existing slot. Returns True if successful."""
		currBank = self.parent.currBank
		if (currBank >= len(self.parent.slotPars) or 
			slot_idx >= len(self.parent.slotPars[currBank]) or 
			self.parent.slotPars[currBank][slot_idx] is None):
			return False
		
		old_active_slot = self.parent.activeSlot
		self.parent.activeSlot = slot_idx
		self.parent.bankActiveSlots[currBank] = slot_idx
		
		# Update display with slot parameter
		if slot_par := self.parent.slotPars[currBank][slot_idx]:
			self.parent.display_manager.update_parameter_display(slot_par)
		
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
		
		# Save current active slot for current bank
		if self.parent.currBank < len(self.parent.bankActiveSlots):
			self.parent.bankActiveSlots[self.parent.currBank] = self.parent.activeSlot
		
		# Switch to new bank
		old_bank = self.parent.currBank
		self.parent.currBank = bank_idx
		
		# Ensure bank structure exists
		self.parent._validate_storage()
		
		# Recall previous active slot for this bank
		if (bank_idx < len(self.parent.bankActiveSlots) and 
			self.parent.bankActiveSlots[bank_idx] is not None):
			previous_slot = self.parent.bankActiveSlots[bank_idx]
			
			# Check if the slot still has a valid parameter
			if (previous_slot < len(self.parent.slotPars[bank_idx]) and 
				self.parent.slotPars[bank_idx][previous_slot] is not None):
				self.parent.activeSlot = previous_slot
			else:
				self.parent.activeSlot = None
				self.parent.bankActiveSlots[bank_idx] = None
		else:
			self.parent.activeSlot = None
		
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
			self.parent.display_manager.update_parameter_display(active_par)
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		else:
			# Return to hover mode
			if self.parent.hoveredPar is not None:
				self.parent.display_manager.update_parameter_display(self.parent.hoveredPar)
			else:
				self.parent.display_manager.update_all_display(
					0.5, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False
				)
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
	
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
	
	def get_slot_parameter(self, slot_idx: int, bank_idx: Optional[int] = None) -> Optional[Union[Par, ParGroup]]:
		"""Get the parameter (or ParGroup) assigned to a slot in the specified bank (defaults to current bank)"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
			
		if (bank_idx >= len(self.parent.slotPars) or 
			slot_idx >= len(self.parent.slotPars[bank_idx])):
			return None
		return self.parent.slotPars[bank_idx][slot_idx]
	
	def is_slot_occupied(self, slot_idx: int, bank_idx: Optional[int] = None) -> bool:
		"""Check if a slot has a parameter (or ParGroup) assigned in the specified bank (defaults to current bank)"""
		return self.get_slot_parameter(slot_idx, bank_idx) is not None
	
	def is_slot_active(self, slot_idx: int) -> bool:
		"""Check if a slot is currently active in the current bank"""
		return self.parent.activeSlot == slot_idx
	
	def get_active_slot_parameter(self) -> Optional[Union[Par, ParGroup]]:
		"""Get the parameter (or ParGroup) of the currently active slot"""
		if self.parent.activeSlot is None:
			return None
		return self.get_slot_parameter(self.parent.activeSlot)