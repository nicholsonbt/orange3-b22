import numpy as np

from scipy import ndimage

from AnyQt import QtCore, QtGui, QtWidgets

import Orange.data
from Orange.widgets import gui, settings, widget
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.widgets.utils.itemmodels import DomainModel

from orangecontrib.spectroscopy.utils import values_to_linspace, index_values

from Orange.data.util import get_unique_names



class CloseButton(QtWidgets.QPushButton):
    def __init__(self):
        QtWidgets.QPushButton.__init__(self)
        
        self.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton))

        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0);
                border: 0px;
            }
            QPushButton::hover {
                background-color: rgba(200, 50, 50, 255);
            }
        """)





class AttrItem(QtWidgets.QListWidgetItem):
    def __init__(self, widget, master, label, callback=None):
        QtWidgets.QListWidgetItem.__init__(self)

        self.widget = widget
        self.master = master
        self.label = label
        self.callback = callback

        self.item = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        text_widget = QtWidgets.QLabel(label)
        layout.addWidget(text_widget)

        layout.addStretch()

        remove_widget = CloseButton()
        remove_widget.clicked.connect(self.callback)
        layout.addWidget(remove_widget)

        self.item.setLayout(layout)

        self.setSizeHint(self.sizeHint())

        self.widget.addItem(self)
        self.widget.setItemWidget(self, self.item)









class OWConstrainCluster(widget.OWWidget, ConcurrentWidgetMixin):
    name = "Constrian Cluster"


    class Inputs:
        data = widget.Input("Data", Orange.data.Table, default=True)


    class Outputs:
        data = widget.Output("Data", Orange.data.Table, default=True)


    settingsHandler = settings.DomainContextHandler()
    
    want_main_area = False
    # resizing_enabled = False


    cluster_attr = settings.ContextSetting(None)
    category_attrs = settings.ContextSetting([])
    constrain_continuous = settings.ContextSetting(False)

    
    

    axis_model = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                             valid_types=Orange.data.ContinuousVariable)
    
    category_model = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                             valid_types=Orange.data.DiscreteVariable)


    connectivity = settings.Setting(0)
    autocommit = settings.Setting(True)



    class Error(widget.OWWidget.Error):
        pass


    class Warning(widget.OWWidget.Warning):
        no_categories = widget.Msg("No categories found.")



    def __init__(self):
        widget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

        self.data = None

        self.cluster_attr = None
        self.constrain_continuous = False
        self.axis_attrs = []
        self.category_attrs = []
        self.connectivity = 0

        gui.comboBox(
            self.controlArea, self, "cluster_attr",
            contentsLength=12, searchable=True,
            callback=self.cluster_attr_changed, model=self.category_model
        )
        
        layout = QtWidgets.QVBoxLayout()

        gbox = QtWidgets.QGroupBox("Spatial Constraints")
        vbox = QtWidgets.QVBoxLayout()

        checkbox = QtWidgets.QCheckBox("Neighbourhood Constraint")
        checkbox.stateChanged.connect(self.spatial_constraint_changed)
        vbox.addWidget(checkbox)


        form = QtWidgets.QFormLayout()
        self.spinbox = gui.spin(self, self, "connectivity", minv=1, maxv=1,
                              step=1, callback=self.connectivity_changed)
        
        form.addRow("Connectivity", self.spinbox)
        vbox.addLayout(form)


        gbox.setLayout(vbox)
        layout.addWidget(gbox)

        gbox = QtWidgets.QGroupBox("Category Constraints")
        self.category_list = QtWidgets.QListWidget()
        
        addbutton = QtWidgets.QPushButton(
            "Add Category", toolTip="Add a new category",
            minimumWidth=120,
            shortcut=QtGui.QKeySequence.New
        )

        self.category_menu = QtWidgets.QMenu(addbutton)
        addbutton.setMenu(self.category_menu)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.category_list)
        vbox.addWidget(addbutton)

        gbox.setLayout(vbox)

        layout.addWidget(gbox)

        self.controlArea.layout().addLayout(layout)

        gui.rubber(self.controlArea)

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Data")


    @property
    def valid_categories(self):
        categories = [attr.name for attr in self.category_model]
        exists = [self.category_list.item(i).label for i in range(self.category_list.count())]

        return [category for category in categories if category not in exists and
                (self.cluster_attr is None or category is not self.cluster_attr.name)]


    def init_models(self):
        domain = self.data.domain if self.data else None
        self.axis_model.set_domain(domain)
        self.category_model.set_domain(domain)

        if len(self.category_model) == 0:
            self.cluster_attr = None
            self.Warning.no_categories()

        else:
            if self.cluster_attr is None:
                self.cluster_attr = self.category_model[0]

        self.spinbox.setMaximum(len(self.axis_model))

        self.category_attrs = []


    def cluster_attr_changed(self):
        if self.cluster_attr.name in self.category_attrs:
            self.remove_category(self.cluster_attr.name)
        
        else:
            self.refresh_category_menu()

        self.commit.deferred()


    def spatial_constraint_changed(self, flag):
        self.constrain_continuous = flag
        self.commit.deferred()

    
    def connectivity_changed(self):
        print(self.connectivity)
        self.commit.deferred()


    def refresh_category_menu(self):
        def callback(category):
            return lambda: self.add_category(category)

        self.category_menu.clear()

        for item in self.valid_categories:
            attr = self.category_menu.addAction(item)
            attr.triggered.connect(callback(item))



    def add_category(self, category):
        def callback(category):
            return lambda: self.remove_category(category)
        
        AttrItem(self.category_list, self, category, callback(category))
        self.category_attrs.append(category)
        self.refresh_category_menu()
        self.commit.deferred()


    def remove_category(self, category):
        self.category_attrs.remove(category)

        items = [self.category_list.item(i) for i in range(self.category_list.count())]
        for item in items:
            if item.label == category:
                row = self.category_list.row(item)
                self.category_list.takeItem(row)

        self.refresh_category_menu()
        self.commit.deferred()


    @staticmethod
    def consensus_cluster(data, attrs):
        ks = [len(attr.values) for attr in attrs]
        n = np.prod(ks)

        counts = np.empty(ks)
        consensus = np.empty((data.shape[0]))

        for i in range(n):
            k = i
            permutation = np.empty((len(ks)))
            
            for j, m in enumerate(ks):
                permutation[j] = k % m
                k = k // m

            indices = np.where((data == permutation).all(axis=1))[0]
            consensus[indices] = i
            counts[tuple(permutation.astype(int))] = np.sum(indices)

        print(counts)

        return consensus, counts
    

    @staticmethod
    def spatial_cluster(col, axes, connectivity):
        if axes is None:
            return col
        
        ls = []
        indices = []
        
        for i in range(axes.shape[1]):
            axis = axes[:, i]

            lsa = values_to_linspace(axis)
            
            ls.append(lsa)
            indices.append(index_values(axis, lsa))

        new_shape = tuple([lsa[2] for lsa in ls])
        hyperspec = np.ones(new_shape) * np.nan

        hyperspec[tuple(indices)] = col
        labelled = np.empty(hyperspec.shape)

        vals = np.unique(hyperspec)
        k = -1

        structure = ndimage.generate_binary_structure(axes.shape[1], connectivity)
        print(structure)

        for i in vals:
            labels, n = ndimage.label(hyperspec == i, structure=structure)
            labelled[labels != 0] = labels[labels != 0] + k
            k += n

        return labelled[tuple(indices)], k


    @Inputs.data
    def set_data(self, data):
        self.Warning.no_categories.clear()
        self.data = data
        self.init_models()
        self.refresh_category_menu()
        self.commit.now()

    
    def get_attrs_data(self, attr_names):
        if len(attr_names) == 0:
            return None, None
        
        indices = [self.data.domain.index(col) for col in attr_names]

        attrs = list(self.data.domain.select_columns(indices))
        data = np.column_stack([self.data.get_column(attr) for attr in attr_names])

        return attrs, data




    @gui.deferred
    def commit(self):
        new_data = None

        if not self.data is None:
            attr_names = [self.cluster_attr.name] + self.category_attrs

            category_attrs, category_data = self.get_attrs_data(attr_names)

            data, _ = OWConstrainCluster.consensus_cluster(category_data, category_attrs)

            n = int(np.nanmax(data))

            if self.constrain_continuous:
                _, axis_data = self.get_attrs_data(self.axis_model)

                data, n = OWConstrainCluster.spatial_cluster(data, axis_data, self.connectivity) # metric=self.metric.lower()

            values = [f"C{i+1}" for i in range(n+1)]
            var = Orange.data.DiscreteVariable(name=get_unique_names(self.data.domain, "Cluster"), values=values)

            print(self.data.X.shape, data.shape)

            new_data = self.data.add_column(var, data, to_metas=True)

        self.Outputs.data.send(new_data)


    






if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    from orangecontrib.b22.utils import loadClustered
    WidgetPreview(OWConstrainCluster).run(set_data=loadClustered())