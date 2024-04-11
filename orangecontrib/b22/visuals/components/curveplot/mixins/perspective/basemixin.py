from Orange.widgets.widget import OWComponent
from orangecontrib.b22.widgets.utils.plots.multiimageplot.utils import SettingsHandlerMixin

from AnyQt import QtCore


class BaseMixin(OWComponent, QtCore.QObject, SettingsHandlerMixin):
    """Assume self.update_view() refreshes the view."""
    def __init__(self, parent, *args, **kwargs):
        OWComponent.__init__(self, parent)
        QtCore.QObject.__init__(self, parent)
        SettingsHandlerMixin.__init__(self)
        
        self.parent = parent

    def add_actions(self, menu):
        """Adds actions to the menu."""
        pass

    def setup(self):
        """Called at end of __init__."""
        pass

    def calculate(self, x, ys):
        return x, ys
    

    def update_view(self):
        self.parent.update_view()

    
    def apply(self, flag=None):
        if flag:
            self.parent.update_selected(self)
    

    @property
    def selected_perpective(self):
        raise NotImplementedError