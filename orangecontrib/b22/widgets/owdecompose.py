import numpy as np

import random

from AnyQt import QtCore, QtGui, QtWidgets

import Orange.data
from Orange.widgets import widget as owwidget
from Orange.widgets import gui, settings
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.widgets.utils.itemmodels import DomainModel

from sklearn import decomposition

from orangecontrib.b22.visuals.components.menu.utils import get_icon





def delete_layout(layout):
     if layout is not None:
         while layout.count():
             item = layout.takeAt(0)
             widget = item.widget()
             if widget is not None:
                 widget.setParent(None)
             else:
                 delete_layout(item.layout())
    
    



class IconButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        QtWidgets.QPushButton.__init__(self)

        icon = get_icon(*args)
        self.setIcon(icon)

        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                padding: 2px;
                margin: 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: lightgray;
            }
            QPushButton:pressed {
                background-color: gray;
            }
        """)


    def resizeEvent(self, event):
        height = event.size().height()
        self.resize(QtCore.QSize(height, height))





class AdvancedControl(QtWidgets.QWidget):
    option_reset = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QWidget.__init__(self)


    def reset_control(self):
        raise NotImplementedError()



class SeedSelector(AdvancedControl):
    seed_changed = QtCore.pyqtSignal(int)

    def __init__(self, default=0, lower=0, upper=99):
        AdvancedControl.__init__(self)

        self.default = default
        self.lower = lower
        self.upper = upper

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        label = QtWidgets.QLabel("Seed:")

        self._spinbox = QtWidgets.QSpinBox()
        self._spinbox.setRange(lower, upper)
        self._spinbox.setMinimumWidth(80)
        self._spinbox.setWrapping(True)
        self._spinbox.valueChanged.connect(lambda value: self.seed_changed.emit(value))


        button_box = QtWidgets.QHBoxLayout()
        button_box.setContentsMargins(0,0,0,0)
        button_box.setSpacing(0)
        
        random_button = IconButton("shuffle.svg")
        random_button.clicked.connect(self.select_random)

        reset_button = IconButton("SP_BrowserReload", self)
        reset_button.pressed.connect(self.reset_control)

        button_box.addWidget(random_button)
        button_box.addWidget(reset_button)


        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(self._spinbox)
        layout.addLayout(button_box)

        self.setLayout(layout)

        self.reset_control()


    def select_random(self):
        seed = random.randint(self.lower, self.upper)
        self._spinbox.setValue(seed)


    @property
    def seed(self):
        return self._spinbox.value()
    

    def reset_control(self):
        self._spinbox.setValue(self.default)
        self.option_reset.emit()







class AdvancedMenu(QtWidgets.QWidget):
    def __init__(self, parent=None, title="Advanced"):
        QtWidgets.QWidget.__init__(self, parent)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        self.title = title

        self.menu = QtWidgets.QMenu(parent)
        menu_button = QtWidgets.QPushButton(title)
        menu_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        menu_button.setMenu(self.menu)

        reset_button = IconButton("SP_BrowserReload")
        reset_button.pressed.connect(self.on_reset)

        layout.addWidget(menu_button)
        layout.addWidget(reset_button)

        self.setLayout(layout)

        self.setContentLayout()


    
    @QtCore.pyqtSlot()
    def on_reset(self):
        resetables = self.menu.findChildren(AdvancedControl)
        
        for widget in resetables:
            widget.reset_control()



    def setContentLayout(self, layout=None):
        self.menu.clear()

        if layout is None:
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(QtWidgets.QLabel("No advanced options"))

        action = QtWidgets.QWidgetAction(self.menu)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        action.setDefaultWidget(widget)

        self.menu.addAction(action)










def overload_default(default, kwargs):
    combined = default.copy()

    for k, v in kwargs.items():
        combined[k] = v

    return combined


def ensure_positive(data):
    negs = data < 0

    if np.allclose(data[negs], 0):
        new_data = data.copy()
        new_data[negs] = 0
        return new_data
    
    raise ValueError(f"matrix includes negative values such as {np.min(data)}")


def add_insignificant_noise(data):
    scale = 1e-9

    k = np.mean(data) * scale

    noise = np.random.random(data.shape) * k

    return data + noise


def init_nmf(data):
    data = ensure_positive(data)
    data = add_insignificant_noise(data)
    return data


def init_ica(data):
    data = add_insignificant_noise(data)
    return data


    



# class Model:
#     def __init__(self, cls, data, **kwargs):
#         """_summary_

#         N = samples
#         M = features (wavenumbers)
#         K = components

#         Parameters
#         ----------
#         data : _type_
#             _description_
#         """
#         self._model = cls(**kwargs)
#         self._weights = self._model.fit_transform(data)

#     @property
#     def weights(self):
#         """_summary_

#         (N, K)

