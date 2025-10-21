
'''Info Header Start
Name : display_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.201.toe
Saveversion : 2023.12120
Info Header End'''
import re
from typing import Optional
from constants import ScreenMessages, VSN1ColorIndex, KnobLedUpdateMode, StepMode
from formatters import LabelFormatter
from validators import ParameterValidator
import math

class DisplayManager:
	"""Unified display manager that handles ALL display logic and delegates to renderers"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.vsn1_renderer = parent_ext.vsn1_manager
		self.ui_renderer = parent_ext.ui_manager
	
	def show_parameter_error(self, par, error_msg: str):
		"""Show error message for invalid parameter."""
		param_label = LabelFormatter.get_label_for_parameter(par, self.parent.labelDisplayMode)
		self.update_all_display(0.5, 0, 1, param_label, error_msg, compress=True)
	
	def get_slot_state_value(self, slot_idx: int) -> int:
		"""Centralized slot state logic: 0=free (hover), 127=occupied, 255=active"""
		# Check if slot is active
		if self.parent.activeSlot == slot_idx:
			return 255  # Active slot
			
		# Check if slot is occupied
		currBank = self.parent.currBank
		if (currBank < len(self.parent.slotPars) and 
			slot_idx < len(self.parent.slotPars[currBank]) and 
			self.parent.slotPars[currBank][slot_idx] is not None):
			return 127   # Occupied slot
			
		return 0  # Free slot (hover mode)
	
	def clear_screen(self):
		"""Clear all displays"""
		self.vsn1_renderer.clear_screen()
		self.ui_renderer.clear_screen()
	
	def update_all_display(self, val, norm_min, norm_max, 
						  label: str, display_text: Optional[str] = None, step_indicator = None, compress: bool = True):
		"""Update all displays with parameter info - handles ALL logic here"""
		if compress:
		# Process label based on display mode and compression setting
			processed_label = LabelFormatter.format_label(label, self.parent.labelDisplayMode)
		else:	
			processed_label = LabelFormatter.truncate_label(label)
		
		# Calculate circle fill percentage - handle both numeric and string values
		try:
			val_num = float(val)
			norm_min_num = float(norm_min) 
			norm_max_num = float(norm_max)
			
			if norm_max_num != norm_min_num:
				percentage = (val_num - norm_min_num) / (norm_max_num - norm_min_num)
			else:
				percentage = 0.5
		except (ValueError, TypeError):
			percentage = 0.5
		
		# Use display_text if provided, otherwise format the value
		if display_text is not None:
			bottom_text = display_text
		else:
			bottom_text = LabelFormatter.format_value(val)
		
		# Delegate to renderers with processed data
		self.vsn1_renderer.render_display(val, norm_min, norm_max, processed_label, bottom_text, percentage, step_indicator)
		
		if bottom_text in [ScreenMessages.HOVER, ScreenMessages.EXPR, ScreenMessages.UNSUPPORTED] and self.parent.knobLedUpdateMode in [KnobLedUpdateMode.VALUE]:
			self.vsn1_renderer.update_knob_leds_gradual(0)
		elif self.parent.knobLedUpdateMode in [KnobLedUpdateMode.VALUE]:
			self.vsn1_renderer.update_knob_leds_gradual(percentage)

		
		self.ui_renderer.render_display(val, norm_min, norm_max, processed_label, bottom_text, percentage, step_indicator)
    
	def update_parameter_display(self, par, bottom_text: str = None, force_knob_leds: bool = False):
		"""Update displays for a specific parameter - handles ALL logic here"""
		if par is None:
			return
		if not par.valid:
			return
			
		# Handle different parameter types - ALL logic here
		if par.isMenu:
			val = par.menuIndex
			min_val, max_val = 0, len(par.menuNames) - 1
			
			# For string menus, show the actual value if it's not in menuNames, otherwise show label
			if par.isString and par.eval() not in par.menuNames:
				display_text = str(par.eval())
			else:
				display_text = str(par.menuLabels[par.menuIndex])
			
			display_text = LabelFormatter.format_label(display_text, self.parent.labelDisplayMode)
		elif par.isToggle or par.isMomentary:
			val = 1 if par.eval() else 0
			min_val, max_val = 0, 1
			display_text = "On" if val else "Off"
		elif par.isPulse:
			val = 1 if par.eval() else 0
			min_val, max_val = 0, 1
			display_text = f"_PULSE_"
		else:
			val = par.eval()
			min_val, max_val = par.normMin, par.normMax
			display_text = None

		if bottom_text is not None:
			display_text = bottom_text

		# Use the centralized label method which handles parameter groups
		label = LabelFormatter.get_label_for_parameter(par, self.parent.labelDisplayMode)
		
		# Fallback logic for parameters without labels (sequence blocks)
		if not par.label and (block := par.sequenceBlock):
			name = par.name
			name = re.split(r'\d+', name)[-1]
			if name:
				if isinstance(block.owner, constantCHOP):
					fallback_label = block.par.name.eval()
				else:
					fallback_label = name.capitalize()
				# Apply formatting to the fallback label too
				label = LabelFormatter.format_label(fallback_label, self.parent.labelDisplayMode)
		
		# Use the unified display logic
		self.update_all_display(val, min_val, max_val, label, display_text, compress=True)
		if force_knob_leds:
			if self.parent.knobLedUpdateMode in [KnobLedUpdateMode.VALUE]:
				percentage = (val - min_val) / (max_val - min_val)
				self.vsn1_renderer.update_knob_leds_gradual(percentage)
			elif self.parent.knobLedUpdateMode in [KnobLedUpdateMode.STEPS]:
				index = next((i for i, s in enumerate(self.parent.seqSteps) if s.par.Step.eval() == self.parent._currStep), None)
				self.vsn1_renderer.update_knob_leds_steps(index)
			elif self.parent.knobLedUpdateMode in [KnobLedUpdateMode.OFF]:
				self.vsn1_renderer.update_knob_leds_gradual(0)
	
	def update_step_display(self, step: float):
		"""Update displays with current step value - handles ALL logic here"""
		seq = self.parent.seqSteps
		if len(seq) == 0:
			return
			
		# Calculate step display values
		min_step = min(s.par.Step.eval() for s in seq)
		max_step = max(s.par.Step.eval() for s in seq)
		
		# Map step to 0-1 range for display
		if max_step != min_step:
			mapped_step = (step - min_step) / (max_step - min_step)
		else:
			mapped_step = 0.5

		# Scale for better display
		mapped_step = mapped_step ** 0.5
		
		# Find step index for indicator
		index = next((i for i, s in enumerate(seq) if s.par.Step.eval() == step), None)
		
		self.update_all_display(mapped_step, min_step, max_step, ScreenMessages.STEP, 
							   display_text=str(step), step_indicator=index, compress=False)
		if self.parent.knobLedUpdateMode in [KnobLedUpdateMode.STEPS]:
			self.vsn1_renderer.update_knob_leds_steps(index)

	def set_bank_indicator(self, bank_idx: int):
		self.vsn1_renderer.set_bank_indicator(bank_idx)
		self.ui_renderer.set_bank_indicator(bank_idx)
	
	# VSN1-specific methods that also update UI equivalents
	def update_all_slot_leds(self):
		"""Update all slot LEDs and UI equivalents"""
		self.vsn1_renderer.update_all_slot_leds()
		self.ui_renderer.update_all_slot_indicators()
	
	def update_slot_leds(self, current_slot=None, previous_slot=None):
		"""Update specific slot LEDs and UI equivalents"""
		self.vsn1_renderer.update_slot_leds(current_slot, previous_slot)
		self.ui_renderer.update_slot_indicators(current_slot, previous_slot)
	
	def update_outline_color_index(self, color_index: int):
		"""Update outline color and UI equivalent"""
		self.vsn1_renderer.update_outline_color_index(color_index)
		self.ui_renderer.update_outline_color(color_index)
	
	def send_slot_led_feedback(self, slot_idx: int, value: int):
		"""Send slot feedback to both displays"""
		self.vsn1_renderer.send_slot_led_feedback(slot_idx, value)
		self.ui_renderer.send_slot_feedback(slot_idx, value)

	def set_stepmode_indicator(self, step_mode: StepMode):
		"""Set mode indicator in UI"""
		self.vsn1_renderer.set_stepmode_indicator(step_mode)
		self.ui_renderer.set_stepmode_indicator(step_mode)