import numpy as np

from AnyQt import QtCore, QtGui, QtWidgets

import Orange.data
from Orange.widgets import gui, settings, widget
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.widgets.utils.itemmodels import DomainModel

class MissingPrimaryException(Exception):
    pass

class MissingSecondaryException(Exception):
    pass

class IncompatibleShapeException(Exception):
    pass





class Operation:
    def __init__(self, name, func):
        self.name = name
        self.func = func




def bubble_operation(operation, *args):
    n = len(args)

    if n > 2:
        mid = n // 2
        left = bubble_operation(operation, *args[:mid])
        right = bubble_operation(operation, *args[mid:])
        return operation(left, right)
    
    if n == 2:
        return operation(*args)
    
    if n == 1:
        return args[0]



def divide(p_data, s_data):
    # RULES:
    # 1. INF / x = INF
    # 2. x / INF = 0

    # 3. INF / INF = NAN
    # 4. x / 0 = NAN
    # 5. NAN / x = NAN
    # 6. x / NAN = NAN

    # 7. x / y = z

    p_inf = np.isinf(p_data)
    s_inf = np.isinf(s_data)

    infs = np.logical_and(p_inf, np.logical_not(s_inf)) # 1
    zero = np.logical_and(s_inf, np.logical_not(p_inf)) # 2

    nans_arrs = [
        np.logical_and(infs, zero), # 3
        s_data == 0, # 4
        np.isnan(p_data), # 5
        np.isnan(s_data), # 6
    ]

    nans = bubble_operation(np.logical_or, *nans_arrs)

    base = np.full_like(p_data, np.nan)
    base[infs] = p_data[infs]
    base[zero] = 0

    valid = np.logical_not(bubble_operation(np.logical_or, infs, zero, nans))

    return np.divide(p_data, s_data, out=base, where=valid)




OPERATIONS = [
    Operation("Addition", lambda p_data, s_data: p_data + s_data),
    Operation("Subtraction", lambda p_data, s_data: p_data - s_data),
    Operation("Multiplication", lambda p_data, s_data: p_data * s_data),
    Operation("Division", lambda p_data, s_data: divide(p_data, s_data)),
]








class OWElementWise(widget.OWWidget, ConcurrentWidgetMixin):
    name = "Elementwise Operations"


    class Inputs:
        p_data = widget.Input("Primary Data", Orange.data.Table, default=True)
        s_data = widget.Input("Secondary Data", Orange.data.Table)


    class Outputs:
        data = widget.Output("Data", Orange.data.Table, default=True)




    settingsHandler = settings.DomainContextHandler()
    
    want_main_area = False


    operation_index = settings.Setting(0)

    operations = OPERATIONS


    class Error(widget.OWWidget.Error):
        incompatible_shapes = widget.Msg("Incompatible shapes: {} and {}")
        missing_primary = widget.Msg("Secondary data but no primary")


    class Warning(widget.OWWidget.Warning):
        pass


    def __init__(self):
        widget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

        self.p_data = None
        self.s_data = None

        gui.comboBox(
            self.controlArea, self, "operation_index",
            contentsLength=12, searchable=True,
            callback=self.operation_changed, items=[op.name for op in self.operations]
        )
        

        # list_container = QtWidgets.QHBoxLayout()

        # gbox = QtWidgets.QGroupBox("Spatial Constraints")


        # self.axis_list = QtWidgets.QListWidget()

        # addbutton = QtWidgets.QPushButton(
        #     "Add Axis", toolTip="Add a new axis",
        #     minimumWidth=120,
        #     shortcut=QtGui.QKeySequence.New
        # )

        # self.axis_menu = QtWidgets.QMenu(addbutton)
        # addbutton.setMenu(self.axis_menu)

        # vbox = QtWidgets.QVBoxLayout()
        # vbox.addWidget(self.axis_list)
        # vbox.addWidget(addbutton)

        # gbox.setLayout(vbox)

        # list_container.addWidget(gbox)


        # gbox = QtWidgets.QGroupBox("Category Constraints")
        # self.category_list = QtWidgets.QListWidget()
        
        # addbutton = QtWidgets.QPushButton(
        #     "Add Category", toolTip="Add a new category",
        #     minimumWidth=120,
        #     shortcut=QtGui.QKeySequence.New
        # )

        # self.category_menu = QtWidgets.QMenu(addbutton)
        # addbutton.setMenu(self.category_menu)

        # vbox = QtWidgets.QVBoxLayout()
        # vbox.addWidget(self.category_list)
        # vbox.addWidget(addbutton)

        # gbox.setLayout(vbox)

        # list_container.addWidget(gbox)

        # self.controlArea.layout().addLayout(list_container)

    
    def reshape_data(self, data, shape):
        # Same shape.
        if data.shape == shape:
            return data

        # A single row.
        if data.shape[0] == 1 and data.shape[1] == shape[1]:
            return np.tile(data, (shape[0], 1))

        # A single column.
        if data.shape[0] == shape[0] and data.shape[1] == 1:
            return np.tile(data, (1, shape[1]))

        raise IncompatibleShapeException(data.shape, shape)


    
    def get_transformed(self):
        if self.s_data is None:
            raise MissingSecondaryException
        
        if self.p_data is None:
            raise MissingPrimaryException
        
        p_shape = self.p_data.X.shape
        s_shape = self.s_data.X.shape

        rows = max(p_shape[0], s_shape[0])
        cols = max(p_shape[1], s_shape[1])

        p_data = self.reshape_data(self.p_data.X.copy(), (rows, cols))
        s_data = self.reshape_data(self.s_data.X.copy(), (rows, cols))

        return p_data, s_data
    

    def do_operation(self, func):
        try:
            return func(*self.get_transformed())
        
        except MissingSecondaryException:
            return self.p_data.X.copy()
        
    
    def calculate(self):
        operation = self.get_operation_func()

        data = self.p_data.copy()

        data.X = self.do_operation(operation)

        return data


    def get_operation_func(self):
        return self.operations[self.operation_index].func


    def operation_changed(self):
        self.commit()


    @Inputs.p_data
    def set_primary_data(self, data):
        self.p_data = data
        self.commit()


    @Inputs.s_data
    def set_secondary_data(self, data):
        self.s_data = data
        self.commit()


    def commit(self):
        self.Error.incompatible_shapes.clear()
        self.Error.missing_primary.clear()

        data = None
        
        try:
            data = self.calculate()

        except IncompatibleShapeException as e:
            self.Error.incompatible_shapes(e.args[0], e.args[1])
        
        except MissingPrimaryException:
            self.Error.missing_primary()

        except AttributeError as e:
            data = None

        self.Outputs.data.send(data)




if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWElementWise).run(set_data=collagen)
