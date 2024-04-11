import numpy as np

from AnyQt import QtCore, QtWidgets

from Orange.widgets import settings

from orangecontrib.spectroscopy.widgets.gui import lineEditDecimalOrNone


from orangecontrib.b22.visuals.components.curveplot.mixins.perspective.basemixin import BaseMixin


from orangecontrib.b22.visuals.components.curveplot.mixins.perspective.utils import FormAction, bin_combine
    




class WaterfallMixin(BaseMixin):
    __DEFAULT_X_GAP = 10
    __DEFAULT_Y_GAP = 0.1

    waterfall = settings.Setting(False)
    gap_x = settings.Setting(__DEFAULT_X_GAP, schema_only=True)
    gap_y = settings.Setting(__DEFAULT_Y_GAP, schema_only=True)


    def __init__(self, parent, *args, **kwargs):
        BaseMixin.__init__(self, parent, *args, **kwargs)

        self.allow_waterfall = kwargs.get("allow_waterfall", True)
        self.allow_select_x_gap = kwargs.get("allow_select_x_gap", True)
        self.allow_select_y_gap = kwargs.get("allow_select_y_gap", True)
        self.shortcut = kwargs.get("waterfall_shortcut", QtCore.Qt.Key_W)

        self.action = None
        self.gap_x_le = None
        self.gap_y_le = None
    

    def add_actions(self, menu, shortcut_visible=True):
        if self.allow_waterfall:
            self.action = QtWidgets.QAction(
                "Waterfall plot", self.parent, shortcut=self.shortcut, checkable=True,
                triggered=lambda x: self.waterfall_changed()
            )

            self.action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            self.action.setShortcutVisibleInContextMenu(shortcut_visible)
            menu.addAction(self.action)
            self.parent.addAction(self.action)

            if self.allow_select_x_gap:
                action = FormAction(self.parent)
                self.gap_x_le = lineEditDecimalOrNone(action.form_box, self, "gap_x", callback=self.gap_changed)
                action.addRow("Waterfall gap x", self.gap_x_le)
                menu.addAction(action)
                self.parent.addAction(action)

            if self.allow_select_y_gap:
                action = FormAction(self.parent)
                self.gap_y_le = lineEditDecimalOrNone(action.form_box, self, "gap_y", bottom=0, top=90, callback=self.gap_changed)
                action.addRow("Waterfall gap y", self.gap_y_le)
                menu.addAction(action)
                self.parent.addAction(action)
        

    def setup(self):
        self.apply()


    def calculate(self, x, ys):
        if self.waterfall:
            new_xs, new_ys = bin_combine(
                np.array([x + float(self.gap_x)*i for i in range(ys.shape[0])]),
                np.array([y + float(self.gap_y)*i for i, y in enumerate(ys[::-1,:])])
            )

            return new_xs, new_ys[::-1,:]

        return x, ys
    

    @property
    def selected_perpective(self):
        return self.waterfall


    def gap_changed(self):
        self.update_view()

    
    def waterfall_changed(self):
        self.waterfall = not self.waterfall
        self.apply()
        self.update_view()

    
    def apply(self, flag=None):
        if flag is None:
            flag = self.waterfall
        else:
            self.waterfall = flag
        
        if flag:
            BaseMixin.apply(self, flag)

        self.action.setChecked(flag)
