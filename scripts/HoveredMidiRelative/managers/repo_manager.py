'''Info Header Start
Name : repo_manager
Author : Dan@DAN-4090
Saveversion : 2023.12120
Info Header End'''
from typing import Optional, Union

class RepoManager:
	"""Manages bank/slot storage using StorageManager properties and tables for persistence
	
	Runtime: Uses self.parent.slotPars and self.parent.bankActiveSlots (instant access)
	Persistence: Tables for import/export only
	"""
	def __init__(self, parent_ext):
		self.parent = parent_ext
	
	@property
	def Repo(self):
		"""Get the Repo operator that contains bank tables"""
		return self.parent.ownerComp.op('repoMaker').Repo
	
	def get_slot_parameter(self, slot_idx: int, bank_idx: Optional[int] = None) -> Optional[Union[Par, 'ParGroup']]:
		"""Get parameter from stored property - instant access"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		return self.parent.slotPars[bank_idx][slot_idx]
	
	def set_slot_parameter(self, slot_idx: int, parameter: Union[Par, 'ParGroup'], bank_idx: Optional[int] = None):
		"""Store parameter in stored property - instant"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		self.parent.slotPars[bank_idx][slot_idx] = parameter
	
	def clear_slot(self, slot_idx: int, bank_idx: Optional[int] = None):
		"""Clear a slot"""
		self.set_slot_parameter(slot_idx, None, bank_idx)
	
	def get_active_slot(self, bank_idx: Optional[int] = None) -> Optional[int]:
		"""Get active slot index for a bank"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		return self.parent.bankActiveSlots[bank_idx]
	
	def set_active_slot(self, slot_idx: Optional[int], bank_idx: Optional[int] = None):
		"""Set active slot for a bank"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		self.parent.bankActiveSlots[bank_idx] = slot_idx
	
	def get_all_slots_for_bank(self, bank_idx: Optional[int] = None) -> list:
		"""Get all slots for a bank"""
		if bank_idx is None:
			bank_idx = self.parent.currBank
		
		return self.parent.slotPars[bank_idx].copy()
	
	def is_slot_occupied(self, slot_idx: int, bank_idx: Optional[int] = None) -> bool:
		"""Check if slot has a parameter"""
		return self.get_slot_parameter(slot_idx, bank_idx) is not None
	
	# === Persistence Methods (Tables) ===
	
	def load_from_tables_if_needed(self):
		"""Load FROM tables only if slotPars is empty (optional import)"""
		# Check if we have any data in slotPars
		has_data = any(
			any(slot is not None for slot in bank)
			for bank in self.parent.slotPars
		)
		
		if not has_data:
			# No data in storage, try loading from tables
			self.load_from_tables()
	
	def load_from_tables(self):
		"""Load FROM tables into slotPars (import)"""
		self._ensure_bank_tables()
		
		num_banks = self.parent.numBanks
		for bank_idx in range(num_banks):
			bank_table = self.Repo.op(f'bank{bank_idx}')
			if bank_table is None:
				continue
			
			# Load each slot
			for slot_idx in range(len(self.parent.slotPars[bank_idx])):
				row_idx = slot_idx + 1  # +1 to skip header
				if row_idx >= bank_table.numRows:
					break
				
				op_path = bank_table[row_idx, 0].val
				par_name = bank_table[row_idx, 1].val
				par_type = bank_table[row_idx, 2].val
				is_active = bank_table[row_idx, 3].val == '1'
				
				if op_path and par_name:
					# Reconstruct parameter
					try:
						target_op = op(op_path)
						if target_op:
							if par_type == 'pargroup':
								par = getattr(target_op.parGroup, par_name, None)
							else:
								par = getattr(target_op.par, par_name, None)
							
							if par:
								self.parent.slotPars[bank_idx][slot_idx] = par
								if is_active:
									self.parent.bankActiveSlots[bank_idx] = slot_idx
					except:
						pass
	
	def save_to_tables(self):
		"""Save FROM slotPars TO tables (export)"""
		self._ensure_bank_tables()
		
		num_banks = self.parent.numBanks
		for bank_idx in range(num_banks):
			bank_table = self.Repo.op(f'bank{bank_idx}')
			if bank_table is None:
				continue
			
			# Save each slot
			for slot_idx, par in enumerate(self.parent.slotPars[bank_idx]):
				row_idx = slot_idx + 1  # +1 to skip header
				
				if par is None:
					# Clear slot in table
					bank_table[row_idx, 0] = ''
					bank_table[row_idx, 1] = ''
					bank_table[row_idx, 2] = ''
					bank_table[row_idx, 3] = '0'
				else:
					# Save parameter to table
					try:
						if hasattr(par, 'owner'):
							# Single Par
							op_path = par.owner.path
							par_name = par.name
							par_type = 'par'
						else:
							# ParGroup
							op_path = par[0].owner.path
							par_name = par.name
							par_type = 'pargroup'
						
						bank_table[row_idx, 0] = op_path
						bank_table[row_idx, 1] = par_name
						bank_table[row_idx, 2] = par_type
						# Set active state
						is_active = (self.parent.bankActiveSlots[bank_idx] == slot_idx)
						bank_table[row_idx, 3] = '1' if is_active else '0'
					except:
						# If we can't access the parameter, clear the slot
						bank_table[row_idx, 0] = ''
						bank_table[row_idx, 1] = ''
						bank_table[row_idx, 2] = ''
						bank_table[row_idx, 3] = '0'
	
	def validate_and_clean_all_banks(self):
		"""Validate all parameters in slotPars and clear invalid ones"""
		num_banks = self.parent.numBanks
		
		for bank_idx in range(num_banks):
			for slot_idx in range(len(self.parent.slotPars[bank_idx])):
				par = self.parent.slotPars[bank_idx][slot_idx]
				
				if par is not None:
					# Check if parameter is still valid
					is_valid = False
					
					try:
						# Handle ParGroup
						if hasattr(par, '__iter__') and not isinstance(par, str):
							is_valid = any(p.valid for p in par if p is not None)
						# Handle single Par
						elif hasattr(par, 'valid'):
							is_valid = par.valid
					except:
						is_valid = False
					
					if not is_valid:
						# Clear invalid parameter
						self.parent.slotPars[bank_idx][slot_idx] = None
	
	def _ensure_bank_tables(self):
		"""Ensure all bank tables exist with proper structure"""
		repo = self.Repo
		num_banks = self.parent.numBanks
		num_slots = self.parent.numSlots
		
		for bank_idx in range(num_banks):
			bank_name = f'bank{bank_idx}'
			bank_table = repo.op(bank_name)
			
			is_new_table = bank_table is None
			
			if is_new_table:
				# Create new table DAT
				bank_table = repo.create(tableDAT, bank_name)
			
			# Check if table has correct structure (num rows/cols)
			needs_resize = (bank_table.numRows != num_slots + 1 or bank_table.numCols != 4)
			
			# Only clear and reinitialize if it's a new table or needs resize
			if is_new_table or needs_resize:
				# Set up table structure: header + N slots
				# Columns: path, name, type, active
				bank_table.clear()
				bank_table.setSize(num_slots + 1, 4)  # +1 for header row
				
				# Set header row
				bank_table[0, 0] = 'path'
				bank_table[0, 1] = 'name'
				bank_table[0, 2] = 'type'
				bank_table[0, 3] = 'active'
				
				# Initialize slot rows (row index - 1 = slot index)
				for slot_idx in range(num_slots):
					row_idx = slot_idx + 1  # +1 to skip header
					bank_table[row_idx, 0] = ''  # Empty path
					bank_table[row_idx, 1] = ''  # Empty name
					bank_table[row_idx, 2] = ''  # Empty type
					bank_table[row_idx, 3] = '0'  # Not active
