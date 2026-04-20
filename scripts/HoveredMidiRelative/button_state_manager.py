"""Button state manager — hold/combo detection for note buttons.

All note messages arrive via onReceiveMidi. This manager tracks which
slot and step/bank buttons are currently held and fires the appropriate
action when a hold threshold is reached (checked per-frame in
onFrameStart) or when the button is released without being consumed by
a hold (tap).

Step buttons and bank buttons share the same physical MIDI indices.
The distinction is purely in the interaction:
  - Exclusive short tap  → step action
  - Exclusive long hold  → bank switch
  - Two-button combo     → reset / default / norm / clamp / mode / custom

The push button (encoder press) is handled immediately in onReceiveMidi
and does NOT go through this manager.
"""

from constants import MidiConstants


class ButtonStateManager:
	"""Tracks held note buttons and fires actions based on hold duration.

	Slot buttons:      tap → slot select,  hold → slot learn
	Step/bank buttons: exclusive tap → step,  combo tap → mode select,
	                   combo hold → reset/default/norm/clamp/custom,
	                   exclusive hold → bank switch
	"""

	# Bank button combo HOLD definitions:
	# (bank_block_pos_a, bank_block_pos_b) → (threshold_par, method, args)
	BANK_COMBOS = {
		(0, 1): ('Resetholdlength',      'onResetPar',   ()),
		(0, 2): ('Resetholdlength',   'onSetDefault', ()),
		(0, 3): ('Customizeholdlength',   'onCustomOpen', ()),
		(1, 2): ('Minmaxclampholdlength', 'onSetNorm',    ('min',)),
		(1, 3): ('Minmaxclampholdlength', 'onSetNorm',    ('max',)),
		(2, 3): ('Minmaxclampholdlength', 'onSetClamp',   ('both',)),
	}

	# Bank button combo TAP definitions (pressed together then released
	# before the hold threshold):
	# (bank_block_pos_a, bank_block_pos_b) → (method, args)
	BANK_COMBO_TAPS = {
		(0, 3): ('onReceiveModeSel', ()),
	}

	# Safety: auto-clear buttons held longer than this (e.g. missed Note Off)
	_STALE_THRESHOLD = 30.0
	# Double-push detection window (seconds)
	_DOUBLE_PUSH_WINDOW = 0.7

	def __init__(self, ext):
		self.ext = ext
		# midi_index → entry dict (see on_note_on for schema)
		self._held_notes: dict = {}
		# Bank-session tracking (reset when all step/bank buttons are released)
		self._bank_exclusive_valid: bool = True
		self._bank_combo_consumed: bool = False
		# Push button (encoder press) held state — tracked from MIDI notes
		# so we don't depend on a null CHOP.
		self._push_held: bool = False
		# Timestamp of the last push button release, for double-push detection.
		self._last_push_release: float = 0.0

	# ------------------------------------------------------------------
	# Categorisation
	# ------------------------------------------------------------------

	def _categorize_note(self, index: int):
		"""Categorise a MIDI note index.

		Returns a dict with at least ``category`` ('slot' or 'step_bank'),
		plus category-specific fields.  Returns None for unrecognised indices.

		Step and bank sequences may share the same MIDI indices, so a single
		button can match both.  Slot buttons are mutually exclusive.
		"""
		# Slot buttons (separate from step/bank)
		for block in self.ext.seqSlots:
			if tdu.match(block.par.Index.eval(), [index]):
				return {
					'category': 'slot',
					'slot_block_index': block.index,
				}

		# Step / bank buttons (may overlap in MIDI index)
		step_block = None
		for block in self.ext.seqSteps:
			if tdu.match(block.par.Index.eval(), [index]):
				step_block = block
				break

		bank_block_index = None
		for block in self.ext.seqBanks:
			if tdu.match(block.par.Index.eval(), [index]):
				bank_block_index = block.index
				break

		if step_block is not None or bank_block_index is not None:
			return {
				'category': 'step_bank',
				'step_block': step_block,
				'bank_block_index': bank_block_index,
			}

		return None

	# ------------------------------------------------------------------
	# Push button tracking
	# ------------------------------------------------------------------

	def update_push_state(self, pressed: bool):
		"""Update push button held state and detect double-push.

		Called from onReceiveMidi for every push-button note event.
		On press: check if the previous release was within the
		double-push window and fire onDoublePush if so.
		"""
		if pressed:
			now = absTime.seconds
			if (
				self._last_push_release > 0
				and now - self._last_push_release <= self._DOUBLE_PUSH_WINDOW
			):
				self._last_push_release = 0.0
				self._push_held = True
				self.ext.onDoublePush()
				return
			self._push_held = True
		else:
			self._push_held = False
			self._last_push_release = absTime.seconds

	# ------------------------------------------------------------------
	# Note On / Off
	# ------------------------------------------------------------------

	def on_note_on(self, index: int) -> bool:
		"""Track a button press. Returns True if the index is tracked."""
		cat = self._categorize_note(index)
		if cat is None:
			return False

		category = cat['category']

		# For step/bank buttons: mark all currently-held step/bank buttons
		# (and the new one) as non-exclusive, since a step only fires for
		# an exclusive (single-button) tap.
		exclusive = True
		if category == 'step_bank':
			for v in self._held_notes.values():
				if v['category'] == 'step_bank':
					exclusive = False
					v['exclusive'] = False
					break

		entry = {
			'start_time': absTime.seconds,
			'consumed': False,
			'exclusive': exclusive,
		}
		entry.update(cat)
		self._held_notes[index] = entry

		# Bank-session exclusivity (for the long exclusive-hold → bank switch)
		if category == 'step_bank' and cat.get('bank_block_index') is not None:
			held_banks = sum(
				1 for v in self._held_notes.values()
				if v.get('bank_block_index') is not None and not v['consumed']
			)
			if held_banks > 1:
				self._bank_exclusive_valid = False

		return True

	def on_note_off(self, index: int) -> bool:
		"""Handle button release.  Fires the appropriate tap action if the
		button was not consumed by a hold.  Returns True if the index was
		tracked."""
		info = self._held_notes.pop(index, None)
		if info is None:
			return False

		if not info['consumed']:
			category = info['category']

			if category == 'slot':
				# Tap on slot button → slot select
				self.ext.midi_handler.handle_slot_message(
					index, MidiConstants.MAX_VELOCITY
				)
				self.ext._cancel_hover_timeout()

			elif category == 'step_bank':
				tap_fired = False

				# 1) Check for a tap-combo with another held bank button.
				if info.get('bank_block_index') is not None:
					for _other_idx, other_info in self._held_notes.items():
						if (
							other_info.get('bank_block_index') is not None
							and not other_info['consumed']
						):
							pair = tuple(sorted([
								info['bank_block_index'],
								other_info['bank_block_index'],
							]))
							tap_def = self.BANK_COMBO_TAPS.get(pair)
							if tap_def is not None:
								other_info['consumed'] = True
								method_name, args = tap_def
								getattr(self.ext, method_name)(*args)
								tap_fired = True
								break

				# 2) Step fires only for an exclusive (single-button) tap.
				if (
					not tap_fired
					and info.get('exclusive')
					and info.get('step_block') is not None
				):
					# Delegate to the existing handler which checks
					# knobPushState and other guards.
					self.ext.midi_handler.handle_step_message(index, 0)
					if not self.ext._is_component_parameter():
						self.ext._start_hover_timeout(restart_if_sticky=True)

		# Reset bank-session tracking when no bank buttons remain held
		has_banks = any(
			v.get('bank_block_index') is not None
			for v in self._held_notes.values()
		)
		if not has_banks:
			self._bank_exclusive_valid = True
			self._bank_combo_consumed = False

		return True

	# ------------------------------------------------------------------
	# Per-frame check (called from onFrameStart)
	# ------------------------------------------------------------------

	def on_frame_start(self):
		"""Check held buttons against timing thresholds."""
		if not self._held_notes:
			return

		now = absTime.seconds
		ext = self.ext
		owner = ext.ownerComp

		# ── Stale cleanup ────────────────────────────────────────────
		stale = [
			idx for idx, info in self._held_notes.items()
			if now - info['start_time'] > self._STALE_THRESHOLD
		]
		for idx in stale:
			self._held_notes.pop(idx, None)
		if stale and not any(
			v.get('bank_block_index') is not None
			for v in self._held_notes.values()
		):
			self._bank_exclusive_valid = True
			self._bank_combo_consumed = False
		if not self._held_notes:
			return

		# ── Slot learn holds ─────────────────────────────────────────
		slot_threshold = owner.par.Slotlearnholdlength.eval()
		for index, info in list(self._held_notes.items()):
			if info['category'] == 'slot' and not info['consumed']:
				if now - info['start_time'] >= slot_threshold:
					info['consumed'] = True
					ext.onReceiveMidiSlotLearn(index)

		# ── Bank buttons (entries with bank_block_index) ─────────────
		held_banks = [
			(idx, info) for idx, info in self._held_notes.items()
			if info.get('bank_block_index') is not None and not info['consumed']
		]

		if len(held_banks) == 2 and not self._bank_combo_consumed:
			self._check_bank_combo(held_banks, now, owner, ext)
		elif (
			len(held_banks) == 1
			and self._bank_exclusive_valid
			and not self._bank_combo_consumed
		):
			self._check_bank_exclusive(held_banks[0], now, owner, ext)

	# ------------------------------------------------------------------
	# Bank helpers
	# ------------------------------------------------------------------

	def _check_bank_combo(self, held_banks, now, owner, ext):
		"""Check if two held bank buttons satisfy a combo threshold."""
		(_, info1), (_, info2) = held_banks
		pos1, pos2 = info1['bank_block_index'], info2['bank_block_index']
		combo = tuple(sorted([pos1, pos2]))
		combo_start = max(info1['start_time'], info2['start_time'])
		hold_time = now - combo_start

		combo_def = self.BANK_COMBOS.get(combo)
		if combo_def is None:
			return

		threshold_par, method_name, args = combo_def
		threshold = getattr(owner.par, threshold_par).eval()
		if hold_time >= threshold:
			info1['consumed'] = True
			info2['consumed'] = True
			self._bank_combo_consumed = True
			getattr(ext, method_name)(*args)

	def _check_bank_exclusive(self, held_bank, now, owner, ext):
		"""Check if a single exclusively-held bank button exceeds the switch threshold."""
		idx, info = held_bank
		hold_time = now - info['start_time']
		threshold = self._get_exclusive_bank_threshold(owner)
		if hold_time >= threshold:
			info['consumed'] = True
			ext.onReceiveMidiBankSel(idx)

	def _get_exclusive_bank_threshold(self, owner):
		"""Calculate the exclusive bank-switch hold threshold.

		Must be longer than all combo thresholds so combos resolve first.
		Formula mirrors the original node-engine expression:
		  max(max(0.01,
		          max(Customizeholdlength, Resetholdlength, Minmaxclampholdlength) + 0.01,
		          Bankswitchholdlength),
		      op('perform1')[0])
		"""
		combo_max = max(
			owner.par.Customizeholdlength.eval(),
			owner.par.Resetholdlength.eval(),
			owner.par.Minmaxclampholdlength.eval(),
		)
		inner = max(0.01, combo_max + 0.01, owner.par.Bankswitchholdlength.eval())
		try:
			perform_val = owner.op('perform1')[0].eval()
		except Exception:
			perform_val = 0
		return max(inner, perform_val)
