import json
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class HoveredMidiRelativeExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.hoveredPar = None
		self.persistPar = None
		self.activeMidi = self.ownerComp.op('midiin_active')
		self.resetMidi = self.ownerComp.op('midiin_reset')
		self.currStep = self.evalDefaultstepsize
		self.websocket : websocketDAT = self.ownerComp.op('websocket1')
		
	@property
	def seqSteps(self):
		return self.ownerComp.seq.Steps

	def onParClear(self):
		self.seqSteps.numBlocks = 1
		self.seqSteps[0].par.Index = ''
		# Set first block step to 1
		self.seqSteps[0].par.Step.val = 1.0
		self.parKnobindex.val = ''
		self.parParpersistindex.val = ''
		self.parResetparindex.val = ''

	@property
	def activePar(self):
		return self.persistPar or self.hoveredPar

	def onHoveredParChange(self, _op, _par, _expr, _bindExpr):
		self.hoveredPar = None

		if not self.evalActive:
			return
		if _op is None or _par is None:
			return
		if not (_op := op(_op)) and (_par := _par):
			return
		if (_par := getattr(_op.par, _par)) is None:
			return

		self.hoveredPar = _par
		
		pass

	def onReceiveMidi(self, dat, rowIndex, message, channel, index, value, input, byteData):
		if channel != self.evalChannel or not self.evalActive:
			return
		index = int(index)
		blocks = self._indexToBlock(index)

		if blocks:
			block = blocks[0]
			if block:
				if value == 127:
					self.currStep = block.par.Step.eval()
				elif not self.evalPersiststep and value == 0:
					self.currStep = self.evalDefaultstepsize
			return
		
		if int(index) == int(self.evalKnobindex):
			if message == 'Control Change':
				if self.activePar is None:
					return
				if self.activePar.owner != self.ownerComp:
					self._doStep(self.currStep, value)

		if int(index) == int(self.evalParpersistindex) and message == 'Note On':
				if self.hoveredPar is not None:
					self.persistPar = self.hoveredPar
				else:
					self.persistPar = None


	def onReceiveMidiLearn(self, dat, rowIndex, message, channel, index, value, input, byteData):
		if channel != self.evalChannel or not self.evalActive:
			return
		
		if self.hoveredPar in self.seqSteps.blockPars.Index:
			currentIdxPar = self.hoveredPar
			if currentIdxPar.eval() or currentIdxPar.mode not in [ParMode.CONSTANT, ParMode.BIND]:
				return
			currentIdxPar.val = index
			self._setStepPar(currentIdxPar.sequenceBlock)
		
		elif self.hoveredPar in [self.parKnobindex, self.parParpersistindex, self.parResetparindex]:
			currentPar = self.hoveredPar
			if currentPar.mode not in [ParMode.CONSTANT, ParMode.BIND]:
				return
			currentPar.val = index


	def onResetPar(self):
		if self.activePar is not None:
			self.activePar.reset()


# region par callbacks

	def onSeqStepsNIndex(self, _par, idx):
		self.activeMidi.cook(force=True)

	def onParKnobindex(self, _par, _val):
		self.activeMidi.cook(force=True)

	def onParParpersistindex(self, _par, _val):
		self.activeMidi.cook(force=True)

	def onParResetparindex(self, _par, _val):
		self.resetMidi.cook(force=True)

	def onParPeriststep(self, _par, _val):
		if not _val:
			self.currStep = self.evalDefaultstepsize
			
	def onParDefaultstepsize(self, _par, _val):
		if not self.evalPersiststep:
			self.currStep = _val

	def onParUsedefaultsforvsn1(self):
		# hardcoded stuff for the VSN1
		buttons_steps = {33: 1, 34: 0.1, 35: 0.01, 36: 0.001, 37: 0.0001, 38: 0.00001}
		self.seqSteps.numBlocks = 6
		for i, (button, step) in enumerate(buttons_steps.items()):
			self.seqSteps[i].par.Index.val = button
			self.seqSteps[i].par.Step.val = step

		knob_index = 41
		par_persist_index = 39
		reset_par_index = 40
		self.parKnobindex.val = knob_index
		self.parParpersistindex.val = par_persist_index
		self.parResetparindex.val = reset_par_index

		self.activeMidi.cook(force=True)
		self.resetMidi.cook(force=True)

