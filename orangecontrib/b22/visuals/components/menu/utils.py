import numpy as np
from typing import overload

import random
import os

from AnyQt import QtCore, QtGui, QtWidgets

import Orange.data
from Orange.widgets import widget as owwidget
from Orange.widgets import gui, settings
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.widgets.utils.itemmodels import DomainModel





def get_icon(filename, parent=None):
    path = "orangecontrib\\b22\\widgets\\icons\\"

        
    if parent is None:
        parent = QtWidgets.QApplication.instance()

    try:
        pixmapi = getattr(QtWidgets.QStyle, filename, None)
        return parent.style().standardIcon(pixmapi)
    
    except TypeError:
        return QtGui.QIcon(path + filename)

    
    

    
    
