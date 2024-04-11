import time
import random
import bottleneck
import numpy as np

from AnyQt import QtCore, QtGui, QtWidgets

from Orange.widgets.utils.concurrent import TaskState, ConcurrentMixin

from orangecontrib.b22.visuals.components.curveplot.utils import INDIVIDUAL
from orangecontrib.b22.visuals.components.curveplot.interruptexception import InterruptException




class ShowIndividual(QtCore.QObject, ConcurrentMixin):

    shown = QtCore.pyqtSignal()

    def __init__(self, master):
        QtCore.QObject.__init__(self, parent=master)
        ConcurrentMixin.__init__(self)
        self.master = master

    def show(self):
        master = self.master
        master.clear_graph()  # calls cancel
        master.view_average_menu.setChecked(False)
        master.set_pen_colors()
        master.viewtype = INDIVIDUAL
        if not master.data:
            return
        sampled_indices = master._compute_sample(master.data.X)
        self.start(self.compute_curves, master.data_x, master.data.X,
                   sampled_indices)

    @staticmethod
    def compute_curves(x, ys, sampled_indices, state: TaskState):
        try:
            import dask
            import dask.array as da
            from orangecontrib.spectroscopy import dask_client
        except ImportError:
            dask = None
            dask_client = None

        is_dask = dask and isinstance(ys, dask.array.Array)

        def progress_interrupt(i: float):
            if state.is_interruption_requested():
                if future:
                    future.cancel()
                raise InterruptException

        future = None

        progress_interrupt(0)
        ys = ys[sampled_indices]
        if is_dask:
            future = dask_client.compute(ys)
            while not future.done():
                progress_interrupt(0)
                time.sleep(0.1)
            if future.cancelled():
                return
            ys = future.result()
        ys[np.isinf(ys)] = np.nan  # remove infs that could ruin display

        progress_interrupt(0)
        return x, ys, sampled_indices

    def on_done(self, res):
        x, ys, sampled_indices = res

        master = self.master
        ys = ys[:, master.data_xsind]

        x, ys = master.calculate(x, ys)

        # shuffle the data before drawing because classes often appear sequentially
        # and the last class would then seem the most prevalent if colored
        indices = list(range(len(sampled_indices)))
        random.Random(master.sample_seed).shuffle(indices)
        sampled_indices = [sampled_indices[i] for i in indices]
        master.sampled_indices = sampled_indices
        master.sampled_indices_inverse = {s: i for i, s in enumerate(master.sampled_indices)}
        master.new_sampling.emit(len(master.sampled_indices))
        ys = ys[indices]  # ys was already subsampled

        master.curves.append((x, ys))

        # add curves efficiently
        for y in ys:
            master.add_curve(x, y, ignore_bounds=True)

        if x.size and ys.size:
            bounding_rect = QtWidgets.QGraphicsRectItem(QtCore.QRectF(
                QtCore.QPointF(bottleneck.nanmin(x), bottleneck.nanmin(ys)),
                QtCore.QPointF(bottleneck.nanmax(x), bottleneck.nanmax(ys))))
            bounding_rect.setPen(QtGui.QPen(QtCore.Qt.NoPen))  # prevents border of 1
            master.curves_cont.add_bounds(bounding_rect)

        master.curves_plotted.append((x, ys))
        master.set_curve_pens()
        master.curves_cont.update()
        master.plot.vb.set_mode_panning()

        self.shown.emit()

    def on_partial_result(self, result):
        pass
