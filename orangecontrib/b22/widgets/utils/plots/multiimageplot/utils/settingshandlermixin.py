from Orange.widgets import settings


class NoSettingsHandlerException(AttributeError):
    def __init__(self, *args):
        if len(args) == 2:
            args = [f"'{args[0].__class__.__name__}' and '{args[1].__class__.__name__}' objects have no attribute 'settingsHandler'"]
        
        AttributeError.__init__(self, *args)



class SettingsHandlerMixin:
    def __init__(self, settings_handler=None):
        self._settings_handler = settings_handler


    @property
    def settingsHandler(self):
        if self._settings_handler:
            return self._settings_handler
        
        if not hasattr(self, "parent"):
            self._settings_handler = settings.DomainContextHandler()
            return self._settings_handler
        
        while hasattr(self, "parent") and self.parent:
            if hasattr(self.parent, "settingsHandler"):
                return self.parent.settingsHandler
            
            self = self.parent
            
        raise NoSettingsHandlerException(self, self.parent)

            
    
    
    @settingsHandler.setter
    def settingsHandler(self, settings_handler):
        self._settings_handler = settings_handler
