
'''Info Header Start
Name : handlers
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.187.toe
Saveversion : 2023.12120
Info Header End'''
from constants import MidiConstants, VSN1ColorIndex, ScreenMessages, SecondaryMode, StepMode
from validators import ParameterValidator

class MidiMessageHandler:
	"""Handles MIDI message processing logic"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext

	@property
	def isFromBankOff(self) -> bool:
		"""Used for checking if a bank off message coincides with a step message
		since by default these two messages are assigned to the same MIDI button
		"""
		return self.parent.ownerComp.op('null_midibank')[0].eval() == 1
	
	
	def handle_step_message(self, index: int, value: int) -> bool:
		"""Handle step change messages"""
		blocks = self.parent._index_to_blocks(index, self.parent.seqSteps)
		if not blocks:
			return False
			
		block = blocks[0]
		if value == 0 and not self.isFromBankOff:
			self.parent._currStep = block.par.Step.eval()
		elif not self.parent.evalPersiststep and value == 0:
			self.parent._currStep = self.parent.evalDefaultstepsize
		return True
	
	def handle_knob_message(self, index: int, value: int, active_par) -> bool:
		"""Handle knob control messages"""
		knob_index = self.parent._safe_get_midi_index(self.parent.evalKnobindex, default=-1)
		if int(index) != knob_index:
			return False
			
		if active_par is not None and active_par.owner != self.parent.ownerComp:
			self._do_step(self.parent._currStep, value)
		return True
	
	def handle_push_message(self, index: int, value: int, active_par) -> bool:
		"""Handle pulse button messages"""
		push_index = self.parent._safe_get_midi_index(self.parent.evalPushindex, default=-1)
		if index != push_index:
			return False
			
		if active_par is not None and active_par.owner != self.parent.ownerComp:
			if value == MidiConstants.MAX_VELOCITY:
				if active_par.isPulse or active_par.isMomentary:
					active_par.pulse()
				elif active_par.isMomentary:
					# TODO: implement mouse-like momentary behavior
					active_par.pulse(frames=1)
				elif active_par.isToggle:
					active_par.val = not active_par.eval()
			self.parent.display_manager.update_parameter_display(active_par)
		return True
	
	def handle_slot_message(self, index: int, value: int) -> bool:
		"""Handle slot selection messages"""
		if value != MidiConstants.MAX_VELOCITY:
			return False
			
		blocks = self.parent._index_to_blocks(index, self.parent.seqSlots)
		if not blocks:
			return False
			
		block = blocks[0]
		block_idx = block.index
		
		# Get previous slot index for LED feedback
		prev_slot_index = self.parent.activeSlot
		
		# Check if slot exists and has a parameter in current bank
		currBank = self.parent.currBank
		if (currBank < len(self.parent.slotPars) and 
			block_idx < len(self.parent.slotPars[currBank]) and 
			self.parent.slotPars[currBank][block_idx] is not None):
			# Activate slot
			old_active_slot = self.parent.activeSlot
			self.parent.activeSlot = block_idx
			self.parent.display_manager.update_parameter_display(self.parent.slotPars[currBank][block_idx])
			self.parent.bankActiveSlots[currBank] = block_idx
			# Update LEDs: previous slot and new active slot
			self.parent.display_manager.update_slot_leds(current_slot=block_idx, previous_slot=old_active_slot)
			# Update outline color for active slot
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.WHITE.value)
		else:
			# Deactivate slot (return to hover mode)
			old_active_slot = self.parent.activeSlot
			self.parent.activeSlot = None
			if currBank < len(self.parent.bankActiveSlots):
				self.parent.bankActiveSlots[currBank] = None
			label = self.parent.hoveredPar.label if self.parent.hoveredPar is not None else ScreenMessages.HOVER
			compress = False if label == ScreenMessages.HOVER else True
			self.parent.display_manager.update_all_display(0.5, 0, 1, label, ScreenMessages.HOVER, compress=compress)
			# Update LED: turn off the previously active slot
			self.parent.display_manager.update_slot_leds(previous_slot=old_active_slot)
			# Update outline color for hover mode
			self.parent.display_manager.update_outline_color_index(VSN1ColorIndex.COLOR.value)
		return True

	def handle_bank_message(self, index: int) -> bool:
		"""Handle bank change messages"""
		blocks = self.parent._index_to_blocks(index, self.parent.seqBanks)
		if not blocks:
			return False
		
		block = blocks[0]
		bank_idx = block.index
		
		# Switch to the requested bank
		return self.parent.slot_manager.recall_bank(bank_idx)

	def _do_step(self, step: float, value: int):
		"""Apply step value to active parameter based on MIDI input"""
		active_par = self.parent.activePar
		if active_par is None or not ParameterValidator.is_valid_parameter(active_par):
			return
			
		diff = value - MidiConstants.MIDI_CENTER_VALUE
		
		if active_par.isNumber:
			# Apply secondary step if active
			if self.parent.secondaryPushState and self.parent.secondaryMode == SecondaryMode.STEP:
				step = self.parent.evalSecondarystep or step
			
			# Calculate step amount based on mode
			if self.parent.stepMode == StepMode.RELATIVE:
				step_amount = step * diff
			else: # AutoRange mode - step scales with parameter range
				min_val, max_val = active_par.normMin, active_par.normMax
				step_amount = ((max_val - min_val) * step) * diff
			
			# Handle integer parameters with different step behavior
			if active_par.isInt:
				if self.parent.stepMode == StepMode.RELATIVE:
					# TODO: debatable if this fixed step is good for ints in relative mode. What's the alternative?
					step_amount = 1 if diff > 0 else -1
				else:
					step_amount = max(1, ((max_val - min_val) * step)) * (1 if diff > 0 else -1)
			
			# Apply the step to current value
			active_par.val = active_par.eval() + step_amount
			
		elif active_par.isMenu:
			# Handle menu parameters - step through menu options
			if abs(diff) >= 1:  # Only change on significant step
				current_index = active_par.menuIndex
				step_direction = 1 if diff > 0 else -1
				new_index = current_index + step_direction
				active_par.menuIndex = new_index
				
		elif active_par.isToggle or active_par.isMomentary:
			# Handle toggle parameters - step through on/off states
			current_val = active_par.eval()
			if diff > 0 and not current_val:
				active_par.val = True
			elif diff < 0 and current_val:
				active_par.val = False
		else:
			# Unsupported parameter type
			return
			
		# Update screen display
		self.parent.display_manager.update_parameter_display(active_par)

