from constants import VSN1ColorIndex, ScreenMessages
from formatters import LabelFormatter

class UIManager:
	"""Manager for UI elements"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.ui = self.parent.ownerComp.op('UI')
		

	@property
	def buttons(self):
		return self.ui.op('BUTTONS').ops('button*')

	@property
	def ui_enabled(self) -> bool:
		return self.parent.evalEnableui

	def _set_top_text(self, text: str):
		self.ui.par.Toptext.val = text

	def _set_bottom_text(self, text: str):
		self.ui.par.Bottomtext.val = text

	def _set_circle_fill(self, percentage: float):
		self.ui.par.Circlefill = tdu.clamp(tdu.remap(percentage, 0, 1, 0.05, 1), 0.05, 1)

	def _set_button_color(self, index: int, color_phase_idx: int):
		button = self.buttons[index]
		if button is None:
			return
		button.par.Colorphaseidx = color_phase_idx

	
	def render_display(self, val, norm_min, norm_max, processed_label: str, bottom_text: str, percentage: float, step_indicator = None):
		"""Render display data to UI - ONLY the UI parameter updates, no logic"""
		if not self.ui_enabled:
			return
		# Set UI parameters - ONLY difference from VSN1 renderer
		self._set_circle_fill(percentage)
		self._set_top_text(processed_label)
		self._set_bottom_text(bottom_text)
		
		# Set step indicator if provided
		if step_indicator is not None:
			self.set_step_indicator(step_indicator)
	
	def clear_screen(self):
		"""Clear the UI display - ONLY the UI parameter updates"""
		if not self.ui_enabled:
			return
		self._set_circle_fill(0.5)
		self._set_top_text("")
		self._set_bottom_text("")

	def set_step_indicator(self, index: int):
		if not self.ui_enabled:
			return
		self.ui.par.Stepindicatorindex = index
		# get step value from seqSteps
		step_value = self.parent.seqSteps[index].par.Step.eval()
		self.ui.par.Stepvalue = step_value
		#self.ui.par.StepIndicator.val = index
		pass
	
	# UI equivalents for VSN1 features
	def update_all_slot_indicators(self):
		"""Update all slot indicators in UI"""
		if not self.ui_enabled:
			return
		for i in range(len(self.buttons)):
			self._set_button_color(i, 0)
		pass
	
	def update_slot_indicators(self, current_slot=None, previous_slot=None):
		"""Update specific slot indicators in UI"""
		if not self.ui_enabled:
			return
		
		# Update previous slot LED (if specified)
		if previous_slot is not None:
			prev_led_value = self.parent.display_manager.get_slot_state_value(previous_slot)
			self._set_button_color(previous_slot, prev_led_value)
		
		# Update current slot LED (if specified)
		if current_slot is not None:
			curr_led_value = self.parent.display_manager.get_slot_state_value(current_slot)
			self._set_button_color(current_slot, curr_led_value)
		pass
	
	def update_outline_color(self, color_index: int):
		"""Update UI outline/border color equivalent"""
		if not self.ui_enabled:
			return
		self.ui.par.Slotactive = True if color_index == VSN1ColorIndex.WHITE.value else False
		pass
	
	def send_slot_feedback(self, slot_idx: int, value: int):
		"""Send slot feedback to UI equivalent"""
		if not self.ui_enabled:
			return
		self._set_button_color(slot_idx, value)
		pass

	def _set_button_label(self, slot_idx: int, label: str):
		button = self.buttons[slot_idx]
		if button is None:
			return
		label = LabelFormatter.format_label(label, self.parent.labelDisplayMode) if label != ScreenMessages.HOVER else ScreenMessages.HOVER
		button.par.label = label
		
		# Also update button color to match slot state
		color_value = self.parent.display_manager.get_slot_state_value(slot_idx)
		self._set_button_color(slot_idx, color_value)