#         Returns
#         -------
#         _type_
#             _description_
#         """
#         return self._weights
    
#     @property
#     def components(self):
#         """_summary_

#         (K, M)

#         Returns
#         -------
#         _type_
#             _description_
#         """
#         return self._model.components_
    

#     def remove_component(self, index):
#         self._model.components_ = np.delete(self._model.components_, index, 0)
#         self._weights = np.delete(self._weights, index, 1)

    
    
#     @property
#     def compose(self):
#         return np.dot(self.weights, self.components)

    
#     @staticmethod
#     def create(cls, init=None, **kwargs):
#         if init is None:
#             init = lambda data: data
            
#         return lambda data, cls=cls, init=init, default=kwargs, **kwargs: Model(cls, init(data), **overload_default(default, kwargs))




# DECOMPOSITIONS = [
#         ("ICA", Model.create(FastICA, init=init_ica)),
#         ("Factor Analysis", Model.create(FactorAnalysis)),
#         ("NMF", Model.create(NMF, init=init_nmf)),
#         ("PCA", Model.create(PCA)),
#         ("TruncatedSVD", Model.create(TruncatedSVD)),
#     ]




class Model(owwidget.OWComponent, QtWidgets.QWidget):
    def __init__(self, parent,  model):
        owwidget.OWComponent.__init__(self)
        QtWidgets.QWidget.__init__(self)

        self.indent = QtWidgets.QWidget()
        self.indent.setFixedWidth(15)

        self.parent = parent

        self.model = None
        self.cls = model
        self.weights = None


    @property
    def data(self):
        return self.parent.data





# FastICA, FactorAnalysis, NMF, PCA, TruncatedSVD


class PCA(Model):
    name = "Principal Component Analysis"
    abbr = "PCA"

    k = 4
    min_variance = 0.8
    max_components = 20


    changed = QtCore.pyqtSignal()


    def __init__(self, parent):
        Model.__init__(self, parent, decomposition.PCA)


    def init(self, data, **kwargs):
        if data is None:
            self.model = None
            self.weights = None
        
        else:
            self.model = self.cls(**kwargs)
            self.weights = self.model.fit_transform(data)
            
        self.changed.emit()


    def get_components(self):
        pass

    def get_weights(self):
        pass

    def get_denoised(self):
        pass

    def get_residuals(self):
        pass

    def get_basic_controls(self):
        layout = QtWidgets.QVBoxLayout()
        
        
        layout.addWidget(self.get_n_components_groupbox())

        #layout = QtWidgets.QVBoxLayout()


        return layout
    

    def get_n_components_groupbox(self):
        ## User-selected n components:
        n_components = QtWidgets.QRadioButton("Use N Components")
        
        label = QtWidgets.QLabel("Components:")
        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(1, self.max_components)
        spinbox.setValue(self.k)
        spinbox.valueChanged.connect(self.k_changed)

        box = QtWidgets.QHBoxLayout()
        box.addWidget(self.indent)
        box.addWidget(label)
        box.addWidget(spinbox)

        n_components_box = QtWidgets.QVBoxLayout()
        n_components_box.addLayout(box)


        ## Percentage Variance

        percentage_variance = QtWidgets.QRadioButton("Use Percentage Variance")
        
        label = QtWidgets.QLabel("Variance:")
        spinbox = QtWidgets.QDoubleSpinBox()
        spinbox.setRange(0, 1)
        spinbox.setSingleStep(0.01)
        spinbox.setValue(self.min_variance)
        spinbox.valueChanged.connect(self.min_variance_changed)

        box = QtWidgets.QHBoxLayout()
        box.addWidget(self.indent)
        box.addWidget(label)
        box.addWidget(spinbox)

        percentage_variance_box = QtWidgets.QVBoxLayout()
        percentage_variance_box.addLayout(box)


        ## MLE

        mle_computed = QtWidgets.QRadioButton("Use Minka's MLE")
        all_components = QtWidgets.QRadioButton("Use all components")

        ##



        choose_n_components = QtWidgets.QButtonGroup()
        choose_n_components.addButton(n_components)
        choose_n_components.addButton(percentage_variance)
        choose_n_components.addButton(mle_computed)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(n_components)
        vbox.addLayout(n_components_box)
        vbox.addWidget(percentage_variance)
        vbox.addLayout(percentage_variance_box)
        vbox.addWidget(mle_computed)
        vbox.addWidget(all_components)

        groupbox = QtWidgets.QGroupBox("N Components")
        groupbox.setLayout(vbox)

        # n components:
        # n components
        # Percentage Variance
        # Predict
        # All

        return groupbox


        
    def get_advanced_controls(self):
        layout = QtWidgets.QVBoxLayout()

        seed_selector = SeedSelector()
        # seed_selector.seed_changed.connect(self.seed_changed)
        layout.addWidget(seed_selector)

        return layout
    
    
    def k_changed(self):
        self.init(n_components=self.k)


    def min_variance_changed(self):
        self.init(n_components=self.min_variance)






