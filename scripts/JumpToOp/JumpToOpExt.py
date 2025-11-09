

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

class JumpToOpExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.mousePosExt : TLMouseExt = self.ownerComp.op('MOUSE_POS_IN_NETWORKEDITOR').ext.TLMouseExt
		
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

	@property
	def currentZoom(self) -> float:
		if currPane := self.currPane:
			return currPane.zoom
		return 0

	@property
	def mousePosInEditor(self) -> (float, float):
		if currPane := self.currPane:
			_chop = self.ownerComp.op('MOUSE_POS_IN_NETWORKEDITOR/xy')
			if _chop:
				self.mousePosExt.UpdateMousePosition()
				return _chop['x'].eval(), _chop['y'].eval()
		return None


	def setZoom(self, zoom: float, to_mouse : bool = False, target_pos: tuple = None):
		"""Set zoom level and optionally center on a position
		
		Args:
			zoom: Target zoom level
			to_mouse: If True, center on current mouse position (ignored if target_pos is provided)
			target_pos: Optional (x, y) tuple to center on. If provided, overrides to_mouse.
		"""
		if currPane := self.currPane:
			currPane.zoom = zoom
			if target_pos:
				# Use provided target position
				_x, _y = target_pos
				currPane.x = _x
				currPane.y = _y
			elif to_mouse:
				# Use current mouse position
				_mousePos = self.mousePosInEditor
				if _mousePos:
					_x, _y = _mousePos
					currPane.x = _x
					currPane.y = _y

	@property
	def toOp(self) -> OP:
		return self.ownerComp.par.Toop.eval()

	def onParJump(self):
		if currPane := self.currPane:
			self.toOp.current = True
			currPane.home(op=self.toOp)
			zoom = self.currZoom
			run(lambda: self.setZoom(zoom), delayFrames=1)

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
				run(lambda: self.setZoom(zoom), delayFrames=1)




