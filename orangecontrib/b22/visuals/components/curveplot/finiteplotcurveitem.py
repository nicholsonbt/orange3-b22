import numpy as np
import pyqtgraph as pg



class FinitePlotCurveItem(pg.PlotCurveItem):
    """
    PlotCurveItem which filters non-finite values from set_data

    Required to work around Qt>=5.12 plotting bug
    See https://github.com/Quasars/orange-spectroscopy/issues/408
    and https://github.com/pyqtgraph/pyqtgraph/issues/1057
    """

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)

    def setData(self, *args, **kargs):
        """Filter non-finite values from x,y before passing on to updateData"""
        if len(args) == 1:
            y = args[0]
        elif len(args) == 2:
            x = args[0]
            y = args[1]
        else:
            x = kargs.get('x', None)
            y = kargs.get('y', None)

        if x is not None and y is not None:
            non_finite_values = np.logical_not(np.isfinite(x) & np.isfinite(y))
            kargs['x'] = x[~non_finite_values]
            kargs['y'] = y[~non_finite_values]
        elif y is not None:
            non_finite_values = np.logical_not(np.isfinite(y))
            kargs['y'] = y[~non_finite_values]
        else:
            kargs['x'] = x
            kargs['y'] = y

        # Don't pass args as (x,y) have been moved to kargs
        self.updateData(**kargs)
