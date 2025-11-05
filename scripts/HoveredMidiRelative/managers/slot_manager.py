
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
		
		# Store pending invalidation info for popup dialog callback
		self._pending_invalidation = None
		
		# Queue for sequential invalidation handling
		self._invalidation_queue = []
		self._processing_invalidation = False
		self._banks_to_save_after_queue = set()  # Track banks modified during queue processing
	
	def is_dialog_open(self) -> bool:
		"""Check if the parameter recovery dialog is currently open"""
		try:
			return self.parent.popDialog.op("popDialogWindow").isOpen
		except:
			return False
	
	def is_invalidation_active(self) -> bool:
		"""Check if invalidation/recovery is active (dialog open OR queue being processed)"""
		return self.is_dialog_open() or self._processing_invalidation
	
	def queue_invalidation_check(self):
		"""Queue a check for invalid parameters and process them sequentially with dialogs"""
		# Don't queue if already processing
		if self._processing_invalidation:
			return
		
		# Find all invalid parameters
		invalid_params = []
		for bank_idx in range(self.parent.numBanks):
			for slot_idx in range(self.parent.numSlots):
				par = self.parent.slotPars[bank_idx][slot_idx]
				if par is None:
					continue
				
				# Check if parameter is invalid
				is_invalid = False
				try:
					# Try to access .valid property
					if not par.valid:
						is_invalid = True
					elif not par.name:
						is_invalid = True
				except:
					# Exception accessing parameter properties = invalid
					is_invalid = True
				
				if is_invalid:
					invalid_params.append((slot_idx, bank_idx))
		
		if invalid_params:
			# Start processing the first one
			self._invalidation_queue = invalid_params
			self._processing_invalidation = True
			self._process_next_invalidation()
	
	def _batch_update_operator_path(self, old_op_path: str, new_op_path: str, exclude_slot: tuple = None):
		"""Batch-update all slots that have the same old operator path to the new path
		
		Args:
			old_op_path: Old operator path (e.g., "/project1/geo1")
			new_op_path: New operator path (e.g., "/project1/geo2")
			exclude_slot: Tuple of (slot_idx, bank_idx) to exclude from batch update (already fixed)
		"""
		updated_slots = []
		failed_slots = []
		banks_to_save = set()  # Track which banks need saving
		
		# Go through all bank tables in the repo
		for bank_idx in range(self.parent.numBanks):
			bank_table = self.parent.repo_manager.Repo.op(f'bank{bank_idx}')
			if bank_table is None:
				continue
			
			# Iterate through all rows in this bank table (skip header row)
			for row_idx in range(1, bank_table.numRows):
				slot_idx = row_idx - 1  # Row 1 = slot 0
				
				# Skip the slot we just manually fixed
				if exclude_slot and (slot_idx, bank_idx) == exclude_slot:
					continue
				
				# Read directly from repo table
				slot_op_path = bank_table[row_idx, 0].val  # path column
				par_name = bank_table[row_idx, 1].val      # name column
				par_type = bank_table[row_idx, 2].val      # type column
				
				# Check if this slot's path matches or is a child of the old path
				# Exact match: /project1/test1 == /project1/test1
				# Child match: /project1/test1/circle1 starts with /project1/test1/
				is_exact_match = (slot_op_path == old_op_path)
				is_child_match = slot_op_path.startswith(old_op_path + '/')
				
				# Skip slots that have already been cleared in memory (even if still in repo table)
				if self.parent.slotPars[bank_idx][slot_idx] is None:
					continue
				
				if (is_exact_match or is_child_match) and par_name:
					is_pargroup = (par_type.lower() == 'pargroup')
					
					# Calculate the new path
					if is_exact_match:
						# Exact match - replace entire path
						updated_op_path = new_op_path
					else:
						# Child match - replace the prefix, keep the rest
						# e.g., /project1/base1/test1/circle1 -> /project1/test1/circle1
						remaining_path = slot_op_path[len(old_op_path):]  # Gets '/circle1'
						updated_op_path = new_op_path + remaining_path
					
					# Try to recover with new path (don't save to table yet)
					new_path_parname = f"{updated_op_path}:{par_name}"
					success = self._try_recover_parameter(
						slot_idx=slot_idx,
						bank_idx=bank_idx,
						path_parname=new_path_parname,
						is_pargroup=is_pargroup,
						save_to_table=False  # Don't save yet - we'll save all banks at once at the end
					)
					
					if success:
						updated_slots.append((slot_idx, bank_idx))
						banks_to_save.add(bank_idx)
						
						# Remove from invalidation queue if present
						if (slot_idx, bank_idx) in self._invalidation_queue:
							self._invalidation_queue.remove((slot_idx, bank_idx))
					else:
						failed_slots.append((slot_idx, bank_idx, par_name))
		
		# Save all modified banks to tables at once
		for bank_idx in banks_to_save:
			# If we're processing invalidation queue, defer save to preserve repo data
			if self._processing_invalidation:
				self._banks_to_save_after_queue.add(bank_idx)
			else:
				self.parent.repo_manager.save_bank_to_table(bank_idx)
	
	def _batch_clear_operator_path(self, old_op_path: str, exclude_slot: tuple = None):
		"""Batch-clear all slots that have the same operator path
		
		Args:
			old_op_path: Operator path to match (e.g., "/project1/geo1")
			exclude_slot: Tuple of (slot_idx, bank_idx) to exclude from batch clear (already cleared)
		"""
		cleared_slots = []
		banks_to_save = set()  # Track which banks need saving
		
		# Go through all bank tables in the repo
		for bank_idx in range(self.parent.numBanks):
			bank_table = self.parent.repo_manager.Repo.op(f'bank{bank_idx}')
			if bank_table is None:
				continue
			
			# Iterate through all rows in this bank table (skip header row)
			for row_idx in range(1, bank_table.numRows):
				slot_idx = row_idx - 1  # Row 1 = slot 0
				
				# Skip the slot we just manually cleared
				if exclude_slot and (slot_idx, bank_idx) == exclude_slot:
					continue
				
				# Read directly from repo table
				slot_op_path = bank_table[row_idx, 0].val  # path column
				par_name = bank_table[row_idx, 1].val      # name column
				
				# Check if this slot's path matches or is a child of the old path
				is_exact_match = (slot_op_path == old_op_path)
				is_child_match = slot_op_path.startswith(old_op_path + '/')
				
				# Skip slots that have already been cleared in memory
				if self.parent.slotPars[bank_idx][slot_idx] is None:
					continue
				
				if (is_exact_match or is_child_match) and par_name:
					# Clear this slot
					self._clear_slot_data(slot_idx, bank_idx)
					cleared_slots.append((slot_idx, bank_idx))
					banks_to_save.add(bank_idx)
					
					# Remove from invalidation queue if present
					if (slot_idx, bank_idx) in self._invalidation_queue:
						self._invalidation_queue.remove((slot_idx, bank_idx))
		
		# Track banks for saving after queue completes (don't save now to preserve repo data)
		if self._processing_invalidation:
			for bank_idx in banks_to_save:
				self._banks_to_save_after_queue.add(bank_idx)
		else:
			# Not in queue processing, save immediately
			for bank_idx in banks_to_save:
				self.parent.repo_manager.save_bank_to_table(bank_idx)
	
	def _process_next_invalidation(self):
		"""Process the next invalid parameter in the queue"""
		if not self._invalidation_queue:
			# Queue is empty, done processing
			self._processing_invalidation = False
			
			# Save all modified banks to tables now that queue is complete
			if self._banks_to_save_after_queue:
				for bank_idx in self._banks_to_save_after_queue:
					self.parent.repo_manager.save_bank_to_table(bank_idx)
				self._banks_to_save_after_queue.clear()
			
			# Update UI after all invalidations are processed
			if hasattr(self.parent, 'ui_manager'):
				self.parent.ui_manager.refresh_all_button_states()
			
			# Update display based on current state
			if self.parent.activeSlot is None:
				# No active slot - return to hover mode
				if self.parent.evalColorhoveredui:
					self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
				else:
					self.parent.ui_manager.set_hovered_ui_color(-1)
				
				self.parent.display_manager.update_all_display(
					0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False
				)
				self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
			else:
				# Still have active slot - refresh its display
				active_par = self.parent.slotPars[self.parent.currBank][self.parent.activeSlot]
				if active_par is not None:
					self.parent.display_manager.update_parameter_display(active_par)
			
			# Update all slot LEDs
			self.parent.display_manager.update_all_slot_leds()
			return
		
		# Get the next invalid parameter
		slot_idx, bank_idx = self._invalidation_queue.pop(0)
		
		# Check if this slot is now valid (might have been fixed during batch update)
		try:
			par = self.parent.slotPars[bank_idx][slot_idx]
			if par is not None and par.valid:
				# This slot was fixed! Skip it and process the next one
				# Defer to next frame to ensure proper timing
				run("args[0]._process_next_invalidation()", self, delayFrames=1)
				return
		except:
			pass  # Parameter is invalid, continue with invalidation
		
		# Invalidate it with dialog (will call _on_recovery_dialog_response when done)
		self.invalidate_slot(slot_idx, bank_idx, update_ui=False, show_dialog=True)
	
	def _clear_slot_data(self, slot_idx: int, bank_idx: int):
		"""Clear slot data without updating UI (for batch operations)"""
		# Clear from internal storage
		self.parent.slotPars[bank_idx][slot_idx] = None
		
		# If this was the active slot, deactivate it
		if self.parent.activeSlot == slot_idx and self.parent.currBank == bank_idx:
			self.parent.activeSlot = None
			self.parent._activeSlotPar = None
			self.parent.bankActiveSlots[bank_idx] = None
	
	def invalidate_slot(self, slot_idx: int, bank_idx: Optional[int] = None, update_ui: bool = True, show_dialog: bool = True):
		"""Clear an invalid parameter from slot storage (both internal and external)
		
		Called when a parameter becomes invalid (operator deleted, moved, etc.)
		Args:
			slot_idx: Slot index to clear
			bank_idx: Bank index (defaults to current bank)
			update_ui: Whether to update UI/display after clearing (default True)
			show_dialog: Whether to show recovery dialog before clearing (default True)
		"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		# If show_dialog is True, try to recover the parameter via popup
		if show_dialog:
			# Get path and name from repo storage (tables) since the parameter is invalid
			op_path, par_name, is_pargroup = self._get_parameter_info_from_repo(slot_idx, bank_idx)
			
			# If we got path and name from storage, show recovery dialog
			if op_path and par_name:
				self._show_parameter_recovery_dialog(
					slot_idx=slot_idx,
					bank_idx=bank_idx,
					op_path=op_path,
					par_name=par_name,
					is_pargroup=is_pargroup,
					update_ui=update_ui
				)
				return  # Dialog will handle clearing or recovery
		
		# Immediate clearing (no dialog or dialog failed)
		self._clear_slot_data(slot_idx, bank_idx)
		
		# Clear from external storage (tables)
		# If processing queue, defer save to preserve repo data for other invalid params
		if self._processing_invalidation:
			self._banks_to_save_after_queue.add(bank_idx)
		else:
			self.parent.repo_manager.save_bank_to_table(bank_idx)
		
		# Update UI/display if requested
		if update_ui:
			self._update_ui_after_invalidation(slot_idx, bank_idx)
		
		# If we're processing a queue, continue to next item
		# (dialog callback would normally do this, but we skipped the dialog)
		if self._processing_invalidation:
			# Defer to next frame to ensure proper timing
			run("args[0]._process_next_invalidation()", self, delayFrames=1)
	
	def _get_parameter_info_from_repo(self, slot_idx: int, bank_idx: int) -> tuple:
		"""Get parameter info from repo storage tables
		
		Args:
			slot_idx: Slot index
			bank_idx: Bank index
			
		Returns:
			Tuple of (op_path, par_name, is_pargroup) or (None, None, False) if not found
		"""
		try:
			# Get the bank table from repo
			bank_table = self.parent.repo_manager.Repo.op(f'bank{bank_idx}')
			if bank_table is None:
				return (None, None, False)
			
			# Get the row for this slot (+1 for header row)
			row_idx = slot_idx + 1
			if row_idx >= bank_table.numRows:
				return (None, None, False)
			
			# Read from table columns
			op_path = bank_table[row_idx, 0].val  # path column
			par_name = bank_table[row_idx, 1].val  # name column
			par_type = bank_table[row_idx, 2].val  # type column
			
			if not op_path or not par_name:
				return (None, None, False)
			
			# Determine if it's a pargroup (case-insensitive for backward compatibility)
			is_pargroup = (par_type.lower() == 'pargroup')
			
			return (op_path, par_name, is_pargroup)
			
		except Exception as e:
			return (None, None, False)
	
	def _update_ui_after_invalidation(self, slot_idx: int, bank_idx: int):
		"""Update UI/display after slot invalidation"""
		is_current_bank = self.parent.currBank == bank_idx
		
		if not is_current_bank:
			return  # Don't update UI for other banks
		
		# Update UI button label
		if hasattr(self.parent, 'ui_manager'):
			self.parent.ui_manager._set_button_label(slot_idx, ScreenMessages.HOVER)
		
		# If no active slot remains, return to hover mode
		if self.parent.activeSlot is None:
			# Return to hover mode
			if self.parent.evalColorhoveredui:
				self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
			else:
				self.parent.ui_manager.set_hovered_ui_color(-1)
			
			self.parent.display_manager.update_all_display(
				0, 0, 1, ScreenMessages.HOVER, ScreenMessages.HOVER, compress=False
			)
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		
		# Update slot LEDs
		self.parent.display_manager.update_slot_leds(current_slot=self.parent.activeSlot, previous_slot=slot_idx)
	
	def _show_parameter_recovery_dialog(self, slot_idx: int, bank_idx: int, op_path: str, 
	                                     par_name: str, is_pargroup: bool, update_ui: bool):
		"""Show popup dialog to allow user to fix invalid parameter path
		
		Args:
			slot_idx: Slot index with invalid parameter
			bank_idx: Bank index
			op_path: Original operator path
			par_name: Original parameter name
			is_pargroup: Whether this was a ParGroup
			update_ui: Whether to update UI after clearing
		"""
		# Store pending invalidation info for callback
		self._pending_invalidation = {
			'slot_idx': slot_idx,
			'bank_idx': bank_idx,
			'is_pargroup': is_pargroup,
			'update_ui': update_ui
		}
		
		# Format the path:parname for display/editing
		path_parname = f"{op_path}:{par_name}"
		par_type = "ParGroup" if is_pargroup else "Parameter"
		
		# Update display to show _INVALID_ message
		self.parent.display_manager.update_all_display(
			0, 0, 1, 
			ScreenMessages.INVALID, 
			ScreenMessages.INVALID, 
			compress=False
		)
		
		# Show popup dialog
		self.parent.popDialog.Open(
			title=f"Invalid {par_type} in Slot {slot_idx + 1}",
			text=f"The {par_type.lower()} is no longer valid.\nEdit the path to fix all related slots, or clear this slot only, or clear all related slots.",
			buttons=["Fix", "Clear", "Clear All"],
			textEntry=path_parname,
			callback=self._on_recovery_dialog_response,
			escButton=2,  # Escape = Clear button (button 2)
			enterButton=1,  # Enter = Fix button (button 1)
			escOnClickAway=False  # Don't close on click away
		)
	
	def _on_recovery_dialog_response(self, info):
		"""Callback for parameter recovery dialog
		
		Args:
			info: Dictionary containing button info from PopDialog
				- info['buttonNum']: Button number clicked (1 = Fix, 2 = Clear, 3 = Clear All)
				- info['button']: Button text
				- info['ownerComp']: Owner component
		"""
		if self._pending_invalidation is None:
			return  # No pending invalidation
		
		slot_idx = self._pending_invalidation['slot_idx']
		bank_idx = self._pending_invalidation['bank_idx']
		is_pargroup = self._pending_invalidation['is_pargroup']
		update_ui = self._pending_invalidation['update_ui']
		
		# Get the text entry value from the dialog
		entryText = info['enteredText']
		
		# Get the original path from repo storage for comparison
		orig_op_path, orig_par_name, _ = self._get_parameter_info_from_repo(slot_idx, bank_idx)
		
		# Clear pending invalidation
		self._pending_invalidation = None
		
		# Button 1 = Fix, Button 2 = Clear (single), Button 3 = Clear All (batch)
		buttonNum = info['buttonNum']
		if buttonNum == 1:
			# FIX: Batch update all related slots
			# FIRST: Check if this is a path change that should trigger batch update
			# We need to do batch update BEFORE saving to table, otherwise save will clear repo!
			should_batch_update = False
			if orig_op_path and ':' in entryText:
				new_op_path, new_par_name = entryText.rsplit(':', 1)
				new_op_path = new_op_path.strip()
				
				# Check if the operator path changed (not just the param name)
				if new_op_path != orig_op_path:
					should_batch_update = True
					
					# Batch update other slots BEFORE recovering this one
					# (otherwise save_bank_to_table will clear the repo!)
					self._batch_update_operator_path(
						old_op_path=orig_op_path, 
						new_op_path=new_op_path,
						exclude_slot=(slot_idx, bank_idx)
					)
			
			# THEN: Try to recover this parameter
			success = self._try_recover_parameter(
				slot_idx=slot_idx,
				bank_idx=bank_idx,
				path_parname=entryText,
				is_pargroup=is_pargroup
			)
			
			if success:
				# Recovery succeeded - remove from invalidation queue
				if (slot_idx, bank_idx) in self._invalidation_queue:
					self._invalidation_queue.remove((slot_idx, bank_idx))
			else:
				# Recovery failed - clear the slot
				self._clear_slot_data(slot_idx, bank_idx)
				
				# Remove from invalidation queue since we're clearing it
				if (slot_idx, bank_idx) in self._invalidation_queue:
					self._invalidation_queue.remove((slot_idx, bank_idx))
				
				# Track bank for saving after queue completes (don't save now to preserve repo data)
				self._banks_to_save_after_queue.add(bank_idx)
				
				if update_ui:
					self._update_ui_after_invalidation(slot_idx, bank_idx)
		elif buttonNum == 2:
			# CLEAR: Clear only this slot (no batch operation)
			self._clear_slot_data(slot_idx, bank_idx)
			
			# Remove from invalidation queue since we're clearing it
			if (slot_idx, bank_idx) in self._invalidation_queue:
				self._invalidation_queue.remove((slot_idx, bank_idx))
			
			# Track bank for saving after queue completes (don't save now to preserve repo data)
			self._banks_to_save_after_queue.add(bank_idx)
			
			if update_ui:
				self._update_ui_after_invalidation(slot_idx, bank_idx)
		else:
			# CLEAR ALL: Batch-clear all slots with the same operator path
			# (_batch_clear_operator_path handles removing slots from queue internally)
			if orig_op_path:
				self._batch_clear_operator_path(orig_op_path, exclude_slot=(slot_idx, bank_idx))
			
			# Clear this slot
			self._clear_slot_data(slot_idx, bank_idx)
			
			# Remove from invalidation queue since we're clearing it
			if (slot_idx, bank_idx) in self._invalidation_queue:
				self._invalidation_queue.remove((slot_idx, bank_idx))
			
			# Track bank for saving after queue completes (don't save now to preserve repo data)
			self._banks_to_save_after_queue.add(bank_idx)
			
			if update_ui:
				self._update_ui_after_invalidation(slot_idx, bank_idx)
		
		# If we're processing a queue, handle the next invalidation
		if self._processing_invalidation:
			# Defer to next frame to allow current dialog to fully close
			run("args[0]._process_next_invalidation()", self, delayFrames=1)
	
	def _try_recover_parameter(self, slot_idx: int, bank_idx: int, 
	                            path_parname: str, is_pargroup: bool, save_to_table: bool = True) -> bool:
		"""Try to recover a parameter from user-provided path:parname
		
		Args:
			slot_idx: Slot index to restore to
			bank_idx: Bank index
			path_parname: User-provided "operator_path:par_name" string
			is_pargroup: Whether to look for a ParGroup or single Par
			save_to_table: Whether to save to table after recovery (default True, set False for batch operations)
			
		Returns:
			True if recovery succeeded, False otherwise
		"""
		try:
			# Parse path:parname
			if ':' not in path_parname:
				return False
			
			op_path, par_name = path_parname.rsplit(':', 1)
			op_path = op_path.strip()
			par_name = par_name.strip()
			
			if not op_path or not par_name:
				return False
			
			# Try to get the operator
			target_op = op(op_path)
			if target_op is None:
				return False
			
			# Try to get the parameter (try both parGroup and par if is_pargroup hint fails)
			recovered_par = None
			
			if is_pargroup:
				# Try ParGroup first
				recovered_par = getattr(target_op.parGroup, par_name, None)
				if recovered_par is None:
					# Maybe it's actually a single Par, try that
					recovered_par = getattr(target_op.par, par_name, None)
			else:
				# Try single Par first
				recovered_par = getattr(target_op.par, par_name, None)
				if recovered_par is None:
					# Maybe it's actually a ParGroup, try that
					recovered_par = getattr(target_op.parGroup, par_name, None)
			
			# Check if parameter is valid
			if recovered_par is None:
				return False
			
			# Verify it's a supported parameter type
			if not ParameterValidator.is_supported_parameter_type(recovered_par):
				return False
			
			# Success! Restore the parameter to the slot
			self.parent.slotPars[bank_idx][slot_idx] = recovered_par
			
			# Save to table (unless this is a batch operation that will save later)
			if save_to_table:
				# If we're processing invalidation queue, defer save to preserve repo data
				if self._processing_invalidation:
					self._banks_to_save_after_queue.add(bank_idx)
				else:
					self.parent.repo_manager.save_bank_to_table(bank_idx)
			
			# Update UI if this is the current bank
			if bank_idx == self.parent.currBank:
				# Update button label
				if hasattr(self.parent, 'ui_manager'):
					label = LabelFormatter.get_label_for_parameter(recovered_par, self.parent.labelDisplayMode)
					self.parent.ui_manager._set_button_label(slot_idx, label)
				
				# If this was the active slot, update the active slot cache
				if self.parent.activeSlot == slot_idx:
					self.parent._activeSlotPar = recovered_par
					self.parent.display_manager.update_parameter_display(recovered_par)
				
				# Update LEDs
				self.parent.display_manager.update_slot_leds(
					current_slot=self.parent.activeSlot,
					previous_slot=None
				)
			
			return True
			
		except Exception as e:
			return False
	
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
		
		# Assign parameter (or ParGroup) to runtime storage
		self.parent.slotPars[currBank][slot_idx] = parameter
		
		# Update table for persistence (only current bank for performance)
		self.parent.repo_manager.save_bank_to_table(currBank)

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
		self.parent._activeSlotPar = parameter  # Cache the active parameter for fast access
		
		# Turn off hovered UI color when assigning a slot
		self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Update UI button label
		if hasattr(self.parent, 'ui_manager'):
			label = LabelFormatter.get_label_for_parameter(parameter, self.parent.labelDisplayMode)
			self.parent.ui_manager._set_button_label(slot_idx, label)
		
		# Update displays and feedback
		try:
			param_label = LabelFormatter.get_label_for_parameter(parameter, self.parent.labelDisplayMode)
			self.parent.display_manager.update_parameter_display(parameter, bottom_text=ScreenMessages.LEARNED)
			
			# Update LEDs and outline color
			self.parent.display_manager.update_slot_leds(current_slot=slot_idx, previous_slot=old_active_slot)
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		except Exception as e:
			# Display update failed - likely due to invalid parameters in other slots
			# Queue invalidation check to show recovery dialogs
			if 'Invalid Par' in str(e) or 'tdError' in str(type(e).__name__):
				self.queue_invalidation_check()
			else:
				raise  # Re-raise unexpected errors
		

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
		
		# Update table for persistence (only current bank for performance)
		self.parent.repo_manager.save_bank_to_table(currBank)
		
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
		
		# Check if parameter is valid - if not, queue invalidation check
		try:
			if not slot_par.valid:
				# Parameter is invalid - queue invalidation check for all slots
				self.queue_invalidation_check()
				return False
		except:
			# Accessing .valid failed - parameter is definitely invalid
			self.queue_invalidation_check()
			return False

		# Clear any unused captured values from previous slot
		if self.parent.activeSlot is not None:
			old_slot_par = self.parent.slotPars[currBank][self.parent.activeSlot]
			if old_slot_par is not None and old_slot_par.valid:
				self.parent.undo_manager.on_slot_deactivated(old_slot_par)
		
		old_active_slot = self.parent.activeSlot
		self.parent.activeSlot = slot_idx
		self.parent._activeSlotPar = slot_par  # Store directly for ultra-fast access
		self.parent.bankActiveSlots[currBank] = slot_idx
		
		# Update table for persistence (only current bank for performance)
		self.parent.repo_manager.save_bank_to_table(currBank)
		
		# Turn off hovered UI color when activating a slot
		self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Update display with slot parameter
		if slot_par is not None and slot_par.valid:
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
			
			# Check for any invalid parameters in this bank after successful activation
			self.queue_invalidation_check()
			
			return True
		
		return False

	def recall_bank(self, bank_idx: int):
		"""Switch to a different bank and recall its last active slot"""
		# Block bank changes while invalidation is active (dialog or queue processing)
		if self.is_invalidation_active():
			return False
		
		# Validate bank index
		if bank_idx < 0 or bank_idx >= self.parent.numBanks:
			return False
		
		try:
			# Clear any unused captured values from current bank's active slot
			old_bank = self.parent.currBank
			if self.parent.activeSlot is not None:
				old_slot_par = self.parent.slotPars[old_bank][self.parent.activeSlot]
				if old_slot_par is not None:
					self.parent.undo_manager.on_slot_deactivated(old_slot_par)
			
			# Save current active slot for current bank
			self.parent.bankActiveSlots[old_bank] = self.parent.activeSlot
			
			# Update table for old bank persistence before switching
			self.parent.repo_manager.save_bank_to_table(old_bank)
			
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
					# Check if parameter is still valid
					is_valid = False
					try:
						is_valid = slot_par.valid
					except:
						pass  # Parameter is invalid
					
					if not is_valid:
						# Parameter is invalid - treat as empty
						slot_par = None
				
				if slot_par is not None:
					self.parent.activeSlot = previous_slot
					self.parent._activeSlotPar = slot_par  # Store directly for ultra-fast access
					
					# Turn off hovered UI color when recalling a slot
					self.parent.ui_manager.set_hovered_ui_color(-1)
					
					# Capture initial values for undo when recalling slot
					self.parent.undo_manager.on_slot_activated(slot_par)
				else:
					self.parent.activeSlot = None
					self.parent._activeSlotPar = None  # Clear cached active slot parameter
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
			
			# Always check for invalid parameters after bank switch
			# This ensures all invalid parameters in ALL banks are handled sequentially with dialogs
			# (queue_invalidation_check only shows dialogs if it finds invalid params)
			self.queue_invalidation_check()
			
			return True
			
		except Exception as e:
			# Catch invalid parameter errors during bank recall
			if 'Invalid Par' not in str(e) and 'tdError' not in str(type(e).__name__):
				raise  # Re-raise unexpected errors
			
			# Ensure we're on the new bank with no active slot before showing dialogs
			self.parent.currBank = bank_idx
			self.parent.activeSlot = None
			self.parent._activeSlotPar = None
			self.parent.bankActiveSlots[bank_idx] = None
			
			# Restore hovered UI color
			if self.parent.evalColorhoveredui:
				self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
			else:
				self.parent.ui_manager.set_hovered_ui_color(-1)
			
			# Try to refresh display (might fail if there are invalid parameters)
			try:
				self._refresh_bank_display()
			except Exception as display_error:
				# Show basic empty display if refresh fails
				self.parent.display_manager.update_all_display(
					0, 0, 1, 
					ScreenMessages.HOVER, 
					ScreenMessages.HOVER, 
					compress=False
				)
			
			# Queue invalidation check to show recovery dialogs sequentially
			# This will find all invalid parameters and show dialog with batch update option
			self.queue_invalidation_check()
			
			return True
	
	def _refresh_bank_display(self):
		"""Refresh all display elements when switching banks"""
		currBank = self.parent.currBank
		
		# Update bank indicator on both displays
		self.parent.display_manager.set_bank_indicator(currBank)
		
		# Update UI button labels and colors for the new bank (comprehensive refresh)
		if hasattr(self.parent, 'ui_manager'):
			self.parent.ui_manager.refresh_all_button_states()
		
		# Update slot LEDs on both VSN1 hardware and UI
		self.parent.display_manager.update_all_slot_leds()
		
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
		if self.parent.activeSlot is None or self.parent._activeSlotPar is None or not self.parent._activeSlotPar.valid:
			return
		self.parent._set_parexec_pars(self.parent.hoveredPar)
		
		old_active_slot = self.parent.activeSlot
		currBank = self.parent.currBank
		
		# Clear active slot
		self.parent.activeSlot = None
		self.parent._activeSlotPar = None  # Clear cached active slot parameter
		self.parent._set_parexec_pars(None)
		self.parent.bankActiveSlots[currBank] = None
		
		# Update table for persistence (only current bank for performance)
		self.parent.repo_manager.save_bank_to_table(currBank)
		
		# Restore hovered UI color if enabled (now in hover mode)
		if self.parent.evalColorhoveredui:
			self.parent.ui_manager.set_hovered_ui_color(self.parent.evalColorindex - 1)
		else:
			self.parent.ui_manager.set_hovered_ui_color(-1)
		
		# Get label for hovered parameter (or ParGroup)
		if self.parent.hoveredPar is not None and self.parent.hoveredPar.valid:
			# Use formatter to get proper label (handles both Par and ParGroup)
			label = LabelFormatter.get_label_for_parameter(self.parent.hoveredPar, self.parent.labelDisplayMode)
		else:
			label = ScreenMessages.HOVER

		if self.parent.hoveredPar is not None and self.parent.hoveredPar.valid:
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
			self.parent._activeSlotPar = None  # Clear cached active slot parameter
			self.parent.bankActiveSlots[bank_idx] = None
		
		# Update table for persistence (only this bank for performance)
		self.parent.repo_manager.save_bank_to_table(bank_idx)
			
		# If we're currently in this bank, update UI
		if bank_idx == self.parent.currBank:
			if self.parent.activeSlot == slot_idx:
				self.parent.activeSlot = None
				self.parent._activeSlotPar = None  # Clear cached active slot parameter
				
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