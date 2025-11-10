
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
		self.target_pos = None  # Target position (behavior depends on mode)
		self.start_pos = None  # Starting pane position for smooth interpolation
		self.is_target_locked = False  # Track if target is locked (for "Target" mode)
		self.timeout_seconds = 0.33 # Timeout in seconds if target is locked
		self.zoom_limit = 2.5
	
	def capture_target_locked(self):
		"""Capture and lock to initial mouse position (Target mode)"""
		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		if mouse_pos := _jumpExt.mousePosInEditor:
			if _jumpExt.currPane:
				if not self.is_target_locked:
					# First time: Lock target to initial mouse position
					self.target_pos = mouse_pos
					self.is_target_locked = True
				
				# Always update start position to current pane position (for smooth interpolation)
				self.start_pos = (_jumpExt.currPane.x, _jumpExt.currPane.y)
				
				# Restart timeout on every zoom action to keep target active
				self.start_timeout()
	
	def update_target_seeking(self):
		"""Update target to current mouse position (Seek mode - always following cursor)"""
		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		mouse_pos = _jumpExt.mousePosInEditor
		if mouse_pos and _jumpExt.currPane:
			# Always update target to current mouse position
			self.target_pos = mouse_pos
			# Store current pane position as start (for smooth interpolation to target)
			self.start_pos = (_jumpExt.currPane.x, _jumpExt.currPane.y)
			# Start/restart timeout
			self.start_timeout()
	
	def clear_target(self):
		"""Clear zoom target position and interpolation state"""
		self.target_pos = None
		self.start_pos = None
		self.is_target_locked = False
		self.cancel_timeout()
	
	def cancel_timeout(self):
		"""Cancel any active zoom target timeout"""
		try:
			if self.timeout_run is not None and self.timeout_run.active:
				self.timeout_run.kill()
		except (AttributeError, tdError):
			pass
	
	def on_timeout(self):
		"""Called when zoom timeout expires - clear zoom target"""
		self.target_pos = None
		self.start_pos = None
		self.is_target_locked = False
	
	def get_interpolated_position(self, mode: str = 'Seek'):
		"""Calculate interpolated position between current pane position and target
		
		Args:
			mode: 'Target' for locked position with ease-out, 'Seek' for continuous following
			
		Returns:
			Tuple of (x, y) interpolated position, or None if no target captured
		"""
		if self.target_pos is None or self.start_pos is None:
			return None
		
		start_x, start_y = self.start_pos
		target_x, target_y = self.target_pos
		
		if mode == 'Seek':
			# Seek mode: Simple linear interpolation
			# Creates smooth following movement without big jumps
			interpolation_amount = self.parent.evalZoominterpolation
			interpolated_x = start_x + (target_x - start_x) * interpolation_amount
			interpolated_y = start_y + (target_y - start_y) * interpolation_amount
		else:
			# Target mode: Linear interpolation
			# Once locked, smoothly moves to the initial capture point
			interpolation_amount = self.parent.evalZoominterpolation
			interpolated_x = start_x + (target_x - start_x) * interpolation_amount
			interpolated_y = start_y + (target_y - start_y) * interpolation_amount
		
		return (interpolated_x, interpolated_y)
	
	def start_timeout(self):
		"""Start timeout to clear captured zoom target
		
		Args:
			timeout_seconds: Duration in seconds before clearing zoom target (default: 0.1)
		"""
		# Cancel existing timeout
		self.cancel_timeout()
		
		# Start new timeout
		delay_ms = int(self.timeout_seconds * 1000)
		# debug(f'starting timeout for {delay_ms}ms')
		try:
			self.timeout_run = run(
				"args[0].on_timeout()", 
				self, delayMilliSeconds=delay_ms, delayRef=op.TDResources
			)
		except Exception as e:
			print(f"Error starting zoom timeout: {e}")
	
	def handle_zoom_knob(self, value: int) -> bool:
		"""Handle zoom knob MIDI message
		
		Args:
			value: MIDI value from knob
			
		Returns:
			True if zoom was handled, False otherwise
		"""
		# Check if zoom is disabled (0 or negative means disabled)
		if not self.parent.evalEnablezoom:
			# Clear any stuck state
			self.clear_target()
			return False
		
		from constants import MidiConstants
		
		# Get zoom mode from parent
		zoom_mode = getattr(self.parent, 'evalZoommode', 'Seek')
		
		# Update target based on mode
		if zoom_mode == 'Target':
			# Target mode: Lock to initial mouse position
			self.capture_target_locked()
		else:
			# Seek mode: Continuously follow cursor
			self.update_target_seeking()
		
		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		if not _jumpExt or not _jumpExt.currPane:
			# No valid pane, clear state and don't process
			self.clear_target()
			return False
		
		current_zoom = _jumpExt.currentZoom
		direction = 1 if value > MidiConstants.MIDI_CENTER_VALUE else -1
		zoom_delta = direction * self.parent.evalZoomnetwork * (5 if self.parent.knobPushState else 1)
		_zoom_limit = self.zoom_limit
		# Check if we've hit the zoom limit
		if current_zoom >= _zoom_limit and direction > 0:
			# At max zoom and trying to zoom in further - just adjust x/y position, don't change zoom
			new_zoom = current_zoom
		else:
			# Normal zoom behavior (can always zoom out, can zoom in up to 2.5)
			new_zoom = current_zoom + zoom_delta
			# Clamp to max zoom of zoom_limit when zooming in
			if direction > 0:
				new_zoom = min(new_zoom, _zoom_limit)
		
		# Use interpolated position (behavior depends on mode)
		interpolated_pos = self.get_interpolated_position(mode=zoom_mode)
		if interpolated_pos:
			_jumpExt.setZoom(new_zoom, target_pos=interpolated_pos)
		else:
			_jumpExt.setZoom(new_zoom, to_mouse=True)
		
		return True

