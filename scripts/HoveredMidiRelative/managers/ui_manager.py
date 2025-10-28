
'''Info Header Start
Name : ui_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.193.toe
Saveversion : 2023.12120
Info Header End'''
from constants import VSN1ColorIndex, ScreenMessages, StepMode, OverrideUIElements
from formatters import LabelFormatter

class UIManager:
	"""Manager for UI elements"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.ui = self.parent.ownerComp.op('_UI/UI')

		self.default_ui_colors = {}
		for _row in self.parent.ownerComp.op('table_default_ui_cols').rows():
			_element = _row[0].val
			_col = (float(_row[1].val), float(_row[2].val), float(_row[3].val))
			self.default_ui_colors[_element] = _col

		self.page_cols = []
		for _row in self.parent.ownerComp.op('null_page_cols').rows():
			_cols = (float(_cell.val) for _cell in _row)
			self.page_cols.append(list(_cols))

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
		self.ui.par.Circlefill = tdu.clamp(tdu.remap(percentage, 0, 1, 0.0, 1), 0.0, 1)

	def _set_button_color(self, index: int, color_phase_idx: int):
		button = self.buttons[index]
		if button is None:
			return
		button.par.Colorphaseidx = color_phase_idx

	def _set_defaultnotch(self, norm_default: float):
		self.ui.par.Normdefault = norm_default

	
	def render_display(self, val, norm_min, norm_max, processed_label: str, bottom_text: str, percentage: float, step_indicator = None, norm_default = None):
		"""Render display data to UI - ONLY the UI parameter updates, no logic"""
		if not self.ui_enabled:
			return
		# Set UI parameters - ONLY difference from VSN1 renderer
		self._set_circle_fill(percentage)
		self._set_top_text(processed_label)
		self._set_bottom_text(bottom_text)
		if norm_default is None:
			norm_default = -1
		self._set_defaultnotch(norm_default)
		
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
		self._set_defaultnotch(-1)

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
		"""Update all slot color indicators in UI (called by display_manager)"""
		if not self.ui_enabled:
			return
		# Only update colors, not labels (labels are handled separately)
		for i in range(len(self.buttons)):
			slot_state = self.parent.display_manager.get_slot_state_value(i)
			self._set_button_color(i, slot_state)
	
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

	def set_bank_indicator(self, bank_idx: int):
		"""Set bank indicator in UI"""
		if not self.ui_enabled:
			return
		# Update UI parameter to show current bank
		self.ui.par.Currentbank = bank_idx
	
	def refresh_all_button_states(self):
		"""Refresh all button labels and colors for current bank"""
		if not self.ui_enabled:
			return
		
		currBank = self.parent.currBank
		for i in range(self.parent.numSlots):
			# Update label
			if (i < len(self.parent.slotPars[currBank]) and 
				self.parent.slotPars[currBank][i] is not None):
				label = LabelFormatter.get_label_for_parameter(
					self.parent.slotPars[currBank][i], 
					self.parent.labelDisplayMode
				)
				self._set_button_label(i, label)
			else:
				self._set_button_label(i, ScreenMessages.HOVER)
			
			# Update color based on slot state
			slot_state = self.parent.display_manager.get_slot_state_value(i)
			self._set_button_color(i, slot_state)
		
	def _set_button_label(self, slot_idx: int, label: str):
		"""Set button label for a slot"""
		if not self.ui_enabled or slot_idx >= len(self.buttons):
			return
		button = self.buttons[slot_idx]
		if button is None:
			return
		label = LabelFormatter.format_label(label, self.parent.labelDisplayMode) if label != ScreenMessages.HOVER else ScreenMessages.HOVER
		button.par.label = label
		
		# Also update button color to match slot state
		color_value = self.parent.display_manager.get_slot_state_value(slot_idx)
		self._set_button_color(slot_idx, color_value)

	def set_bank_indicator(self, bank_idx: int):
		"""Set bank indicator in UI"""
		if not self.ui_enabled:
			return
		# Update UI parameter to show current bank
		self.ui.par.Bankindicatorindex = bank_idx

	def set_stepmode_indicator(self, step_mode: StepMode):
		"""Set mode indicator in UI"""
		if not self.ui_enabled:
			return
		self.ui.par.Modecolorindex = 1 if step_mode == StepMode.FIXED else 2
		self.render_display(0.5, 0, 1, '_MODE_', '_FIXED_' if step_mode == StepMode.FIXED else '_ADAPT_', 0.5)

	def set_hovered_ui_color(self, color_index: int):
		"""Set hovered UI color with proper brightness adjustments per element type.
		
		Color relationships from OverrideUIElements:
		- .selected.loc is darkest (base)
		- .selected is middle (+ 0.025)
		- .loc is lightest (+ 0.05 of .selected, + 0.075 of .selected.loc)
		- For menubar/button it's opposite (.sel is darker)
		- Toggle thumb on is 0.65 lighter than off
		"""
		page_col = self.page_cols[color_index % 4]
		multiplier = 1 if color_index != 2 else 0.5
		for _element in OverrideUIElements.PARMS:
			try:
				if color_index != -1:
					# Calculate base color (darkest variant)
					base_color = [_col * multiplier for _col in page_col]
					
					# Apply brightness adjustments based on element type
					if '.selected.loc' in _element:
						# Darkest variant (base)
						ui.colors[_element] = base_color
					elif '.selected' in _element:
						# Middle variant (+ 0.025)
						ui.colors[_element] = [min(1.0, c + 0.025) for c in base_color]
					elif '.loc' in _element:
						# Check if it's button/menubar (opposite logic)
						if 'button' in _element or 'menubar' in _element:
							# For button/menubar, .loc is darker than .sel
							if '.sel' in _element:
								# .sel is lightest for button/menubar
								ui.colors[_element] = [min(1.0, c + 0.075) for c in base_color]
							else:
								# .loc is darker (base)
								ui.colors[_element] = base_color
						elif 'toggle.thumb.on' in _element:
							# Toggle on is 0.65 lighter than off
							ui.colors[_element] = [min(1.0, c + 0.25) for c in base_color]
						elif 'toggle.thumb.off' in _element:
							# Toggle off is base
							ui.colors[_element] = base_color
						else:
							# Standard .loc is lightest (+ 0.075)
							ui.colors[_element] = [min(1.0, c + 0.075) for c in base_color]
					elif '.sel' in _element:
						# For button/menubar .sel without .loc
						if 'button' in _element or 'menubar' in _element:
							# .sel is lightest for button/menubar
							ui.colors[_element] = [min(1.0, c + 0.075) for c in base_color]
						else:
							# Standard .sel (shouldn't normally hit this)
							ui.colors[_element] = [min(1.0, c + 0.05) for c in base_color]
					else:
						# Fallback
						ui.colors[_element] = base_color
				else:
					# Reset to default, stored in table_default_ui_colors
					_default_color = self.default_ui_colors[_element]
					ui.colors[_element] = _default_color
			except:
				pass