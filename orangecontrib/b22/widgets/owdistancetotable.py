from Orange.widgets import widget, settings, gui

from Orange import distance
import Orange.data

import numpy as np

from scipy.sparse import issparse
import bottleneck as bn

from AnyQt import QtCore, QtGui, QtWidgets


from Orange.widgets.unsupervised.owdistances import MetricDefs, InterruptException

from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin

from Orange.data.util import get_unique_names



class OWDistanceToTable(widget.OWWidget):
    name = "Distances to table"
    description = "Compute a matrix of pairwise distances."
    icon = "icons/Distance.svg"
    keywords = "distances"
    id = "orangecontrib.b22.widgets.owdistancetotable.OWDistanceToTable"


    class Inputs:
        data = widget.Input("Data", Orange.data.Table, default=True)
        distances = widget.Input("Distances", Orange.misc.DistMatrix)


    class Outputs:
        data = widget.Output("Data", Orange.data.Table)


    settings_version = 1

    distance_name = settings.Setting(None)
    to_metas = settings.Setting(True)

    want_main_area = False
    resizing_enabled = False


    class Error(widget.OWWidget.Error):
        pass


    class Warning(widget.OWWidget.Warning):
        pass


    def __init__(self):
        widget.OWWidget.__init__(self)

        self.data = None
        self.distances = None

        self.distance_name = "Distance"

        box = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Name:")

        name_le = gui.lineEdit(None, self, "distance_name", callback=self.name_changed, callbackOnType=True)

        box.addWidget(label)
        box.addWidget(name_le)

        self.controlArea.layout().addLayout(box)

        #gui.auto_apply(self.buttonsArea, self, "autocommit")


    def name_changed(self):
        self.commit()


    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.commit()


    @Inputs.distances
    def set_distances(self, distances):
        self.distances = distances
        self.commit()


    def commit(self):
        out_data = self.create_out_data()
        self.Outputs.data.send(out_data)


    def create_out_data(self):
        MAX_COLS = 5

        if self.distances is None or self.distances.shape[1] > MAX_COLS:
            return None

        variables = [Orange.data.ContinuousVariable(get_unique_names(self.data.domain, f"{self.distance_name} {i+1}")) for i in range(self.distances.shape[1])]

        
        if self.data is None:
            domain = Orange.data.Domain(variables)
            return Orange.data.Table.from_numpy(domain, self.distances)

        out_data = self.data

        for i, variable in enumerate(variables):
            out_data = out_data.add_column(variable, self.distances[:,i], to_metas=self.to_metas)

        return out_data






    def onDeleteWidget(self):
        super().onDeleteWidget()


    




if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWDistanceToTable).run(set_data=collagen)
