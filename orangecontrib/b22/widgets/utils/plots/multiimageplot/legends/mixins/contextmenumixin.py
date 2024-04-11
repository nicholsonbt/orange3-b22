from AnyQt import QtWidgets, QtCore

from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItemRegistry

from Orange.widgets import gui


from orangecontrib.b22.widgets.utils.plots.multiimageplot.legends.mixins.imagecoloursettingmixin import ImageColourSettingMixin



class ContextMenuMixin(ImageColourSettingMixin):
    def __init__(self):
        ImageColourSettingMixin.__init__(self)
        self.meta = {}

        self.contextMenu = None

        self.added.connect(self.setup_context_menu)
        self.added.connect(lambda: print("Hello"))


    def setup_context_menu(self):
        print("-------- CONTEXT MENU")
        self.contextMenu = QtWidgets.QMenu()
        self.action1 = QtWidgets.QAction("Option 1")
        self.action2 = QtWidgets.QAction("Option 2")

        self.contextMenu.addAction(self.action1)
        self.contextMenu.addAction(self.action2)

        self.add_choose_plot_type(self.contextMenu)
        self.add_choose_visibility(self.contextMenu)
        ImageColourSettingMixin.add_choose_colour_settings(self, self.contextMenu)
        self.linked_image.add_menu(self.contextMenu)



    # Plot type:
    def add_choose_plot_type(self, menu):
        choose_plot_type = QtWidgets.QWidgetAction(self)
        self.plot_choice = QtWidgets.QComboBox()
        self.plot_choice.addItems(ImageItemRegistry.get_names())

        index = ImageItemRegistry.get(self.linked_image.id)
        self.plot_choice.setCurrentIndex(index)
        self.plot_choice.currentIndexChanged.connect(self.select_plot_type)

        choose_plot_type.setDefaultWidget(self.plot_choice)
        menu.addAction(choose_plot_type)
        

    def select_plot_type(self, plot_type):
        self.parent.convert_to_type(self.index, plot_type)
        self.contextMenu.close()

    


    # Visibility:
    def add_choose_visibility(self, menu):
        self.visible = QtWidgets.QAction("Show Plot", menu, checkable=True)
        self.visible.toggled.connect(self.toggle_visibility)
        self.visible.toggle()
        menu.addAction(self.visible)


    def toggle_visibility(self):
        if self.visible.isChecked():
            self.linked_image.show()

        else:
            self.linked_image.hide()
            




    def show_context_menu(self, pos):
        self.contextMenu.exec_(pos)
        return True
    

    def update(self):
        ImageColourSettingMixin.update(self)