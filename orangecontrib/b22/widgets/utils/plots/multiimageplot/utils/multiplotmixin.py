import pyqtgraph as pg



class MultiPlotMixin:
    def __init__(self, parent):
         self.parent = parent

         self.plot = pg.GraphicsLayout()

         self.items = []


    def __len__(self):
        return len(self.items)


    def refresh_order(self):
        self.plot.clear()

        for index in self.parent.order:
            self.plot.addItem(self.items[index])


    def clear(self):
        self.items = []
        self.refresh_order()


    def add_item(self, item, index=None):
        if index is None:
            self.items.append(item)
            #self.plot.addItem(item)
        
        else:
            self.items.insert(index, item)
            #self.refresh()
        
        self.refresh_order()
            

    def pop_item(self, index):
        item = self.items.pop(index)
        self.refresh_order()
        return item
