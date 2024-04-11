from AnyQt import QtCore

from orangecontrib.b22.visuals.components.curveplot.interactiveviewbox import InteractiveViewBox




class InteractiveViewBoxC(InteractiveViewBox):

    def __init__(self, graph):
        super().__init__(graph)
        self.y_padding = 0.02

    def wheelEvent(self, ev, axis=None):
        # separate axis handling with modifier keys
        if axis is None:
            axis = 1 if ev.modifiers() & QtCore.Qt.ControlModifier else 0
        super().wheelEvent(ev, axis=axis)
