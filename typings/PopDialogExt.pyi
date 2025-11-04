from TDStoreTools import StorageManager
import TDFunctions as TDF

class PopDialogExt:

    def __init__(self, ownerComp):
        """
		Popup dialog extension. Just call the DoPopup method to create a popup.
		Provide info in that method. This component can be used over and over,
		no need for a different component for each dialog, unless you want to
		change the insides.
		"""
        self.ownerComp = ownerComp
        self.windowComp = ownerComp.op('popDialogWindow')
        self.details = None
        pass

    def OpenDefault(self, text='', title='', buttons=('OK',), callback=None, details=None, textEntry=False, escButton=1, escOnClickAway=True, enterButton=1, textEntryType='string'):
        pass

    def Open(self, text=None, title=None, buttons=None, callback=None, details=None, textEntry=None, escButton=None, escOnClickAway=None, enterButton=None, textEntryType=None):
        """
		Open a popup dialog.
		text goes in the center of the dialog. Default None, use pars.
		title goes on top of the dialog. Blank means no title bar. Default None,
			use pars
		buttons is a list of strings. The number of buttons is equal to the
			number of buttons, up to 4. Default is ['OK']
		callback: a method that will be called when a selection is made, see the
		 	SetCallback method. This is in addition to all internal callbacks.
		 	If not provided, Callback DAT will be searched.
		details: will be passed to callback in addition to item chosen.
			Default is None.
		If textEntry is a string, display textEntry field and use the string
			as a default. If textEntry is False, no entry field. Default is
			None, use pars
		escButton is a number from 1-4 indicating which button is simulated when
			esc is pressed or False for no button simulation. Default is None,
			use pars. First button is 1 not 0!!!
		enterButton is a number from 1-4 indicating which button is simulated
			when enter is pressed or False for no button simulation. Default is
			None, use pars. First button is 1 not 0!!!
		escOnClickAway is a boolean indicating whether esc is simulated when user
			clicks somewhere besides the dialog. Default is None, use pars
		textEntryType: 'string', 'float', 'integer', 'password'. Default is 
			None, use 'string'
		"""
        pass

    def actualOpen(self):
        pass

    def Close(self):
        """
		Close the dialog
		"""
        pass

    def OnButtonClicked(self, buttonNum):
        """
		Callback from buttons
		"""
        pass

    def OnKeyPressed(self, key):
        """
		Callback for esc or enterpressed.
		"""
        pass

    def OnClickAway(self):
        """
		Callback for esc pressed. Only happens when Escbutton is not None
		"""
        pass

    def OnParValueChange(self, par, val, prev):
        """
		Callback for when parameters change
		"""
        pass

    def OnParPulse(self, par):
        pass

    def UpdateTextHeight(self):
        pass

    @property
    def DialogHeight(self):
        pass