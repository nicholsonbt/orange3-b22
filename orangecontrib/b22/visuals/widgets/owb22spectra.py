import Orange.data
from Orange.widgets.widget import OWWidget, Msg, Input
from Orange.widgets.settings import Setting, DomainContextHandler, SettingProvider

from orangewidget.utils.visual_settings_dlg import VisualSettingsDialog

from orangecontrib.spectroscopy.widgets.utils import SelectionOutputsMixin

from orangecontrib.b22.visuals.components import CurvePlot
from orangecontrib.b22.visuals.components.curveplot.utils import SELECTMANY




class OWB22Spectra(OWWidget, SelectionOutputsMixin):
    name = "B22 Spectra"


    class Inputs:
        data = Input("Data", Orange.data.Table, default=True)
        data_subset = Input("Data subset", Orange.data.Table)


    class Outputs(SelectionOutputsMixin.Outputs):
        pass


    priority = 10

    want_control_area = False

    settingsHandler = DomainContextHandler()

    curveplot = SettingProvider(CurvePlot)
    visual_settings = Setting({}, schema_only=True)

    graph_name = "curveplot.plotview"  # need to be defined for the save button to be shown


    class Information(SelectionOutputsMixin.Information):
        showing_sample = Msg("Showing {} of {} curves.")
        view_locked = Msg("Axes are locked in the visual settings dialog.")


    class Warning(OWWidget.Warning):
        no_x = Msg("No continuous features in input data.")
        large_cascade = Msg("Showing cascade with {} spectra.")


    def __init__(self):
        super().__init__()
        SelectionOutputsMixin.__init__(self)
        self.settingsAboutToBePacked.connect(self.prepare_special_settings)
        self.curveplot = CurvePlot(self, select=SELECTMANY)
        self.curveplot.selection_changed.connect(self.selection_changed)
        self.curveplot.new_sampling.connect(self._showing_sample_info)
        self.curveplot.locked_axes_changed.connect(
            lambda locked: self.Information.view_locked(shown=locked))
        self.mainArea.layout().addWidget(self.curveplot)
        self.resize(900, 700)
        VisualSettingsDialog(self, self.curveplot.parameter_setter.initial_settings)


    @Inputs.data
    def set_data(self, data):
        self.closeContext()  # resets schema_only settings
        self._showing_sample_info(None)
        self.Warning.no_x.clear()
        self.openContext(data)
        self.curveplot.set_data(data, auto_update=False)
        if data is not None and not len(self.curveplot.data_x):
            self.Warning.no_x()
        self.selection_changed()


    @Inputs.data_subset
    def set_subset(self, data):
        self.curveplot.set_data_subset(data.ids if data else None, auto_update=False)


    def set_visual_settings(self, key, value):
        self.curveplot.parameter_setter.set_parameter(key, value)
        self.visual_settings[key] = value


    def handleNewSignals(self):
        self.curveplot.update_view()


    def selection_changed(self):
        self.send_selection(self.curveplot.data,
                            self.curveplot.selection_group)


    def _showing_sample_info(self, num):
        if num is not None and self.curveplot.data and num != len(self.curveplot.data):
            self.Information.showing_sample(num, len(self.curveplot.data))
        else:
            self.Information.showing_sample.clear()


    def save_graph(self):
        # directly call save_graph so it hides axes
        self.curveplot.save_graph()


    def prepare_special_settings(self):
        self.curveplot.save_peak_labels()


    def onDeleteWidget(self):
        self.curveplot.shutdown()
        super().onDeleteWidget()



if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWB22Spectra).run(set_data=collagen)