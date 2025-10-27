
'''Info Header Start
Name : vsn1_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.191.toe
Saveversion : 2023.12120
Info Header End'''
from constants import VSN1Constants, StepMode
from formatters import LabelFormatter
from constants import VSN1ColorIndex

class VSN1Manager:
	"""Manages VSN1 hardware integration - screen updates and LED feedback"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.grid_comm : IntechGridCommExt = self.parent.ownerComp.op('IntechGridComm').ext.IntechGridCommExt
		self.knob_led_dampen = 0.4
	
	def is_vsn1_enabled(self) -> bool:
		return self.parent.evalVsn1support
	
	def render_display(self, val, norm_min, norm_max, processed_label: str, bottom_text: str, percentage: float, step_indicator = None):
		"""Render display data to VSN1 screen - ONLY the Lua output, no logic"""
		if not self.is_vsn1_enabled():
			return
			
		# Simple Lua function call - ONLY difference from UI renderer
		lua_code = f"update_param({val}, {norm_min}, {norm_max}, '{processed_label}', '{bottom_text}', {step_indicator})"
		self.grid_comm.SendLua(lua_code, queue=True)
	
	def clear_screen(self):
		"""Clear the VSN1 screen"""
		lua_code = "--[[@cb]] lcd:ldaf(0,0,319,239,c[1])lcd:ldrr(3,3,317,237,10,c[2])lcd:ldsw()"
		self.grid_comm.SendLua(lua_code)
	
	def set_step_indicator(self, index: int):
		"""Set step indicator on VSN1 display"""
		# Handled by main render_display
		pass
		
	
	def _send_slot_led(self, slot_idx: int, value: int, is_knob: bool = False):
		"""Send LED command for a specific slot"""
		if not self.is_vsn1_enabled():
			return
		idx = slot_idx if is_knob else 10 + slot_idx
		self.grid_comm.SendLua(f'set_led({idx},1,{int(value)})')
	
	def _send_batch_leds(self, led_updates: list):
		"""Send multiple LED commands in a single Lua message"""
		if not self.is_vsn1_enabled() or not led_updates:
			return
		
		# Build batch Lua command#
		lua_commands = []
		for idx, value in led_updates:
			lua_commands.append(f'set_led({idx},1,{int(value)})')
		
		# Send as single Lua message
		batch_lua = ';'.join(lua_commands)
		self.grid_comm.SendLua(batch_lua)
	
	def send_slot_led_feedback(self, slot_index: int, value: int, prev_slot_index: int = None):
		"""Send LED feedback to VSN1 controller using slot indices (0-based)"""
		if not self.is_vsn1_enabled():
			return
		
		# Batch LED updates
		led_updates = []
		led_updates.append((10 + slot_index, value))  # Current slot
		
		if prev_slot_index is not None and prev_slot_index != slot_index:
			led_updates.append((10 + prev_slot_index, 0))  # Previous slot off
		
		self._send_batch_leds(led_updates)
	
	def update_all_slot_leds(self):
		"""Update all slot LEDs based on current state: 0=free, 30=occupied, 255=active (initialization only)"""
		if not self.is_vsn1_enabled():
			return
			
		# Batch all slot LED updates
		led_updates = []
		for slot_idx in range(len(VSN1Constants.SLOT_INDICES)):
			led_value = self.parent.display_manager.get_slot_state_value(slot_idx)
			led_updates.append((10 + slot_idx, led_value))
		
		self._send_batch_leds(led_updates)
	
	def update_slot_leds(self, current_slot: int = None, previous_slot: int = None):
		"""Update only current and previous slot LEDs for efficiency"""
		if not self.is_vsn1_enabled():
			return
		
		# Batch slot LED updates
		led_updates = []
		
		if previous_slot is not None:
			prev_led_value = self.parent.display_manager.get_slot_state_value(previous_slot)
			led_updates.append((10 + previous_slot, prev_led_value))
		
		if current_slot is not None:
			curr_led_value = self.parent.display_manager.get_slot_state_value(current_slot)
			led_updates.append((10 + current_slot, curr_led_value))
		
		self._send_batch_leds(led_updates)

	def update_outline_color_index(self, color_index: int, do_sw = True):
		self.grid_comm.SendLua(f'rc={color_index};lcd:ldrr(3,3,317,237,10,c[rc]){"lcd:ldsw()" if do_sw else ""}')

	def update_knob_leds_gradual(self, fill: float):
		"""Update knob LEDs with batch sending"""
		if not self.is_vsn1_enabled():
			return
		fill = tdu.clamp(fill, 0, 1)
		self.parent.midiOut.sendControl(self.parent.evalChannel, VSN1Constants.ROTARY_LED_FEEDBACK_INDEX, fill)

	def update_knob_leds_steps(self, step_indicator_idx: int):
		"""Update knob LEDs with steps"""
		if not self.is_vsn1_enabled():
			return
		
		# Batch all knob LED updates
		led_updates = []
		for idx, led_idx in enumerate(VSN1Constants.KNOB_LED_IDXS):
			led_updates.append((led_idx, (step_indicator_idx == idx) * 255 * self.knob_led_dampen))
			
		self._send_batch_leds(led_updates)

	def set_bank_indicator(self, bank_idx: int):
		"""Set bank indicator on VSN1 display"""
		if not self.is_vsn1_enabled():
			return
		# Send Lua command to update bank indicator on screen
		self.grid_comm.SendLua(f'b={bank_idx};lcd:ldsw()')

	def set_stepmode_indicator(self, step_mode: StepMode):
		if not self.is_vsn1_enabled():
			return
		if step_mode == StepMode.FIXED:
			self.grid_comm.SendLua(f'ci=2')
		else:
			self.grid_comm.SendLua(f'ci=3')
		self.render_display(0.5, 0, 1, '_MODE_', '_FIXED_' if step_mode == StepMode.FIXED else '_ADAPT_', 0.5)

	def clear_all_slot_leds(self):
		"""Clear all slot LEDs (set to 0)"""
		if not self.is_vsn1_enabled():
			return
		led_updates = []
		for i in range(len(VSN1Constants.SLOT_INDICES)):
			led_updates.append((10 + i, 0))
		self._send_batch_leds(led_updates)
	
	def show_info_message(self, _slot_pars):
		"""Display slot parameter info message on VSN1 screen in a 2x4 grid"""
		if not self.is_vsn1_enabled():
			return
		self.clear_screen()
		# Display labels in 2x4 grid
		# fill with none up to length of number of slots in VSN1Constants.SLOT_INDICES
		_slot_pars = _slot_pars + [None] * (len(VSN1Constants.SLOT_INDICES) - len(_slot_pars))
		for i, par in enumerate(_slot_pars):
			if par is not None:
				label = LabelFormatter.get_label_for_parameter(par, self.parent.labelDisplayMode, max_length=7)
			else:
				label = "  ---"	
			# Calculate grid position (2 rows, 4 columns)
			row = i // 4  # 0 or 1
			col = i % 4   # 0, 1, 2, or 3
			
			# Calculate x and y positions
			# Columns: 10, 90, 170, 250 (80px spacing)
			# Rows: 180, 210 (30px spacing)
			x = 10 + (col * 80)
			y = 180 + (row * 30)
			
			self.grid_comm.SendLua(f'dtx("{label}", {x}, {y}, 26, 2)')
		self.grid_comm.SendLua(f'doBank()')
		# Set outline color based on current state
		self.update_outline_color_index(VSN1ColorIndex.WHITE.value if self.parent.activeSlot is not None else VSN1ColorIndex.COLOR.value, do_sw=False)  # Active slot
		
		self.grid_comm.SendLua(f'lcd:ldsw()')
