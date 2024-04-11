



def default_image_values(data):
        return data.X[:,:,[500, 1000, 1500]]




class ImageItemBase:
    # pg.PlotItems have a 'name' method, so the term 'name' can't be
    # used here.
    id = "Unknown"
    

    def __init__(self, image_values=None):
        self.set_image_values(image_values)
        
    
    def set_image_values(self, image_values):
        if not image_values:
            image_values = default_image_values
        
        self.image_values = image_values


    def get_values(self, data):
        return self.image_values(data)


    def set_data(self, imdata, domain, coords, image_values_fixed_levels):
        raise NotImplementedError()
    

    def set_border(self, pen):
        raise NotImplementedError()
    
    def add_menu(self, menu):
        pass
