from constants import VSN1Constants

class VSN1Manager:
	"""Manages VSN1 hardware integration - screen updates and LED feedback"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.grid_comm : IntechGridCommExt = self.parent.ownerComp.op('IntechGridComm').ext.IntechGridCommExt
	
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
		
	
	def _send_slot_led(self, slot_idx: int, value: int):
		"""Send LED command for a specific slot"""
		if not self.is_vsn1_enabled():
			return
		self.grid_comm.SendLua(f'set_led({10+slot_idx},1,{int(value)})')
	
	def send_slot_led_feedback(self, slot_index: int, value: int, prev_slot_index: int = None):
		"""Send LED feedback to VSN1 controller using slot indices (0-based)"""
		if not self.is_vsn1_enabled():
			return
		
		# Send LED command using slot index directly (0-based)
		self._send_slot_led(slot_index, value)
		
		# Turn off previous LED if specified
		if prev_slot_index is not None and prev_slot_index != slot_index:
			self._send_slot_led(prev_slot_index, 0)
	
	def update_all_slot_leds(self):
		"""Update all slot LEDs based on current state: 0=free, 30=occupied, 255=active (initialization only)"""
		if not self.is_vsn1_enabled():
			return
			
		# Update LEDs for all possible slots (used only during initialization)
		for slot_idx in range(len(VSN1Constants.SLOT_INDICES)):
			led_value = self.parent.display_manager.get_slot_state_value(slot_idx)
			self._send_slot_led(slot_idx, led_value)
	
	def update_slot_leds(self, current_slot: int = None, previous_slot: int = None):
		"""Update only current and previous slot LEDs for efficiency"""
		if not self.is_vsn1_enabled():
			return
		
		# Update previous slot LED (if specified)
		if previous_slot is not None:
			prev_led_value = self.parent.display_manager.get_slot_state_value(previous_slot)
			self._send_slot_led(previous_slot, prev_led_value)
		
		# Update current slot LED (if specified)
		if current_slot is not None:
			curr_led_value = self.parent.display_manager.get_slot_state_value(current_slot)
			self._send_slot_led(current_slot, curr_led_value)

	def update_outline_color_index(self, color_index: int):
		self.grid_comm.SendLua(f'rc={color_index};lcd:ldrr(3,3,317,237,10,c[rc])lcd:ldsw()')