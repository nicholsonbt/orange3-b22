from Orange.widgets.visualize.utils.customizableplot import CommonParameterSetter

from orangecontrib.spectroscopy.widgets.visual_settings import FloatOrUndefined



class ParameterSetter(CommonParameterSetter):

    VIEW_RANGE_BOX = "View Range"

    def __init__(self, master):
        super().__init__()
        self.master = master

    def update_setters(self):
        self.initial_settings = {
            self.ANNOT_BOX: {
                self.TITLE_LABEL: {self.TITLE_LABEL: ("", "")},
                self.X_AXIS_LABEL: {self.TITLE_LABEL: ("", "")},
                self.Y_AXIS_LABEL: {self.TITLE_LABEL: ("", "")},
            },
            self.LABELS_BOX: {
                self.FONT_FAMILY_LABEL: self.FONT_FAMILY_SETTING,
                self.TITLE_LABEL: self.FONT_SETTING,
                self.AXIS_TITLE_LABEL: self.FONT_SETTING,
                self.AXIS_TICKS_LABEL: self.FONT_SETTING,
                self.LEGEND_LABEL: self.FONT_SETTING,
            },
            self.VIEW_RANGE_BOX: {
                "X": {"xMin": (FloatOrUndefined(), None), "xMax": (FloatOrUndefined(), None)},
                "Y": {"yMin": (FloatOrUndefined(), None), "yMax": (FloatOrUndefined(), None)}
            }
        }

        def set_limits(**args):
            for a, v in args.items():
                if a == "xMin":
                    self.viewbox.fixed_range_x[0] = v
                if a == "xMax":
                    self.viewbox.fixed_range_x[1] = v
                if a == "yMin":
                    self.viewbox.fixed_range_y[0] = v
                if a == "yMax":
                    self.viewbox.fixed_range_y[1] = v
            self.master.update_lock_indicators()
            self.viewbox.setRange(self.viewbox.viewRect())

        self._setters[self.VIEW_RANGE_BOX] = {"X": set_limits, "Y": set_limits}

    @property
    def viewbox(self):
        return self.master.plot.vb

    @property
    def title_item(self):
        return self.master.plot.titleLabel

    @property
    def axis_items(self):
        return [value["item"] for value in self.master.plot.axes.values()]

    @property
    def getAxis(self):
        return self.master.plot.getAxis

    @property
    def legend_items(self):
        return self.master.legend.items