class LCA:
    name = "Latent Semantic Analysis"
    abbr = "LSA"

    def __init__(self):
        pass

    def get_components(self):
        pass

    def get_weights(self):
        pass

    def get_denoised(self):
        pass

    def get_residuals(self):
        pass

    def get_basic_controls(self):
        k = 5
        layout = QtWidgets.QVBoxLayout()
        box = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Components:")
        self.spinbox = QtWidgets.QSpinBox()
        self.spinbox.setValue(k)
        self.spinbox.valueChanged.connect(self.k_changed)
        box.addWidget(label)
        box.addWidget(self.spinbox)
        layout.addLayout(box)

        return layout

        
    def get_advanced_controls(self):
        return None
    
    
    def k_changed(self):
        pass



DECOMPOSITIONS = [PCA, LCA]















class OWDecompose(owwidget.OWWidget, ConcurrentWidgetMixin):
    name = "Decompose"


    class Inputs:
        data = owwidget.Input("Data", Orange.data.Table, default=True)


    class Outputs:
        data = owwidget.Output("Data", Orange.data.Table, default=True)
        components = owwidget.Output("Components", Orange.data.Table)
        denoised = owwidget.Output("Denoised", Orange.data.Table)


    settingsHandler = settings.DomainContextHandler()
    
    want_main_area = False

    decomposition_index = settings.Setting(0)

    # k = settings.Setting(3)

    decompositions = DECOMPOSITIONS



    class Error(owwidget.OWWidget.Error):
        pass


    class Warning(owwidget.OWWidget.Warning):
        pass


    def __init__(self):
        owwidget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)


        gui.comboBox(
            self.controlArea, self, "decomposition_index",
            contentsLength=12, searchable=True,
            callback=self.decomposition_type_changed, items=[x.name for x in self.decompositions]
        )

        vbox = QtWidgets.QVBoxLayout()

        self.basic_menu = QtWidgets.QVBoxLayout()
        vbox.addLayout(self.basic_menu)



        self.advanced_menu = AdvancedMenu(self)
        vbox.addWidget(self.advanced_menu)


        ####
        # btn = QtWidgets.QPushButton("Menu")
        # menu = QtWidgets.QMenu()
        # btn.setMenu(menu)

        # widget = QtWidgets.QWidget()
        # widget.setLayout(vbox)

        # action = QtWidgets.QWidgetAction(self)
        # action.setDefaultWidget(widget)

        # menu.addAction(action)

        # self.controlArea.layout().addWidget(btn)
        ####

        vbox.addStretch()

        self.controlArea.layout().addLayout(vbox)
        
        self.data = None
        self.model = None
        self.decomposition = None

        self.decomposition_type_changed()


    def init_basic_controls(self):
        delete_layout(self.basic_menu.takeAt(0))
        self.basic_menu.addLayout(self.decomposition.get_basic_controls())



    def init_advanced_controls(self):
        self.advanced_menu.setContentLayout(self.decomposition.get_advanced_controls())


    def init_controls(self):
        self.init_basic_controls()
        self.init_advanced_controls()


    def decomposition_type_changed(self):
        if self.decomposition_index >= len(self.decompositions):
            self.decomposition_index = 0

        self.decomposition = self.decompositions[self.decomposition_index]()
        self.init_controls()
        self.commit()

    
    def k_changed(self):
        self.k = self.spinbox.value()
        self.commit()


    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.commit()


    def get_data(self):
        if not (self.data is None or self.model is None):
            table = self.data.copy()

            weights = self.model.weights

            for i in range(weights.shape[1]):
                table = table.add_column(Orange.data.ContinuousVariable(f"W{i}"), weights[:,i], to_metas=True)
            
            return table
    
        return None


    def get_components(self):
        if not (self.data is None or self.model is None):
            domain = Orange.data.Domain(self.data.domain.attributes)
            components = self.model.components
            return Orange.data.Table.from_numpy(domain, components)
        
        return None


    def get_denoised(self):
        if not (self.data is None or self.model is None):
            table = self.data.copy()

            table.X = self.model.compose

            return table
        
        return None


    def commit(self):
        self.model = None

        # self.model.remove_component(0)
        
        # if not self.data is None:
        #     try:
        #         self.model = self.decomposition(self.data.X, n_components=self.k)
        #     except ValueError as e:
        #         print(f"ERROR: {e}")
        
        # self.Outputs.data.send(self.get_data())
        # self.Outputs.components.send(self.get_components())
        # self.Outputs.denoised.send(self.get_denoised())




if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    # collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWDecompose).run()
