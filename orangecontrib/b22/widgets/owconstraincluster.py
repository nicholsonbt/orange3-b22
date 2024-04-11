import numpy as np

from AnyQt import QtCore, QtGui, QtWidgets

import Orange.data
from Orange.widgets import gui, settings, widget
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.widgets.utils.itemmodels import DomainModel

from orangecontrib.b22.widgets.utils.hypertable import Hypertable



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
        remove_widget.clicked.connect(lambda: (self.widget.takeItem(self.widget.row(self)), callback()))
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


    cluster_attr = settings.Setting(None)
    axis_attrs = settings.Setting([])
    category_attrs = settings.Setting([])


    axis_model = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                             valid_types=Orange.data.ContinuousVariable)
    
    category_model = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                             valid_types=Orange.data.DiscreteVariable)


    class Error(widget.OWWidget.Error):
        pass


    class Warning(widget.OWWidget.Warning):
        pass


    def __init__(self):
        widget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

        self.data = None

        gui.comboBox(
            self.controlArea, self, "cluster_attr",
            contentsLength=12, searchable=True,
            callback=self.cluster_attr_changed, model=self.category_model
        )
        

        list_container = QtWidgets.QHBoxLayout()

        gbox = QtWidgets.QGroupBox("Spatial Constraints")


        self.axis_list = QtWidgets.QListWidget()

        addbutton = QtWidgets.QPushButton(
            "Add Axis", toolTip="Add a new axis",
            minimumWidth=120,
            shortcut=QtGui.QKeySequence.New
        )

        self.axis_menu = QtWidgets.QMenu(addbutton)
        addbutton.setMenu(self.axis_menu)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.axis_list)
        vbox.addWidget(addbutton)

        gbox.setLayout(vbox)

        list_container.addWidget(gbox)


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

        list_container.addWidget(gbox)

        self.controlArea.layout().addLayout(list_container)

    
    def attr_changed(self):
        self.calculate()


    def cluster_attr_changed(self):
        self.refresh_category_menu()
        self.attr_changed()


    def refresh_axis_menu(self):
        def callback(axis):
            return lambda: self.add_axis(axis)
        
        self.axis_menu.clear()

        for axis in self.valid_axes():
            attr = self.axis_menu.addAction(axis)
            attr.triggered.connect(callback(axis))


    def add_axis(self, axis):
        AttrItem(self.axis_list, self, axis, self.refresh_axis_menu)
        self.refresh_axis_menu()
        self.attr_changed()


        
    def refresh_category_menu(self):
        def callback(category):
            return lambda: self.add_category(category)
        
        self.category_menu.clear()

        for category in self.valid_categories():
            attr = self.category_menu.addAction(category)
            attr.triggered.connect(callback(category))

    
    def add_category(self, category):
        AttrItem(self.category_list, self, category, self.refresh_category_menu)
        self.refresh_category_menu()
        self.attr_changed()


    def init_attr_models(self):
        domain = data.domain if self.data else None
        self.axis_model.set_domain(domain)
        self.category_model.set_domain(domain)

        if not self.cluster_attr:
            self.cluster_attr = self.category_model[0]


    def valid_axes(self):
        axes = [attr.name for attr in self.axis_model]
        existing = [self.axis_list.item(i).label for i in range(self.axis_list.count())]

        return [axis for axis in axes if axis not in existing]
    

    def valid_categories(self):
        categories = [attr.name for attr in self.category_model]
        existing = [self.category_list.item(i).label for i in range(self.category_list.count())]

        return [category for category in categories if category not in existing and category is not self.cluster_attr.name]
    

    def refresh(self):
        self.refresh_axis_menu()
        self.refresh_category_menu()


    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.init_attr_models()
        self.refresh()


    def get_hypertable(self):
        attrs = [self.axis_list.item(i).label for i in range(self.axis_list.count())]
        print(attrs)
        hypertable = Hypertable.from_table(self.data, attrs)

        print(hypertable[self.cluster_attr])

    def calculate(self):
        self.get_hypertable()





if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWConstrainCluster).run(set_data=collagen)