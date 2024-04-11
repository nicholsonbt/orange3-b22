from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems.imageitembase import ImageItemBase




class ImageItemRegistry:
    plot_types = []

    @staticmethod
    def get_names():
        return [plot_type.id for plot_type in ImageItemRegistry.plot_types]


    @staticmethod
    def register(plot_type):
        assert(issubclass(plot_type, ImageItemBase))

        if plot_type not in ImageItemRegistry.plot_types:
            ImageItemRegistry.plot_types.append(plot_type)

    @staticmethod
    def get(index):
        if isinstance(index, int):
            return ImageItemRegistry.plot_types[index]
        
        if isinstance(index, str):
            names = ImageItemRegistry.get_names()
            return names.index(index)
        
        raise Exception()
    
