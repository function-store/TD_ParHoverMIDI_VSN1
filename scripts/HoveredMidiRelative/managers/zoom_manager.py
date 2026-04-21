
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
		# Inertia state — zoom coasts to a stop after the knob stops moving
		self._velocity = 0.0  # Current zoom velocity (units/frame)
		self._decay = 0.75    # Per-frame decay factor (0 = instant stop, 1 = no decay)
		self._velocity_threshold = 0.0005  # Below this, snap to zero
		self._knob_this_frame = False  # True if handle_zoom_knob ran this frame
		self._last_zoom_pos = None  # Last position used for zoom (for inertia frames)
		self._mixed_direction = 0  # Last zoom direction for Mixed mode (1=in, -1=out)

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

	def capture_target_mixed(self, direction: int):
		"""Lock target like Target mode, but re-capture on direction change (Mixed mode).

		Stays locked while zooming in the same direction. The moment the
		user reverses (zoom-in ↔ zoom-out), the cursor position is
		re-captured as the new target point.
		"""
		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		if mouse_pos := _jumpExt.mousePosInEditor:
			if _jumpExt.currPane:
				# Re-capture if: first time, or direction reversed
				if not self.is_target_locked or direction != self._mixed_direction:
					self.target_pos = mouse_pos
					self.is_target_locked = True
					self._mixed_direction = direction

				self.start_pos = (_jumpExt.currPane.x, _jumpExt.currPane.y)
				self.start_timeout()

	def clear_target(self):
		"""Clear zoom target position and interpolation state"""
		self.target_pos = None
		self.start_pos = None
		self.is_target_locked = False
		self._velocity = 0.0
		self._last_zoom_pos = None
		self._mixed_direction = 0
		self.cancel_timeout()

	def cancel_timeout(self):
		"""Cancel any active zoom target timeout"""
		try:
			if self.timeout_run is not None and self.timeout_run.active:
				self.timeout_run.kill()
		except (AttributeError, tdError):
			pass

	def on_timeout(self):
		"""Called when zoom timeout expires - clear zoom target.
		Velocity is NOT cleared here so inertia can coast after timeout."""
		self.target_pos = None
		self.start_pos = None
		self.is_target_locked = False
		self._mixed_direction = 0

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

		interpolation_amount = self.parent.evalZoominterpolation
		if mode == 'Seek':
			# Seek mode: Simple linear interpolation
			t = interpolation_amount
		else:
			# Target / Mixed mode: Ease-out (decelerates as it approaches target)
			t = interpolation_amount * (2 - interpolation_amount)

		interpolated_x = start_x + (target_x - start_x) * t
		interpolated_y = start_y + (target_y - start_y) * t

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

		try:
			self.timeout_run = run(
				"args[0].on_timeout()",
				self, delayMilliSeconds=delay_ms, delayRef=op.TDResources
			)
		except Exception as e:
			print(f"Error starting zoom timeout: {e}")

	# ------------------------------------------------------------------
	# Inertia
	# ------------------------------------------------------------------

	def on_frame_start(self):
		"""Apply and decay zoom inertia each frame.
		Called from HoveredMidiRelativeExt.onFrameStart.

		On frames where handle_zoom_knob already applied the zoom,
		only decay the velocity — don't apply it again.
		"""
		if self._knob_this_frame:
			# Knob already applied zoom this frame — just decay for next frame
			self._knob_this_frame = False
			self._velocity *= self._decay
			return

		if abs(self._velocity) < self._velocity_threshold:
			self._velocity = 0.0
			return

		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		if not _jumpExt or not _jumpExt.currPane:
			self._velocity = 0.0
			return

		current_zoom = _jumpExt.currentZoom
		_zoom_limit = self.zoom_limit

		# Apply velocity (inertia coast)
		if current_zoom >= _zoom_limit and self._velocity > 0:
			new_zoom = current_zoom
		else:
			new_zoom = current_zoom + self._velocity
			if self._velocity > 0:
				new_zoom = min(new_zoom, _zoom_limit)

		# Zoom toward the same position the knob was using
		if self._last_zoom_pos:
			_jumpExt.setZoom(new_zoom, target_pos=self._last_zoom_pos)
		else:
			_jumpExt.setZoom(new_zoom, to_mouse=True)

		# Decay
		self._velocity *= self._decay

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

		_jumpExt = self.parent.jumpToOp.ext.JumpToOpExt
		if not _jumpExt or not _jumpExt.currPane:
			# No valid pane, clear state and don't process
			self.clear_target()
			return False

		current_zoom = _jumpExt.currentZoom
		direction = 1 if value > MidiConstants.MIDI_CENTER_VALUE else -1

		# Update target based on mode (after direction is known for Mixed)
		if zoom_mode == 'Target':
			self.capture_target_locked()
		elif zoom_mode == 'Mixed':
			self.capture_target_mixed(direction)
		else:
			self.update_target_seeking()

		zoom_delta = direction * self.parent.evalZoomnetwork * (3 if self.parent.knobPushState else 1)
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

		# Feed inertia — fraction of delta so the coast is gentle, not a replay
		self._velocity = zoom_delta * 0.4
		self._knob_this_frame = True

		# Use interpolated position (behavior depends on mode)
		interpolated_pos = self.get_interpolated_position(mode=zoom_mode)
		if interpolated_pos:
			self._last_zoom_pos = interpolated_pos
			_jumpExt.setZoom(new_zoom, target_pos=interpolated_pos)
		else:
			self._last_zoom_pos = None
			_jumpExt.setZoom(new_zoom, to_mouse=True)

		return True
