from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets import gui, settings



class OWGate(OWWidget):
    name = "Gate"
    description = "A gate to control the flow of data."
    icon = "icons/gate.svg"
    id = "orangecontrib.b22.flow.widgets.gate"
    priority = 10


    class Inputs:
        data = Input("Data", object, default=True)

    class Outputs:
        data = Output("Data", object, default=True)

    class Warning(OWWidget.Warning):
        not_connected = Msg("Gate is closed.")


    want_main_area = False
    autocommit = settings.Setting(False)


    def __init__(self):
        super().__init__()

        self.data = None

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Data")




    @Inputs.data
    def setData(self, data):
        self.data = data
        self.Warning.not_connected()
        self.commit.deferred()


    @gui.deferred
    def commit(self):
        self.Warning.not_connected.clear()
        self.Outputs.data.send(self.data)




if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    WidgetPreview(OWGate).run()