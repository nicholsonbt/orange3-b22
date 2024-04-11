from Orange.widgets.widget import OWComponent


class Base(OWComponent):
    def __init__(self, parent):
        OWComponent.__init__(self, parent)
        self.parent = parent
        

    def add_radio(self, box):
        raise NotImplementedError()
    

    def init_values(self, data):
        pass
    

    def image_values(self):
        raise NotImplementedError()
    

    def image_values_fixed_levels(self):
        return None
    

    def setDisabled(self, flag):
        raise NotImplementedError()
    

    def redraw_data(self):
        self.parent.redraw_data()
