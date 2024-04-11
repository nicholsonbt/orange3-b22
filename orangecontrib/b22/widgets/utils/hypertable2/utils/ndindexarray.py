from orangecontrib.b22.widgets.utils.hypertable2.utils.ndlistarray import NDListArray




class NDIndexArray(NDListArray):
    def __init__(self, shape, indices=None):
        NDListArray.__init__(self, shape)

        if indices is not None:
            for i, row in enumerate(indices):
                index = tuple(row)
                self.append(index, i)