import time
import bottleneck
import numpy as np

from AnyQt import QtCore, QtGui


import Orange.data
from Orange.widgets.utils.concurrent import TaskState, ConcurrentMixin


from orangecontrib.spectroscopy.utils import apply_columns_numpy


from orangecontrib.b22.visuals.components.curveplot.utils import AVERAGE
from orangecontrib.b22.visuals.components.curveplot.interruptexception import InterruptException




class ShowAverage(QtCore.QObject, ConcurrentMixin):

    shown = QtCore.pyqtSignal()

    def __init__(self, master):
        QtCore.QObject.__init__(self, parent=master)
        ConcurrentMixin.__init__(self)
        self.master = master

    def show(self):
        master = self.master
        master.clear_graph()  # calls cancel
        master.view_average_menu.setChecked(True)
        master.set_pen_colors()
        master.viewtype = AVERAGE
        if not master.data:
            self.shown.emit()
        else:
            color_var = master.feature_color
            self.start(self.compute_averages, master.data, color_var, master.subset_indices,
                       master.selection_group, master.selection_type)

    @staticmethod
    def compute_averages(data: Orange.data.Table, color_var, subset_indices,
                         selection_group, selection_type, state: TaskState):

        def progress_interrupt(i: float):
            if state.is_interruption_requested():
                if future:
                    future.cancel()
                raise InterruptException

        def _split_by_color_value(data, color_var):
            rd = {}
            if color_var is None:
                rd[None] = np.full((len(data.X),), True, dtype=bool)
            else:
                cvd = data.transform(Orange.data.Domain([color_var]))
                feature_values = cvd.X[:, 0]  # obtain 1D vector
                for v in range(len(color_var.values)):
                    v1 = np.in1d(feature_values, v)
                    if np.any(v1):
                        rd[color_var.values[v]] = v1
                nanind = np.isnan(feature_values)
                if np.any(nanind):
                    rd[None] = nanind
            return rd
        
        try:
            import dask
            import dask.array as da
            from orangecontrib.spectroscopy import dask_client
        except ImportError:
            dask = None
            dask_client = None

        results = []

        future = None

        is_dask = dask and isinstance(data.X, dask.array.Array)

        dsplit = _split_by_color_value(data, color_var)
        compute_dask = []
        for colorv, indices in dsplit.items():
            for part in [None, "subset", "selection"]:
                progress_interrupt(0)
                if part is None:
                    part_selection = indices
                elif part == "selection" and selection_type:
                    part_selection = indices & (selection_group > 0)
                elif part == "subset":
                    part_selection = indices & subset_indices
                if np.any(part_selection):
                    if is_dask:
                        subset = data.X[part_selection]
                        compute_dask.extend([da.nanstd(subset, axis=0),
                                             da.nanmean(subset, axis=0)])
                        std, mean = None, None
                    else:
                        std = apply_columns_numpy(data.X,
                                                  lambda x: bottleneck.nanstd(x, axis=0),
                                                  part_selection,
                                                  callback=progress_interrupt)
                        mean = apply_columns_numpy(data.X,
                                                   lambda x: bottleneck.nanmean(x, axis=0),
                                                   part_selection,
                                                   callback=progress_interrupt)
                    results.append([colorv, part, mean, std, part_selection])

        if is_dask:
            future = dask_client.compute(dask.array.vstack(compute_dask))
            while not future.done():
                progress_interrupt(0)
                time.sleep(0.1)
            if future.cancelled():
                return
            computed = future.result()
            for i, lr in enumerate(results):
                lr[2] = computed[i*2]
                lr[3] = computed[i*2+1]

        progress_interrupt(0)
        return results

    def on_done(self, res):
        master = self.master

        ysall = []
        cinfo = []

        x = master.data_x

        ys = np.array([mean[master.data_xsind] for _,_,mean,_,_ in res])
        x, ys = master.calculate(x, ys)
        

        for i, args in enumerate(res):
            colorv, part, _, std, part_selection = args
            
            std = std[master.data_xsind]

            # Apply a mask to remove any non-finite y values.
            mask = np.isfinite(ys[i,:])
            mean = ys[i,mask]
            xi = x[mask]

            if part is None:
                pen = master.pen_normal if np.any(master.subset_indices) else master.pen_subset
            elif part == "selection" and master.selection_type:
                pen = master.pen_selected
            elif part == "subset":
                pen = master.pen_subset
            ysall.append(mean)
            penc = QtGui.QPen(pen[colorv])
            penc.setWidth(3)
            master.add_curve(xi, mean, pen=penc)
            master.add_fill_curve(xi, mean + std, mean - std, pen=penc)
            cinfo.append((colorv, part, part_selection))

        

        master.curves.append((x, ys))
        master.multiple_curves_info = cinfo
        master.curves_cont.update()
        master.plot.vb.set_mode_panning()

        self.shown.emit()

    def on_partial_result(self, result):
        pass