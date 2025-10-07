
'''Info Header Start
Name : IntechGridCommExt
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.179.toe
Saveversion : 2023.12120
Info Header End'''

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
		
	@property
	def isQueued(self) -> bool:
		"""Used for package that supports queued messages"""
		return self.ownerComp.par.Queuedmessage.eval()

	def SendLua(self, lua_code: str, queue: bool = False):
		if queue:
			# Used for package that supports queued messages
			package_type = 'queue-code'
		else:
			package_type = 'execute-code'
		#package_type = 'execute-code'
		package = {
			'type': package_type,
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
			self.SendLua(self.evalLuacode, queue=self.isQueued)