# endregion par callbacks

	def _doStep(self, step, value):
		midValue = 128/2
		_par = self.activePar
		if not _par.isNumber:
			return
		if _par is not None and _par.mode in [ParMode.CONSTANT, ParMode.BIND]:
			_val = _par.eval()
			_step = step * (value - midValue)
			_newVal = _val + _step
			_par.val = _newVal
			if self.evalVsn1screensupport:
				self._updateScreenVals(_par, _par.eval())

	def _indexToBlock(self, index):
		# look for all indexes in all sequence blocks, returns a list always
		blocks = []
		for block in self.seqSteps:
			if tdu.match(block.par.Index.eval(), [index]):
				blocks.append(block)
		return blocks

	def _setStepPar(self, _block):
		block = _block
		parStep = block.par.Step
		blockIndex = block.index
		# Set step progression: first block gets 1, then each gets /10
		step_value = 1.0 / (10 ** blockIndex)
		if parStep.eval() == 0:
			parStep.val = step_value

# region screen stuff

	def _compressLabel(self, label, max_length):
		"""Always compress labels: sanitize, remove whitespace, remove vowels, then truncate"""
		# Step 0: Sanitize label for Lua safety
		label = self._sanitizeLabelForLua(label)
		
		# Step 1: Always remove whitespace
		compressed = label.replace(' ', '').replace('_', '')
		
		# Step 2: Always remove vowels (keep first character and consonants)
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

	def _updateScreenVals(self, _par, _val):
		screen_template = """--[[@cb]] if f>0 then f=f-1;local a,xo=gmaps({v1},{v2},{v3},0.1,1),#tostring({v1})/2*s/2-#tostring({v1})-s//32,lcd:ldaf(10,10,310,230,c[1])lcd:ldrr(xc-p//1-1,yc-p//1-1,xc+p//1+1,yc+p//1+1,s,c[2])lcd:ldrrf(xc-p*a//1,yc-p*a//1,xc+p*a//1,yc+p*a//1,s,c[3])lcd:ldft({v1},xc-xo,yc+s,s/2,c[2])local xn=(#ids*(s/2))/2-s//32;lcd:ldft("{text}",xc-xn,yc-1.5*s,s/2,c[2])lcd:ldsw()end"""
		
		# Truncate value to 4 characters max, convert to int if whole number
		if _val == int(_val):
			val_str = str(int(_val))
		else:
			val_str = str(_val)
		if len(val_str) > 4:
			val_str = val_str[:4]
		
		# Compress label to maximize meaningful content within 5 character limit
		label = self._compressLabel(_par.label, 5)
		
		
		# Optimize norm_min: convert to int if whole number, then truncate if needed
		norm_min = _par.normMin
		if norm_min == int(norm_min):
			norm_min = str(int(norm_min))
		else:
			norm_min = str(norm_min)
		if len(norm_min) > 3:
			norm_min = norm_min[:3]
			
		# Optimize norm_max: convert to int if whole number, then truncate if needed
		norm_max = _par.normMax
		if norm_max == int(norm_max):
			norm_max = str(int(norm_max))
		else:
			norm_max = str(norm_max)
		if len(norm_max) > 3:
			norm_max = norm_max[:3]
		
		lua_code = screen_template.format(v1=val_str, v2=norm_min, v3=norm_max, text=label)
		
		grid_websocket_package = {
			'type': 'execute-code',
			'script': lua_code
		}

		self.websocket.sendText(json.dumps(grid_websocket_package))

# endregion screen stuff
