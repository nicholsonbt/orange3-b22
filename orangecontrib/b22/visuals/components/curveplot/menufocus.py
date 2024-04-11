from AnyQt import QtWidgets




class MenuFocus(QtWidgets.QMenu):  # menu that works well with subwidgets and focusing
    def focusNextPrevChild(self, next):
        return QtWidgets.QWidget.focusNextPrevChild(self, next)
