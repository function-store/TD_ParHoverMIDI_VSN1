
CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###
import json
class IntechGridCommExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.websocket: websocketDAT = self.ownerComp.op('websocket1')
		

	def SendLua(self, lua_code: str):
		package = {
			'type': 'execute-code',
			'script': lua_code
		}
		self.websocket.sendText(json.dumps(package))
	


