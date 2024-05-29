from Orange.widgets import widget, settings, gui

from Orange import distance
import Orange.data

import numpy as np

from scipy.sparse import issparse
import bottleneck as bn

from AnyQt import QtCore, QtGui, QtWidgets


from Orange.widgets.unsupervised.owdistances import MetricDefs, InterruptException

from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.data.util import get_unique_names



class DistanceRunner:
    @staticmethod
    def run(data, metric, normalized_dist, arg, state):
        if data is None:
            return None

        if arg is None:
            return None

        def callback(i: float) -> bool:
            state.set_progress_value(i)
            if state.is_interruption_requested():
                raise InterruptException

        state.set_status("Calculating...")
        kwargs = {"impute": True, "callback": callback}

        if metric.supports_normalization and normalized_dist:
            kwargs["normalize"] = True

        if isinstance(arg, int):
            kwargs["axis"] = 1 - arg
            return metric(data, **kwargs)
        
        return metric(data, arg, **kwargs)



class OWImprovedDistances(widget.OWWidget, ConcurrentWidgetMixin):
    name = "Improved Distances"
    description = "Compute a matrix of pairwise distances."
    icon = "icons/Distance.svg"
    keywords = "distances"
    id = "orangecontrib.b22.widgets.owimproveddistances.OWImprovedDistances"


    class Inputs:
        data = widget.Input("Data", Orange.data.Table, default=True)
        refs = widget.Input("References", Orange.data.Table)


    class Outputs:
        distances = widget.Output("Distances", Orange.misc.DistMatrix, dynamic=False)
        data = widget.Output("Data", Orange.data.Table)


    settings_version = 1

    axis: int = settings.Setting(0)
    metric_id: int = settings.Setting(0)
    autocommit: bool = settings.Setting(True)

    want_main_area = False
    resizing_enabled = False


    class Error(widget.OWWidget.Error):
        no_continuous_features = widget.Msg("No numeric features")
        no_binary_features = widget.Msg("No binary features")
        dense_metric_sparse_data = widget.Msg("{} requires dense data.")
        distances_memory_error = widget.Msg("Not enough memory")
        distances_value_error = widget.Msg("Problem in calculation:\n{}")
        data_too_large_for_mahalanobis = widget.Msg(
            "Mahalanobis handles up to 1000 {}.")


    class Warning(widget.OWWidget.Warning):
        ignoring_discrete = widget.Msg("Ignoring categorical features")
        ignoring_nonbinary = widget.Msg("Ignoring non-binary features")
        unsupported_sparse = widget.Msg("Some metrics don't support sparse data\n"
                                 "and were disabled: {}")
        imputing_data = widget.Msg("Missing values were imputed")
        no_features = widget.Msg("Data has no features")


    def __init__(self):
        widget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

        self.data = None
        self.refs = None

        self.axis_btns = gui.radioButtons(
            self.controlArea, self, "axis", ["Rows", "Columns"],
            box="Compare", orientation=QtCore.Qt.Horizontal, callback=self._invalidate
        )

        box = gui.hBox(self.controlArea, "Distance Metric")
        self.metric_buttons = QtWidgets.QButtonGroup()
        width = 0
        for i, metric in enumerate(MetricDefs.values()):
            if i % 6 == 0:
                vb = gui.vBox(box)
            b = QtWidgets.QRadioButton(metric.name)
            b.setChecked(self.metric_id == metric.id)
            b.setToolTip(metric.tooltip)
            vb.layout().addWidget(b)
            width = max(width, b.sizeHint().width())
            self.metric_buttons.addButton(b, metric.id)
        for b in self.metric_buttons.buttons():
            b.setFixedWidth(width)

        self.metric_buttons.idClicked.connect(self._metric_changed)

        gui.auto_apply(self.buttonsArea, self, "autocommit")


    @Inputs.data
    def set_data(self, data):
        self.cancel()
        self.data = data
        self.refresh_radios()
        self.commit.now()


    @Inputs.refs
    def set_refs(self, refs):
        self.cancel()
        self.refs = refs

        if refs is None:
            self.axis_btns.setEnabled(True)
        else:
            self.axis_btns.setEnabled(False)

        self.commit.now()



    def _metric_changed(self, id_):
        self.metric_id = id_
        self._invalidate()


    def refresh_radios(self):
        sparse = self.data is not None and issparse(self.data.X)
        unsupported_sparse = []
        for metric in MetricDefs.values():
            button = self.metric_buttons.button(metric.id)
            no_sparse = sparse and not metric.metric.supports_sparse
            button.setEnabled(not no_sparse)
            if no_sparse:
                unsupported_sparse.append(metric.name)
        self.Warning.unsupported_sparse(", ".join(unsupported_sparse),
                                        shown=bool(unsupported_sparse))

    @gui.deferred
    def commit(self):
        if self.data:
            self.compute_distances(self.data, self.refs)

    def compute_distances(self, data, refs):
        def _check_sparse(data):
            # pylint: disable=invalid-sequence-index
            if issparse(data.X) and not metric.supports_sparse:
                self.Error.dense_metric_sparse_data(metric_def.name)
                return False
            return True

        def _fix_discrete(data):
            if data.domain.has_discrete_attributes() \
                    and metric is not distance.Jaccard \
                    and (issparse(data.X) and getattr(metric, "fallback", None)
                         or not metric.supports_discrete
                         or self.axis == 1):
                if not data.domain.has_continuous_attributes():
                    self.Error.no_continuous_features()
                    return False
                self.Warning.ignoring_discrete()
                data = distance.remove_discrete_features(data, to_metas=True)
            return True

        def _fix_nonbinary(data):
            if metric is distance.Jaccard and not issparse(data.X):
                nbinary = sum(a.is_discrete and len(a.values) == 2
                              for a in data.domain.attributes)
                if not nbinary:
                    self.Error.no_binary_features()
                    return False
                elif nbinary < len(data.domain.attributes):
                    self.Warning.ignoring_nonbinary()
                    data = distance.remove_nonbinary_features(data,
                                                              to_metas=True)
            return True

        def _fix_missing(data):
            if not metric.supports_missing and bn.anynan(data.X):
                self.Warning.imputing_data()
                data = distance.impute(data)
            return True

        def _check_tractability(data):
            if metric is distance.Mahalanobis:
                if self.axis == 0:
                    # when computing distances by columns, we want < 1000 rows
                    if len(data) > 1000:
                        self.Error.data_too_large_for_mahalanobis("rows")
                        return False
                else:
                    if len(data.domain.attributes) > 1000:
                        self.Error.data_too_large_for_mahalanobis("columns")
                        return False
            return True

        def _check_no_features(data):
            if len(data.domain.attributes) == 0:
                self.Warning.no_features()
            return True


        metric_def = MetricDefs[self.metric_id]
        metric = metric_def.metric
        self.clear_messages()
        if data is not None:
            for check in (_check_sparse, _check_tractability,
                          _check_no_features,
                          _fix_discrete, _fix_missing, _fix_nonbinary):
                if not check(data):
                    data = None
                    break

        if refs is not None:
            for check in (_check_sparse, _check_tractability,
                          _check_no_features,
                          _fix_discrete, _fix_missing, _fix_nonbinary):
                if not check(refs):
                    refs = None
                    break
        else:
            refs = self.axis

        self.start(DistanceRunner.run, data, metric,
                   metric_def.normalize, refs)

    def on_partial_result(self, _):
        pass

    def on_done(self, result: Orange.misc.DistMatrix):
        assert isinstance(result, Orange.misc.DistMatrix) or result is None
        self.Outputs.distances.send(result)

        MAX_COLS = 5

        if result.shape[1] <= MAX_COLS:
            out_data = self.data.copy()
            
            for i in range(result.shape[1]):
                data = result[:,i]
                variable = Orange.data.ContinuousVariable(get_unique_names(out_data.domain, f"K {i+1}"))
                out_data = out_data.add_column(variable, data, to_metas=True)
            
            self.Outputs.data.send(out_data)


    def on_exception(self, ex):
        if isinstance(ex, ValueError):
            self.Error.distances_value_error(ex)
        elif isinstance(ex, MemoryError):
            self.Error.distances_memory_error()
        elif isinstance(ex, InterruptException):
            pass
        else:
            raise ex
        

    def onDeleteWidget(self):
        self.shutdown()
        super().onDeleteWidget()


    def _invalidate(self):
        self.commit.deferred()

    




if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWImprovedDistances).run(set_data=collagen)
