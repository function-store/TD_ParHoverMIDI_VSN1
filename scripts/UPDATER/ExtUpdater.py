import TDFunctions as TDF

class ExtUpdater:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.update_button = op('/ui/dialogs/bookmark_bar/wiki/text')
		self.IsUpdatable = tdu.Dependency(False)
		self.newTag = None
		self.fetchedTag = None
		self._should_always_prompt = False
		self._called_from_check = False

	def Check(self, _):
		self._called_from_check = True
		try:
			self.CheckAndPrompt(None)
		except Exception:
			# Clear flag if CheckAndPrompt fails before async starts
			self._called_from_check = False
			raise

	def CheckSilent(self, _):
		if self.ownerComp.par.Enabled.eval():
			iop.TDAsyncIO.Run([self._doDaCheck()])

	def CheckAndPrompt(self, _):
		"""Variant of Check that always prompts the update dialog after checking"""
		if self.ownerComp.par.Enabled.eval():
			self._should_always_prompt = True
			iop.TDAsyncIO.Run([self._doDaCheck()])

	async def _doDaCheck(self):
		iop.GitHub.PollLatestTag()
	
	def OnPolledLatestTag(self, new_tag):
		try:
			self.newTag = new_tag
			_base = self.ownerComp.par.Target.eval()
			fetchedTag = _base.par.Version.eval()
			self.fetchedTag = fetchedTag
			if not (_base and fetchedTag):
				if self._should_always_prompt:
					self._prompt_after_check()
				return
			
			new_major = int(new_tag.split('.')[0])
			base_major = int(fetchedTag.split('.')[0])
			tag_flag = new_tag[-1]

			if new_major > base_major:
				self.IsUpdatable.val = False
			else:
				self.IsUpdatable.val = (fetchedTag != new_tag)
			
			# If we should always prompt, do it now
			if self._should_always_prompt:
				self._prompt_after_check()
		except Exception as e:
			# Clear flags if any error occurs before or during prompt
			self._should_always_prompt = False
			self._called_from_check = False
			raise
	
	def _prompt_after_check(self):
		"""Prompt update dialog after check completes"""
		try:
			_base = self.ownerComp.par.Target.eval()
			curr_version = _base.par.Version.eval() if _base else None
			updated_version = self.newTag if self.newTag else None
			is_already_latest = not self.IsUpdatable.val if curr_version and updated_version else True
			
			# If called from Check, show simple message box only if updatable
			if self._called_from_check:
				if self.IsUpdatable.val:
					_op = self.getGlobalOp()
					if _op:
						ui.messageBox(
							f'Update Available',
							f'An update is available for {_op.name}.\n\nPlease click the Update button to install.',
							buttons=['OK']
						)
				else:
					ui.messageBox(
						f'No Update Available',
						f'You are already on the latest version. You can force update anyway if you want to.',
						buttons=['OK']
					)
			else:
				# Normal full prompt dialog
				self.PromptUpdate(
					is_already_latest=is_already_latest,
					curr_version=curr_version or 'Unknown',
					updated_version=updated_version or 'Unknown'
				)
		except Exception as e:
			ui.messageBox(f'Error prompting update: {e}', 'Error', buttons=['OK'])
		finally:
			self._should_always_prompt = False
			self._called_from_check = False

	def getGlobalOp(self):
		globalOpShortcut = self.ownerComp.par.Globalopshortcut.eval()
		if not globalOpShortcut or not (_op := getattr(op, globalOpShortcut, None)):
			return False
		return _op

	def PromptUpdate(self, is_already_latest: bool = False, curr_version: str = None, updated_version: str = None):
		if not (_op := self.getGlobalOp()):
			raise Exception('Component needs to be a Global OP to update!')
		
		short_header = f'Update {_op.name}'
		message = f'Update available for {_op.name}\n\nCurrent version: {curr_version}\nUpdated version: {updated_version}' if not is_already_latest else f'You are already on the latest version of {_op.name}\n\nCurrent version: {curr_version}'
		confirm_message = f'Would you like to update to a newer version?' if not is_already_latest else f'Would you like to force update anyway?'
		ret = ui.messageBox(short_header, message+'\n'+confirm_message,buttons=['No','Yes'])
		if ret:
			self.Update(should_prompt=False)

	def Update(self, should_prompt: bool = True):
		if should_prompt:
			self.CheckAndPrompt(None)
		else:
			iop.Downloader.par.Download.pulse()

	
	def OnFileDownloaded(self, callbackInfo):
		if not (_globalOp := self.getGlobalOp()):
			return
			
		comp_path = callbackInfo['compPath']
		newComp = op(comp_path)
		fp = tdu.FileInfo(str(callbackInfo['path']))
		if newComp:
			# Store docked operators information before replacement
			oldComp = _globalOp
			docked_ops = []
			for docked_op in oldComp.docked:
				docked_info = {
					'op': docked_op,
					'pos': (docked_op.nodeX, docked_op.nodeY),
				}
				docked_ops.append(docked_info)
				# Undock the operator before replacement
				docked_op.dock = None

			newComp.par.externaltox.mode = ParMode.EXPRESSION
			newComp.par.externaltox.expr = f"f'{{app.userPaletteFolder}}/FNStools_ext/{fp.baseName}'"
			newComp.par.Version = self.newTag
			newComp.par.savebackup = True
			for _par in _globalOp.customPars:
				if newComp.par[_par.name] is None:
					continue
				if _par.name == 'Version':
					continue
				if _par.page.name in ['Version Ctrl']:
					continue

				# restore mode and expressions and values
				newComp.par[_par.name].expr = _par.expr
				newComp.par[_par.name].bindExpr = _par.bindExpr
				newComp.par[_par.name].val = _par.val
				newComp.par[_par.name].mode = _par.mode

			newComp.store('post_update', True)


			TDF.replaceOp(_globalOp, newComp)
			newComp.destroy()

			# Restore docked operators
			newComp = _globalOp
			for dock_info in docked_ops:
				docked_op = dock_info['op']
				if docked_op:
					# Restore position first
					docked_op.nodeX, docked_op.nodeY = dock_info['pos']
					# Then re-dock
					docked_op.dock = newComp

