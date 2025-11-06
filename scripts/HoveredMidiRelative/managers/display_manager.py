
'''Info Header Start
Name : display_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.201.toe
Saveversion : 2023.12120
Info Header End'''
import re
from typing import Optional, Union
from constants import ScreenMessages, VSN1Constants, KnobLedUpdateMode, StepMode
from formatters import LabelFormatter
from validators import ParameterValidator
import math

class DisplayManager:
	"""Unified display manager that handles ALL display logic and hardware rendering (VSN1 + UI)"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.ui_renderer = parent_ext.ui_manager
		
		# VSN1 hardware communication
		self.grid_comm : IntechGridCommExt = self.parent.ownerComp.op('IntechGridComm').ext.IntechGridCommExt
		self.knob_led_dampen = 0.4
	
	def is_vsn1_enabled(self) -> bool:
		"""Check if VSN1 hardware support is enabled"""
		return self.parent.evalVsn1support
	
	def show_parameter_error(self, par_or_group: Union[Par, ParGroup], error_msg: str):
		"""Show error message for invalid parameter (or ParGroup) while still displaying parameter values."""
		if par_or_group.valid:
			param_label = LabelFormatter.get_label_for_parameter(par_or_group, self.parent.labelDisplayMode)
		else:
			param_label = ScreenMessages.INVALID	
		
		# For UNSUPPORTED parameters, don't show actual values (parameter type isn't supported)
		# For EXPR errors, show actual values (parameter is valid type but has expression)
		if error_msg != ScreenMessages.UNSUPPORTED:
			# Try to get actual parameter values for non-unsupported errors
			display_par = self._get_display_parameter(par_or_group)
			if display_par is not None:
				# Get real parameter values
				val, min_val, max_val, display_text, norm_default, clamps = self._get_parameter_display_values(display_par)
				
				# For EXPR errors, enclose value in parentheses
				if error_msg == ScreenMessages.EXPR:
					if display_text is None:
						# Format value with reduced max length to account for "E(" and ")" wrapper
						formatted_val = LabelFormatter.format_value(val, max_length=VSN1Constants.MAX_VALUE_LENGTH - len(ScreenMessages.EXPR_PREFIX) - 1)
						display_text = f"{ScreenMessages.EXPR_PREFIX}{formatted_val})"
					else:
						# Ensure display_text fits within available space before adding wrapper
						max_content_length = VSN1Constants.MAX_VALUE_LENGTH - len(ScreenMessages.EXPR_PREFIX) - 1
						truncated_text = display_text[:max_content_length]
						display_text = f"{ScreenMessages.EXPR_PREFIX}{truncated_text})"
				
				# Show error with actual parameter values
				self.update_all_display(val, min_val, max_val, param_label, display_text if error_msg == ScreenMessages.EXPR else error_msg, compress=True, norm_default=norm_default, clamps=clamps)
				return
		
		# Default: use hardcoded values for unsupported or when we can't extract parameter info
		self.update_all_display(0, 0, 1, param_label, error_msg, compress=True)
	
	def get_slot_state_value(self, slot_idx: int) -> int:
		"""Centralized slot state logic: 0=free (hover), 127=occupied, 255=active"""
		# Check if slot is active
		if self.parent.activeSlot == slot_idx:
			return 255  # Active slot
		
		# Check if slot is occupied
		currBank = self.parent.currBank
		if self.parent.repo_manager.is_slot_occupied(slot_idx, currBank):
			return 127   # Occupied slot
			
		return 0  # Free slot (hover mode)
	
	def clear_screen(self):
		"""Clear all displays"""
		# VSN1
		if self.is_vsn1_enabled():
			lua_code = "--[[@cb]] lcd:ldaf(0,0,319,239,c[1])lcd:ldrr(3,3,317,237,10,c[2])lcd:ldsw()"
			self.grid_comm.SendLua(lua_code)
		# UI
		self.ui_renderer.clear_screen()
	
	def update_all_display(self, val, norm_min, norm_max, 
						  label: str, display_text: Optional[str] = None, step_indicator = None, compress: bool = True, norm_default = None, clamps = None):
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
		self._render_vsn1_display(val, norm_min, norm_max, processed_label, bottom_text, step_indicator=step_indicator, norm_default=norm_default, clamps=clamps)
		
		if bottom_text in [ScreenMessages.HOVER, ScreenMessages.EXPR, ScreenMessages.UNSUPPORTED] and self.parent.knobLedUpdateMode in [KnobLedUpdateMode.VALUE]:
			self.update_knob_leds_gradual(0)
		elif self.parent.knobLedUpdateMode in [KnobLedUpdateMode.VALUE] and step_indicator is None:
			percentage = tdu.clamp(percentage, 0, 1)
			self.update_knob_leds_gradual(percentage)

		
		self.ui_renderer.render_display(val, norm_min, norm_max, processed_label, bottom_text, percentage, step_indicator=step_indicator, norm_default=norm_default, clamps=clamps)
    
	def update_parameter_display(self, par_or_group: Union[Par, ParGroup], bottom_text: str = None, force_knob_leds: bool = False):
		"""Update displays for a specific parameter (or ParGroup) - handles ALL logic here
		For ParGroups, displays the first valid parameter's value"""
		if getattr(self, 'step_updated', False) and self.parent.knobLedUpdateMode not in [KnobLedUpdateMode.STEPS]:
			self.update_knob_leds_steps(-1)
			self.step_updated = False
		if par_or_group is None:
			return
		
		# Extract the parameter to display
		# For ParGroups: get first valid parameter
		# For single Pars: use as-is
		display_par = self._get_display_parameter(par_or_group)
		if display_par is None:
			return
		
		# Get display values based on parameter type
		val, min_val, max_val, display_text, norm_default, clamps = self._get_parameter_display_values(display_par)
		
		# Override display text if provided, or check if parameter has expression
		if bottom_text is not None:
			display_text = bottom_text
		elif not ParameterValidator.is_valid_parameter(display_par):
			# Parameter has expression - enclose value in parentheses
			if display_text is None:
				# Format value with reduced max length to account for "E(" and ")" wrapper
				formatted_val = LabelFormatter.format_value(val, max_length=VSN1Constants.MAX_VALUE_LENGTH - len(ScreenMessages.EXPR_PREFIX) - 1)
				display_text = f"{ScreenMessages.EXPR_PREFIX}{formatted_val})"
			else:
				# Ensure display_text fits within available space before adding wrapper
				max_content_length = VSN1Constants.MAX_VALUE_LENGTH - len(ScreenMessages.EXPR_PREFIX) - 1
				truncated_text = display_text[:max_content_length]
				display_text = f"{ScreenMessages.EXPR_PREFIX}{truncated_text})"
		
		# Get label (handles both Par and ParGroup)
		label = self._get_parameter_label(par_or_group, display_par)
		
		# Update all displays
		self.update_all_display(val, min_val, max_val, label, display_text, compress=True, norm_default=norm_default, clamps=clamps)
		
		# Handle knob LED updates if forced
		if force_knob_leds:
			self._update_knob_leds(val, min_val, max_val)

	def _get_display_parameter(self, par_or_group: Union[Par, ParGroup]) -> Optional[Par]:
		"""Extract the parameter to display from either a single Par or ParGroup
		For ParGroups, returns the first valid parameter"""
		if ParameterValidator.is_pargroup(par_or_group):
			# Get first valid parameter from the group
			for p in par_or_group:
				if p is not None and ParameterValidator.is_valid_parameter(p):
					return p
			return None
		
		# Single Par - validate it exists
		if not par_or_group.valid:
			return None
		return par_or_group
	
	def _get_parameter_display_values(self, par: Par) -> tuple:
		"""Get display values (val, min_val, max_val, display_text) for a parameter
		Returns tuple: (value, min_value, max_value, display_text)"""
		# Allow StrMenus (isMenu and isString) when the feature is enabled or from active slot
		is_strmenu = par.isMenu and par.isString
		allow_strmenus = self.parent.should_allow_strmenus(par)
		
		if par.isMenu and (not par.isString or (is_strmenu and allow_strmenus)):
			val = par.menuIndex
			min_val, max_val = 0, len(par.menuNames) - 1
			
			# For string menus, show the actual value if it's not in menuNames
			if is_strmenu and par.eval() not in par.menuNames:
				display_text = str(par.eval())
			else:
				display_text = str(par.menuLabels[par.menuIndex])
			
			display_text = LabelFormatter.format_label(display_text, self.parent.labelDisplayMode)
			default = par.default
			# find default in menuNames
			# check if default is in menuNames
			if default in par.menuNames:
				default_idx = par.menuNames.index(default)
				norm_default = default_idx / (len(par.menuNames) - 1)
			else:
				norm_default = 0
		elif par.isToggle or par.isMomentary:
			val = 1 if par.eval() else 0
			min_val, max_val = 0, 1
			display_text = "On" if val else "Off"
			norm_default = 1 if par.default else 0
			
		elif par.isPulse:
			# HACK: sorry
			if (state :=getattr(self.parent.midi_handler, 'is_from_pulsepush', 0)) > 0:
				val = 0 if par.eval() else 1
				# HACK: sorry
				
				if state == 2:
					self.parent.midi_handler.is_from_pulsepush = 3
				elif state == 3:
					self.parent.midi_handler.is_from_pulsepush = 0
			else:
				val = 1 if par.eval() else 0
			min_val, max_val = 0, 1
			display_text = "_PULSE_"
			norm_default = 1 if par.eval() else 0

		elif par.isNumber:  # Numeric parameter
			val = par.eval()
			min_val, max_val = par.normMin, par.normMax
			display_text = None
			norm_default = tdu.remap(par.default, min_val, max_val, 0, 1)
			norm_default = tdu.clamp(norm_default, 0, 1)
		else:
			val = 0
			min_val, max_val = 0, 0
			display_text = None
			norm_default = -1

		clamps = (par.clampMin, par.clampMax)
		return val, min_val, max_val, display_text, norm_default, clamps
	
	def _get_parameter_label(self, original: Union[Par, ParGroup], display_par: Par) -> str:
		"""Get formatted label for display
		Uses ParGroup name for groups, or parameter label for single Pars"""
		# Use the centralized label method (handles ParGroup with > prefix)
		label = LabelFormatter.get_label_for_parameter(original, self.parent.labelDisplayMode)

		# Fallback logic for parameters without labels (sequence blocks)
		# Only applies to single parameters, not ParGroups
		if not ParameterValidator.is_pargroup(original) and not display_par.label:
			if block := display_par.sequenceBlock:
				name = display_par.name
				name = re.split(r'\d+', name)[-1]
				if name:
					if isinstance(block.owner, constantCHOP):
						fallback_label = block.par.name.eval()
					else:
						fallback_label = name.capitalize()
					label = LabelFormatter.format_label(fallback_label, self.parent.labelDisplayMode)
		
		return label
	
	def _update_knob_leds(self, val: float, min_val: float, max_val: float):
		"""Update knob LEDs based on current mode"""
		if self.parent.knobLedUpdateMode in [KnobLedUpdateMode.VALUE]:
			percentage = (val - min_val) / (max_val - min_val) if max_val != min_val else 0.5
			self.update_knob_leds_gradual(percentage)
		elif self.parent.knobLedUpdateMode in [KnobLedUpdateMode.STEPS]:
			index = next((i for i, s in enumerate(self.parent.seqSteps) if s.par.Step.eval() == self.parent._currStep), None)
			self.update_knob_leds_steps(index)
		elif self.parent.knobLedUpdateMode in [KnobLedUpdateMode.OFF]:
			self.update_knob_leds_gradual(0)
	
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
		#if self.parent.knobLedUpdateMode in [KnobLedUpdateMode.STEPS]:
		self.update_knob_leds_gradual(0)
		self.update_knob_leds_steps(index)
		if self.parent.knobLedUpdateMode not in [KnobLedUpdateMode.STEPS]:
			self.step_updated = True

	def set_bank_indicator(self, bank_idx: int):
		# VSN1
		if self.is_vsn1_enabled():
			self.grid_comm.SendLua(f'b={bank_idx};lcd:ldsw()')
		# UI
		self.ui_renderer.set_bank_indicator(bank_idx)
	
	# VSN1-specific methods that also update UI equivalents
	def update_all_slot_leds(self):
		"""Update all slot LEDs and UI equivalents"""
		# VSN1
		if self.is_vsn1_enabled():
			led_updates = []
			for slot_idx in range(len(VSN1Constants.SLOT_INDICES)):
				led_value = self.get_slot_state_value(slot_idx)
				led_updates.append((10 + slot_idx, led_value))
			self._send_batch_leds(led_updates)
		# UI
		self.ui_renderer.update_all_slot_indicators()
	
	def update_slot_leds(self, current_slot=None, previous_slot=None):
		"""Update specific slot LEDs and UI equivalents"""
		# VSN1
		if self.is_vsn1_enabled():
			led_updates = []
			if previous_slot is not None:
				prev_led_value = self.get_slot_state_value(previous_slot)
				led_updates.append((10 + previous_slot, prev_led_value))
			if current_slot is not None:
				curr_led_value = self.get_slot_state_value(current_slot)
				led_updates.append((10 + current_slot, curr_led_value))
			self._send_batch_leds(led_updates)
		# UI
		self.ui_renderer.update_slot_indicators(current_slot, previous_slot)
	
	def update_outline_color_index(self, color_index: int):
		"""Update outline color and UI equivalent"""
		# VSN1
		if self.is_vsn1_enabled():
			self.grid_comm.SendLua(f'rc={color_index};lcd:ldrr(3,3,317,237,10,c[rc])lcd:ldsw()')
		# UI
		self.ui_renderer.update_outline_color(color_index)
	
	def send_slot_led_feedback(self, slot_idx: int, value: int):
		"""Send slot feedback to both displays"""
		# VSN1
		if self.is_vsn1_enabled():
			led_updates = [(10 + slot_idx, value)]
			self._send_batch_leds(led_updates)
		# UI
		self.ui_renderer.send_slot_feedback(slot_idx, value)

	def set_stepmode_indicator(self, step_mode: StepMode):
		"""Set mode indicator in UI"""
		# VSN1
		if self.is_vsn1_enabled():
			if step_mode == StepMode.FIXED:
				self.grid_comm.SendLua(f'ci=2')
			else:
				self.grid_comm.SendLua(f'ci=3')
			self._render_vsn1_display(0.5, 0, 1, '_MODE_', '_FIXED_' if step_mode == StepMode.FIXED else '_ADAPT_')
		# UI
		self.ui_renderer.set_stepmode_indicator(step_mode)
	
	# ============================================================================
	# VSN1 Hardware Communication Methods (Private)
	# ============================================================================
	
	def _send_batch_leds(self, led_updates: list):
		"""Send multiple LED commands in a single Lua message"""
		if not self.is_vsn1_enabled() or not led_updates:
			return
		lua_commands = []
		for idx, value in led_updates:
			lua_commands.append(f'set_led({idx},1,{int(value)})')
		batch_lua = ';'.join(lua_commands)
		self.grid_comm.SendLua(batch_lua)
	
	def _render_vsn1_display(self, val, norm_min, norm_max, processed_label: str, bottom_text: str, step_indicator = None, norm_default = None, info = None, clamps = None):
		"""Render display data to VSN1 screen - ONLY the Lua output, no logic"""
		if not self.is_vsn1_enabled():
			return
		if info is None:
			# list current active parameters
			_slot_pars = self.parent.repo_manager.get_all_slots_for_bank(self.parent.currBank)
			_slot_pars = _slot_pars + [None] * (len(VSN1Constants.SLOT_INDICES) - len(_slot_pars))
			_labels = []
			for i, par in enumerate(_slot_pars):
				if par is not None:
					try:
						label = LabelFormatter.get_label_for_parameter(par, self.parent.labelDisplayMode, max_length=6)
						if self.parent.activeSlot is not None:
							_activePar = self.parent.repo_manager.get_slot_parameter(self.parent.activeSlot, self.parent.currBank)
							if _activePar is not None and _activePar.owner == par.owner and _activePar.name == par.name:
								label = '`'+label
					except:
						label = "---"
				else:
					label = "---"
				_labels.append(label)	
			info = _labels
		if norm_default is None:
			norm_default = -1
		if clamps is None:
			clamps = (0, 0)
		info_lua = '{' + ','.join(f"'{s}'" for s in info) + '}' if info else '{}'
		clamps_lua = '{'+f'{1 if clamps[0] else 0}, {1 if clamps[1] else 0}'+ '}'
		lua_code = f"update_param({val}, {norm_min}, {norm_max}, '{processed_label}', '{bottom_text}', {step_indicator}, {norm_default}, {info_lua}, {clamps_lua})"
		self.grid_comm.SendLua(lua_code, queue=True)
	
	def clear_all_slot_leds(self):
		"""Clear all slot LEDs (set to 0)"""
		if self.is_vsn1_enabled():
			led_updates = []
			for i in range(len(VSN1Constants.SLOT_INDICES)):
				led_updates.append((10 + i, 0))
			self._send_batch_leds(led_updates)
	
	def update_knob_leds_gradual(self, fill: float):
		"""Update knob LEDs with gradual fill"""
		if not self.is_vsn1_enabled():
			return
		fill = tdu.clamp(fill, 0, 1)
		try:
			self.parent.midiOut.sendControl(self.parent.evalChannel, VSN1Constants.ROTARY_LED_FEEDBACK_INDEX, fill)
			if f"Cannot communicate with the MIDI device" in self.parent.ownerComp.scriptErrors():
				self.parent.ownerComp.clearScriptErrors(error="*Cannot communicate with the MIDI device*")
			if f"Could not open the MIDI interface" in self.parent.ownerComp.scriptErrors():
				self.parent.ownerComp.clearScriptErrors()
				return
		except tdError as e:
			if "Cannot communicate with the MIDI device" in str(e):
				self.parent.ownerComp.addScriptError(f"Cannot communicate with the MIDI device")
				return
	
	def update_knob_leds_steps(self, step_indicator_idx: int):
		"""Update knob LEDs with steps"""
		if not self.is_vsn1_enabled():
			return
		led_updates = []
		for idx, led_idx in enumerate(VSN1Constants.KNOB_LED_IDXS):
			led_updates.append((led_idx, (step_indicator_idx == idx) * 255 * self.knob_led_dampen))
		self._send_batch_leds(led_updates)