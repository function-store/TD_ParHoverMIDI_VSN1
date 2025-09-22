import json
from TDStoreTools import StorageManager
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class HoveredMidiRelativeExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		
		self.activeMidi = self.ownerComp.op('midiin_active')
		self.resetMidi = self.ownerComp.op('midiin_reset')
		self.slotsLearnMidi = self.ownerComp.op('midiin_slots')
		
		self.websocket : websocketDAT = self.ownerComp.op('websocket1')
		
		self.hoveredPar = None
		self.activeSlot = None

		self.currStep = self.evalDefaultstepsize

		storedItems = [
			{
				'name': 'slotPars',
				'default': [],
				'readOnly': False,
				'property': True,
				'dependable': False
			}
		]

		self.stored = StorageManager(self, ownerComp, storedItems)

		if self.evalVsn1screensupport:
			self._clearScreen()
			self._updateScreenAll(0,0,1,'HOVERINIT', force=True)
		
# region properties

	@property
	def seqSteps(self):
		return self.ownerComp.seq.Steps

	@property
	def seqSlots(self):
		return self.ownerComp.seq.Slots

	@property
	def activePar(self):
		# prioritize active slot pars over hovered par
		if self.activeSlot is not None and self.activeSlot < len(self.slotPars):
			if self.slotPars[self.activeSlot] is not None:
				return self.slotPars[self.activeSlot]
		if self.hoveredPar is not None:
			return self.hoveredPar
		return None


	def onHoveredParChange(self, _op, _par, _expr, _bindExpr):
		self.hoveredPar = None

		if not self.evalActive:
			return
		if _op is None or _par is None:
			return
		if not (_op := op(_op)):
			return
		if (_par := getattr(_op.par, _par)) is None:
			return

		self.hoveredPar = _par

		if self.evalVsn1screensupport:
			if self.activeSlot is not None:
				self._updateScreenPar(_par)
		
		pass

# endregion properties

# region midi callbacks

	def onReceiveMidi(self, dat, rowIndex, message, channel, index, value, input, byteData):		
		if channel != self.evalChannel or not self.evalActive:
			return
		
		_activePar = self.activePar
		_hoveredPar = self.hoveredPar
		index = int(index)

		# check if it belongs to a sequence step
		if message == 'Note On' and (blocks := self.__indexToBlocks(index, self.seqSteps)):
			block = blocks[0]
			if block:
				if value == 127:
					self.currStep = block.par.Step.eval()
				elif not self.evalPersiststep and value == 0:
					self.currStep = self.evalDefaultstepsize
		
		if int(index) == int(self.evalKnobindex):
			if _activePar is not None:
				if message == 'Control Change':
					if _activePar.owner != self.ownerComp:
						self._doStep(self.currStep, value)

		if index == int(self.evalPulseindex):
			if message == 'Note On' and value == 127:
				if _activePar is not None:
					if _activePar.owner != self.ownerComp and _activePar.isPulse:
						_activePar.pulse()

			# TODO: make this an option? pulse with knob instead of button?
			# if message == 'Control Change':
			# 	if value - 128/2 > 0:
			# 		if _activePar.owner != self.ownerComp and _activePar.isPulse:
			# 			_activePar.pulse()

		if message == 'Note On' and value == 127 and (blocks := self.__indexToBlocks(index, self.seqSlots)):
			block = blocks[0]
			if block:
				_blockIdx = block.index
				if _blockIdx < len(self.slotPars):
					self.activeSlot = _blockIdx
					self._updateScreenPar(self.slotPars[self.activeSlot])
				else:
					self.activeSlot = None
					self._updateScreenAll(0,0,1,'_HOVER_', force=True)


	def onReceiveMidiLearn(self, dat, rowIndex, message, channel, index, value, input, byteData):
		if channel != self.evalChannel or not self.evalActive:
			return

		_hoveredPar = self.hoveredPar
		if _hoveredPar is None or _hoveredPar.mode not in [ParMode.CONSTANT, ParMode.BIND] or _hoveredPar.eval():
			return
		
		# Control Change: knob only
		if message == 'Control Change' and _hoveredPar == self.parKnobindex:
			_hoveredPar.val = index

		# Note On: buttons and steps
		elif message == 'Note On':
			if _hoveredPar in [self.parPulseindex, self.parResetparindex]:
				_hoveredPar.val = index
			if _hoveredPar in self.seqSteps.blockPars.Index:
				_hoveredPar.val = index
				self._setStepPar(_hoveredPar.sequenceBlock)
			elif _hoveredPar in self.seqSlots.blockPars.Index:
				_hoveredPar.val = index


	def onReceiveMidiSlotLearn(self, index):
		_hoveredPar = self.hoveredPar

		if (blocks := self.__indexToBlocks(index, self.seqSlots)):
			block = blocks[0]
			if block:
				_blockIdx = block.index
				if _hoveredPar is not None and _hoveredPar.mode in [ParMode.CONSTANT, ParMode.BIND]:
					# Extend list if necessary to accommodate the index
					while len(self.slotPars) <= _blockIdx:
						self.slotPars.append(None)
					# Set the parameter at the correct index
					self.slotPars[_blockIdx] = _hoveredPar
					self._updateScreenAll(0,0,1,'_LEARNED_', force=True)
				else:
					self.activeSlot = None
					self._updateScreenAll(0,0,1,'_HOVER_', force=True)

	def onResetPar(self):
		if self.activePar is not None:
			self.activePar.reset()

