import TDFunctions as TDF

class ExtUpdater:
	def __init__(self, ownerComp):
		self.ownerComp = ownerComp
		self.update_button = op('/ui/dialogs/bookmark_bar/wiki/text')
		self.IsUpdatable = tdu.Dependency(False)
		self.newTag = None

	def Check(self, _):
		if self.ownerComp.par.Enabled.eval():
			iop.TDAsyncIO.Run([self._doDaCheck()])


	async def _doDaCheck(self):
		iop.GitHub.PollLatestTag()
	
	def OnPolledLatestTag(self, new_tag):
		self.newTag = new_tag
		_base = self.ownerComp.par.Target.eval()
		fetchedTag = _base.par.Version.eval()
		if not (_base and fetchedTag):
			return
		
		new_major = int(new_tag.split('.')[0])
		base_major = int(fetchedTag.split('.')[0])
		tag_flag = new_tag[-1]

		if new_major > base_major and not tag_flag != 'f':
			self.IsUpdatable.val = False
		else:
			self.IsUpdatable.val = (fetchedTag != new_tag)

	def getGlobalOp(self):
		globalOpShortcut = self.ownerComp.par.Globalopshortcut.eval()
		if not globalOpShortcut or not (_op := getattr(op, globalOpShortcut, None)):
			return False
		return _op

	def PromptUpdate(self):
		if not (_op := self.getGlobalOp()):
			return
		ret = ui.messageBox(f'Update available for {_op.name}', 'Would you like to update to a newer version?',buttons=['No','Yes'])
		if ret:
			self.Update('dummy')
		else:
			self.update_button.parent().op('docsHelper').OpenDocs()

	def Update(self, _):
		#op.FNS_CONFIG.SaveAllToJSON()			
		if not self.getGlobalOp():
			return
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

