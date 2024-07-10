import numpy as np

import Orange.data
from Orange.widgets import gui, settings, widget
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin





class OWUnwrap(widget.OWWidget, ConcurrentWidgetMixin):
    name = "Unwrap"


    class Inputs:
        data = widget.Input("Data", Orange.data.Table, default=True)


    class Outputs:
        data = widget.Output("Data", Orange.data.Table, default=True)


    want_main_area = False
    want_control_area = True
    resizing_enabled = False


    settingsHandler = settings.DomainContextHandler()


    autocommit = settings.Setting(True)


    DEFAULT_DISCONT = None
    DEFAULT_AXIS = 1
    DEFAULT_PERIOD = 2*np.pi


    discont = settings.Setting(DEFAULT_DISCONT)
    axis = settings.Setting(DEFAULT_AXIS)
    period = settings.Setting(DEFAULT_PERIOD)
    



    class Error(widget.OWWidget.Error):
        pass


    class Warning(widget.OWWidget.Warning):
        pass


    def __init__(self):
        widget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

        self.data = None
        self.discont = OWUnwrap.DEFAULT_DISCONT
        self.axis = OWUnwrap.DEFAULT_AXIS
        self.period = OWUnwrap.DEFAULT_PERIOD

        # Add discont, axis and period options.

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Data")



    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.commit.now()


    @gui.deferred
    def commit(self):
        out_data = None

        if self.data:
            out_data = OWUnwrap.unwrap(self.data, self.discont, self.axis, self.period)

        self.Outputs.data.send(out_data)



    @staticmethod
    def unwrap(in_data, discont=DEFAULT_DISCONT, axis=DEFAULT_AXIS, period=DEFAULT_PERIOD):
        out_data = in_data.copy()
        out_data.X = np.unwrap(in_data.X, discont=discont, axis=axis, period=period)
        return out_data






if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(OWUnwrap).run()