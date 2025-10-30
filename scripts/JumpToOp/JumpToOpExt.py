

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class JumpToOpExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		
	@property
	def currPane(self) -> NetworkEditor | None:
		pane = ui.panes.current
		return pane if isinstance(pane, NetworkEditor) else None

	@property
	def currZoom(self) -> float:
		if currPane := self.currPane:
			if self.evalUsecurrentzoom:
				return currPane.zoom
			else:
				return self.ownerComp.par.Zoom.eval()
		return 1.0

	def setZoom(self, currPane: NetworkEditor, zoom: float):
		if currPane := self.currPane:
			currPane.zoom = zoom

	@property
	def toOp(self) -> OP:
		return self.ownerComp.par.Toop.eval()

	def onParJump(self):
		if currPane := self.currPane:
			self.toOp.current = True
			currPane.home(op=self.toOp)
			zoom = self.currZoom
			run(lambda: self.setZoom(currPane, zoom), delayFrames=1)

	def Jump(self, to_op: OP = None):
		if currPane := self.currPane:
			to_op = to_op if to_op is not None else self.toOp.eval()
			if to_op is None: return
			currPane.owner = to_op.parent()
			to_op.current = True
			to_zoom = True
			if self.evalUsecurrentzoom:
				to_zoom = False
			currPane.home(zoom=to_zoom,op=to_op)
			if not to_zoom:
				zoom = self.currZoom
				run(lambda: self.setZoom(currPane, zoom), delayFrames=1)




