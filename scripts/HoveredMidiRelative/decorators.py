
'''Info Header Start
Name : decorators
Author : Dan@DAN-4090
Saveorigin : HoveredMidiRelative.toe
Saveversion : 2023.12120
Info Header End'''

from functools import wraps

def require_valid_parameter(func):
	"""Decorator that handles invalid parameters gracefully.
	
	This decorator:
	1. Blocks execution while invalidation dialog/queue is active
	2. Wraps execution in try-except to catch invalid parameter errors
	3. Queues invalidation check if an error occurs
	
	Usage:
		@require_valid_parameter
		def onResetPar(self, force: bool = False):
			# Core logic only - no boilerplate needed
			pass
	"""
	@wraps(func)
	def wrapper(self, *args, **kwargs):
		# Block execution while invalidation is active (dialog or queue processing)
		if hasattr(self, 'slot_manager') and self.slot_manager.is_invalidation_active():
			return None
		
		try:
			return func(self, *args, **kwargs)
		except Exception as e:
			# Check if it's an invalid parameter error
			if 'Invalid Par' in str(e) or 'tdError' in str(type(e).__name__):
				# Queue invalidation check for all invalid parameters
				if hasattr(self, 'slot_manager'):
					self.slot_manager.queue_invalidation_check()
				return None
			else:
				# Re-raise unexpected errors
				raise
	
	return wrapper


def block_during_invalidation(func):
	"""Simpler decorator that just blocks execution during invalidation.
	
	Use this for methods that don't directly access parameters but should
	be blocked during the invalidation process (e.g., bank changes, mode switches).
	
	Usage:
		@block_during_invalidation
		def onReceiveModeSel(self):
			# Logic that should be blocked during invalidation
			pass
	"""
	@wraps(func)
	def wrapper(self, *args, **kwargs):
		# Block execution while invalidation is active
		if hasattr(self, 'slot_manager') and self.slot_manager.is_invalidation_active():
			return None
		
		return func(self, *args, **kwargs)
	
	return wrapper

