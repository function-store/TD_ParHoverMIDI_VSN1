

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class ExtTDUIMod:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.master = parent.HoveredMidiRelative
		colorTable = self.master.op('null_page_cols')
		self.PageCols = []
		for _row in colorTable.rows():
			_cols = (float(_cell.val) for _cell in _row)
			self.PageCols.append(list(_cols))
		self.containers = [self.ownerComp.op('select_parhover_button')]
		self.updater = self.ownerComp.parent.HoveredMidiRelative.op("UPDATER")

	@property
	def current_color_index(self):
		return (self.master.par.Colorindex.eval()-1) % 4

	def Install(self):
		targets = [op('/ui/dialogs/mainmenu')]
		#
		containers = self.containers
		containers = sorted(containers, key=lambda x: x.nodeX)
		for target in targets:
			for i, cont in enumerate(containers):
				if _op := target.op(cont.name):
					_op.destroy()
				newOP = target.copy(cont)
				newOP.nodeX = 500 + i*200
				newOP.nodeY = -400
				try:
					newOP.inputCOMPConnectors[0].connect(target.op('emptypanel').outputCOMPConnectors[0])
				except:
					pass
				newOP.allowCooking = True
				
		ui.status = 'Function Store - Navbar installed'
		pass

	def onParInstall():
		self.Install()

	def onButtonClick(self, panelValue):
		name = panelValue.name
		if name == 'lselect':
			op.VSN1_HOVER.openParameters()
		elif name == 'rselect':
			op.VNS1_HOVER.par.Enableui = True
			self.ownerComp.op('window1').par.winopen.pulse()
		elif name == 'mselect':
			op.VSN1_HOVER.par.Colorhoveredui.val = not op.VSN1_HOVER.par.Colorhoveredui.eval()

