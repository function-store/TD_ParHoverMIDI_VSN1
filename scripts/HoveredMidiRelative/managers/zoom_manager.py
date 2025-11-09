
'''Info Header Start
Name : zoom_manager
Author : Dan@DAN-4090
Saveversion : 2023.12120
Info Header End'''

class ZoomManager:
	"""Manager for network editor zoom and navigation functionality"""
	
	def __init__(self, parent_ext):
		self.parent = parent_ext
		self.timeout_run = None  # Run object for zoom target timeout
		self.target_pos = None  # Captured (x, y) position for zoom target
		self.start_pos = None  # Starting pane position for smooth interpolation
		self.interpolation_progress = 0.0  # Progress of zoom position interpolation (0.0 to 1.0)
	
	def capture_target(self):
		"""Capture current mouse position as zoom target if not already captured"""
		if self.target_pos is None:
			_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
			mouse_pos = _jumpExt.mousePosInEditor
			if mouse_pos and _jumpExt.currPane:
				# Capture target position (where we want to zoom to)
				self.target_pos = mouse_pos
				# Capture starting position (current pane position)
				self.start_pos = (_jumpExt.currPane.x, _jumpExt.currPane.y)
				# Reset interpolation progress
				self.interpolation_progress = 0.0
				# Start timeout to clear captured position
				self.start_timeout()
	
	def clear_target(self):
		"""Clear captured zoom target position and interpolation state"""
		self.target_pos = None
		self.start_pos = None
		self.interpolation_progress = 0.0
		self.cancel_timeout()
	
	def cancel_timeout(self):
		"""Cancel any active zoom target timeout"""
		try:
			if self.timeout_run is not None and self.timeout_run.active:
				self.timeout_run.kill()
		except (AttributeError, tdError):
			pass
	
	def on_timeout(self):
		"""Called when zoom timeout expires - clear captured zoom target"""
		self.target_pos = None
		self.start_pos = None
		self.interpolation_progress = 0.0
	
	def get_interpolated_position(self, interpolation_speed: float = 0.015):
		"""Calculate interpolated position between start and target
		
		Args:
			interpolation_speed: How fast to move towards target (0.0 to 1.0). Higher = faster.
			
		Returns:
			Tuple of (x, y) interpolated position, or None if no target captured
		"""
		if self.target_pos is None or self.start_pos is None:
			return None
		
		# Increase interpolation progress (smoothly approach 1.0)
		self.interpolation_progress = min(1.0, self.interpolation_progress + interpolation_speed)
		
		# Apply ease-out cubic for smooth deceleration
		# This makes the movement start fast and slow down as it approaches the target
		t = self.interpolation_progress
		eased_t = 1 - pow(1 - t, 3)
		
		# Interpolate between start and target positions
		start_x, start_y = self.start_pos
		target_x, target_y = self.target_pos
		
		interpolated_x = start_x + (target_x - start_x) * eased_t
		interpolated_y = start_y + (target_y - start_y) * eased_t
		
		return (interpolated_x, interpolated_y)
	
	def start_timeout(self, timeout_seconds: float = 0.1):
		"""Start timeout to clear captured zoom target
		
		Args:
			timeout_seconds: Duration in seconds before clearing zoom target (default: 0.1)
		"""
		# Cancel existing timeout
		self.cancel_timeout()
		
		# Start new timeout
		delay_ms = int(timeout_seconds * 1000)
		self.timeout_run = run(
			"args[0].on_timeout()", 
			self, delayMilliSeconds=delay_ms, delayRef=op.TDResources
		)
	
	def handle_zoom_knob(self, value: int) -> bool:
		"""Handle zoom knob MIDI message
		
		Args:
			value: MIDI value from knob
			
		Returns:
			True if zoom was handled, False otherwise
		"""
		if self.parent.evalZoomnetwork <= 0:
			return False
		
		from constants import MidiConstants
		
		# Capture zoom target position on first zoom action
		self.capture_target()
		
		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		direction = 1 if value > MidiConstants.MIDI_CENTER_VALUE else -1
		new_zoom = _jumpExt.currentZoom + (direction * self.parent.evalZoomnetwork * (10 if self.parent.knobPushState else 1))
		
		# Use interpolated position if target is captured
		interpolated_pos = self.get_interpolated_position()
		if interpolated_pos:
			_jumpExt.setZoom(new_zoom, target_pos=interpolated_pos)
			# Restart timeout to keep target locked while actively zooming
			self.start_timeout()
		else:
			_jumpExt.setZoom(new_zoom, to_mouse=True)
		
		return True

