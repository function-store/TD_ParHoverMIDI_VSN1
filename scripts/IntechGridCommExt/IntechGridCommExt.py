
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###
import json
class IntechGridCommExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.websocket: websocketDAT = self.ownerComp.op('websocket1')
		self.reconnectTimer: timerDAT = self.ownerComp.op('timer1')
		self.callbackManager = self.ownerComp.op('callbackManager')
		

	def SendLua(self, lua_code: str):
		package = {
			'type': 'execute-code',
			'script': lua_code
		}
		self.websocket.sendText(json.dumps(package))
	

	def onReconnectTimerTrigger(self):
		"""TouchDesigner callback when reconnect timer done"""
		self.ownerComp.par.Resetcomm.pulse()

	def onConnect(self):
		self.reconnectTimer.par.initialize.pulse()
		self.callbackManager.Do_Callback('onConnect')

	def onDisconnect(self):
		self.reconnectTimer.par.start.pulse()
		self.callbackManager.Do_Callback('onDisconnect')

	def onParSend(self):
		if self.evalLuacode:
			self.SendLua(self.evalLuacode)