# endregion midi callbacks

# region helper functions

	def _doStep(self, step, value):
		midValue = 128/2
		_par = self.activePar
		if _par is None or _par.mode not in [ParMode.CONSTANT, ParMode.BIND]:
			return
			
		_diff = value - midValue
		_step = step * (_diff)
		
		if _par.isNumber:
			# Handle numeric parameters (float/int)
			_val = _par.eval()
			_newVal = _val + _step
			_par.val = _newVal
		elif _par.isMenu:
			# Handle menu parameters - step through menu options
			if abs(_diff) >= 1:  # Only change on significant step
				current_index = _par.menuIndex
				step_direction = 1 if _step > 0 else -1
				new_index = current_index + step_direction
				_par.menuIndex = new_index
		elif _par.isToggle:
			# Handle toggle parameters - step through on/off states
			current_val = _par.eval()
			if _step > 0 and not current_val:
				_par.val = True  # Turn on if stepping positive and currently off
			elif _step < 0 and current_val:
				_par.val = False  # Turn off if stepping negative and currently on
		else:
			# Unsupported parameter type
			return
			
		if self.evalVsn1screensupport:
			# For menu/toggle, show current selection/state as the "value"
			self._updateScreenPar(_par)

	def _setStepPar(self, _block):
		block = _block
		parStep = block.par.Step
		blockIndex = block.index
		# Set step progression: first block gets 1, then each gets /10
		step_value = 1.0 / (10 ** blockIndex)
		if parStep.eval() == 0:
			parStep.val = step_value

			
	def __indexToBlocks(self, index, in_seq):
		# look for all indexes in all sequence blocks, returns a list always
		blocks = []
		for block in in_seq:
			if tdu.match(block.par.Index.eval(), [index]):
				blocks.append(block)
		return blocks

# endregion helper functions
# region par callbacks

	def onParClear(self):
		self.seqSteps.numBlocks = 1
		self.seqSteps[0].par.Index = ''
		self.seqSteps[0].par.Step.val = 1.0
		self.seqSlots.numBlocks = 1
		self.seqSlots[0].par.Index = ''
		self.parKnobindex.val = ''
		self.parResetparindex.val = ''
		self.parPulseindex.val = ''
		self.activeMidi.cook(force=True)
		self.resetMidi.cook(force=True)
		self.slotsLearnMidi.cook(force=True)

	#TODO: these can be optimized if using Dependency objects
	def onSeqStepsNIndex(self, _par, idx):
		self.activeMidi.cook(force=True)

	def onSeqSlotsNIndex(self, _par, idx):
		self.activeMidi.cook(force=True)
		self.slotsLearnMidi.cook(force=True)

	def onParKnobindex(self, _par, _val):
		self.activeMidi.cook(force=True)

	def onParResetparindex(self, _par, _val):
		self.resetMidi.cook(force=True)
	# end TODO

	def onParPeriststep(self, _par, _val):
		if not _val:
			self.currStep = self.evalDefaultstepsize
			
	def onParDefaultstepsize(self, _par, _val):
		if not self.evalPersiststep:
			self.currStep = _val

	def onParUsedefaultsforvsn1(self):
		# hardcoded stuff for the VSN1
		buttons_steps = {42: 1, 43: 0.1, 44: 0.01, 45: 0.001}
		self.seqSteps.numBlocks = len(buttons_steps)
		for i, (button, step) in enumerate(buttons_steps.items()):
			self.seqSteps[i].par.Index.val = button
			self.seqSteps[i].par.Step.val = step

		slot_indices = [33, 34, 35, 36, 37, 38, 39, 40]
		self.seqSlots.numBlocks = len(slot_indices)
		for i, index in enumerate(slot_indices):
			self.seqSlots[i].par.Index.val = index

		knob_index = 41
		reset_par_index = 41
		pulse_index = 41

		self.parKnobindex.val = knob_index
		self.parResetparindex.val = reset_par_index
		self.parPulseindex.val = pulse_index

		self.activeMidi.cook(force=True)
		self.resetMidi.cook(force=True)
		self.slotsLearnMidi.cook(force=True)

