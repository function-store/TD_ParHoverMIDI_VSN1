'''Info Header Start
Name : vsn1_manager
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.191.toe
Saveversion : 2023.12120
Info Header End'''
from constants import VSN1Constants

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

		self.grid_comm.SendLua(lua_code)
	
	def clear_screen(self):
		"""Clear the VSN1 screen"""
		lua_code = "--[[@cb]] lcd:ldaf(0,0,319,239,c[1])lcd:ldrr(3,3,317,237,10,c[2])"
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
		
		# Build batch Lua command
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

	def update_outline_color_index(self, color_index: int):
		self.grid_comm.SendLua(f'rc={color_index};lcd:ldrr(3,3,317,237,10,c[rc])lcd:ldsw()')

	def update_knob_leds_gradual(self, fill: float):
		"""Update knob LEDs with batch sending"""
		if not self.is_vsn1_enabled():
			return
			
		# Batch all knob LED updates
		led_updates = []
		total_fill = fill * 255 * len(VSN1Constants.KNOB_LED_IDXS)
		for idx, led_idx in enumerate(VSN1Constants.KNOB_LED_IDXS):
			this_fill = 255 if total_fill >= 255 else int(total_fill % 255)
			led_updates.append((led_idx, this_fill * self.knob_led_dampen))
			total_fill -= this_fill
		
		self._send_batch_leds(led_updates)

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