import bottleneck

from AnyQt import QtCore, QtWidgets

from Orange.widgets import settings

from orangecontrib.spectroscopy.widgets.gui import lineEditDecimalOrNone

from orangecontrib.b22.visuals.components.curveplot.mixins.perspective.basemixin import BaseMixin

from orangecontrib.b22.visuals.components.curveplot.mixins.perspective.utils import FormAction



class CascadeMixin(BaseMixin):
    __DEFAULT_GAP = 0.1

    cascade = settings.Setting(False)
    gap = settings.Setting(__DEFAULT_GAP, schema_only=True)


    def __init__(self, parent, *args, **kwargs):
        BaseMixin.__init__(self, parent, *args, **kwargs)

        self.allow_cascade = kwargs.get("allow_cascade", True)
        self.allow_select_gap = kwargs.get("allow_select_cascade_gap", True)
        self.shortcut = kwargs.get("cascade_shortcut", QtCore.Qt.Key_Q)

        self.action = None
        self.gap_le = None
    

    def add_actions(self, menu, shortcut_visible=True):
        if self.allow_cascade:
            self.action = QtWidgets.QAction(
                "Cascade plot", self.parent, shortcut=self.shortcut, checkable=True,
                triggered=lambda x: self.cascade_changed()
            )

            self.action.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
            self.action.setShortcutVisibleInContextMenu(shortcut_visible)
            menu.addAction(self.action)
            self.parent.addAction(self.action)

            if self.allow_select_gap:
                action = FormAction(self.parent)
                self.gap_le = lineEditDecimalOrNone(action.form_box, self, "gap", callback=self.gap_changed)
                action.addRow("Cascade gap", self.gap_le)
                menu.addAction(action)
                self.parent.addAction(action)
        

    def setup(self):
        self.apply()


    def calculate(self, x, ys):
        new_ys = ys.copy()

        if self.cascade:
            data = new_ys[::-1,:]

            prev = data[0,:]

            for i, row in enumerate(data[1:,:]):
                if self.gap == 0:
                    offset = bottleneck.nanmax(prev) - bottleneck.nanmin(row)
                else:
                    minimum = bottleneck.nanmin(row-prev)
                    offset = float(self.gap) - minimum

                data[i+1,:] = row + offset

                prev = row

            self.parent.parent.Warning.large_cascade.clear()

            if data.shape[0] > 50:
                self.parent.parent.Warning.large_cascade(new_ys.shape[0])

            new_ys = data[::-1,:]
        

        return x, new_ys
    

    @property
    def selected_perpective(self):
        return self.cascade
    



    def gap_changed(self):
        self.update_view()

    
    def cascade_changed(self):
        self.cascade = not self.cascade
        self.apply()
        self.update_view()

    
    def apply(self, flag=None):
        if flag is None:
            flag = self.cascade
        else:
            self.cascade = flag
        
        if flag:
            BaseMixin.apply(self, flag)

        self.action.setChecked(flag)