# endregion par callbacks

# region screen stuff

	def _compressLabel(self, label, max_length = 9):
		"""Compress labels only if longer than max_length"""
		# Step 0: Sanitize label for Lua safety
		label = self._sanitizeLabelForLua(label)
		
		# If label is already short enough, return as is
		if len(label) <= max_length:
			return label
		
		# Step 1: Remove whitespace
		compressed = label.replace(' ', '').replace('_', '')
		
		# Step 2: Remove vowels (keep first character and consonants)
		vowels = 'aeiouAEIOU'
		if len(compressed) > 1:
			# Keep first character, remove vowels from rest
			compressed = compressed[0] + ''.join(c for c in compressed[1:] if c not in vowels)
		
		# Step 3: Final truncation to max_length
		return compressed[:max_length]
	
	def _sanitizeLabelForLua(self, label):
		"""Remove or replace characters that could break Lua string syntax"""
		if not label:
			return 'Param'  # Default fallback
		
		# Remove/replace problematic characters
		sanitized = label.replace('"', '').replace("'", '').replace('\\', '').replace('\n', '').replace('\r', '')
		
		# Ensure we have something left
		if not sanitized:
			return 'Param'
		
		return sanitized

	def _updateScreenAll(self, val, norm_min, norm_max, label, display_text=None, force=False):
		if not self.evalVsn1screensupport:
			return

		# Process label based on compression setting
		if self.evalUsecompressedlabels and not force:
			processed_label = self._compressLabel(label)
		else:
			processed_label = label[:9]
		
		# Format numeric values: round if number, truncate all to 9 chars max
		def format_value(v):
			if isinstance(v, (int, float)):
				v = round(v, 6)
			return str(v)[:9]
		
		val_formatted = format_value(val)
		min_formatted = format_value(norm_min)
		max_formatted = format_value(norm_max)
		
		# Use display_text if provided, otherwise format the value
		display_str = display_text if display_text is not None else str(val_formatted)
		lua_code = f"update_param({val_formatted}, {min_formatted}, {max_formatted}, '{processed_label}', '{display_str}')"
		
		grid_websocket_package = {
			'type': 'execute-code',
			'script': lua_code
		}
		self.websocket.sendText(json.dumps(grid_websocket_package))

	def _updateScreenPar(self, _par):
		if not self.evalVsn1screensupport:
			return

		if _par.isMenu:
			_val = _par.menuIndex  # Numeric index for mapping
			_min, _max = 0, len(_par.menuNames) - 1
			display_text = str(_par.menuLabels[_par.menuIndex])  # Actual menu option label
			if self.evalUsecompressedlabels:
				display_text = self._compressLabel(display_text)
		elif _par.isToggle:
			_val = 1 if _par.eval() else 0
			_min, _max = 0, 1
			display_text = "On" if _val else "Off"
		else:
			_val = _par.eval()  # Numeric value
			_min, _max = _par.normMin, _par.normMax
			display_text = None  # Use default formatting
		
		self._updateScreenAll(_val, _min, _max, _par.label, display_text)

	def _clearScreen(self):
		lua_code = "--[[@cb]] lcd:ldaf(0,0,319,239,c[1])lcd:ldrr(3,3,317,237,10,c[2])"
		
		grid_websocket_package = {
			'type': 'execute-code',
			'script': lua_code
		}
		self.websocket.sendText(json.dumps(grid_websocket_package))

# endregion screen stuff
