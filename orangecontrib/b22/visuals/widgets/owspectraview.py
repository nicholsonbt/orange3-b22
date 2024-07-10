import Orange.data
from Orange.widgets import widget, settings



class OWSpectraView(widget.OWWidget):
    name = "Spectra View"


    class Inputs:
        data = widget.Input("Data", Orange.data.Table, default=True)


    class Outputs:
        data = widget.Input("Data", Orange.data.Table, default=True)


    priority = 10

    want_main_area = False

    settingsHandler = settings.DomainContextHandler()


    def __init__(self):
        super().__init__()
        self.data = None


    @Inputs.data
    def set_data(self, data):
        self.data = data


    def onDeleteWidget(self):
        super().onDeleteWidget()



if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWSpectraView).run(set_data=collagen)