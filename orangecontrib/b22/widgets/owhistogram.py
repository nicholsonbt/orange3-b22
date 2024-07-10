import numpy as np

import Orange.data
from Orange.widgets import gui, settings, widget
from Orange.widgets.utils.concurrent import ConcurrentWidgetMixin
from Orange.widgets.utils.itemmodels import DomainModel

from orangecontrib.spectroscopy.widgets.gui import lineEditIntRange



def histogram(values, bins):
    hist, bin_edges = np.histogram(values, bins)
    means = (bin_edges[:-1] + bin_edges[1:]) / 2

    return hist, means


def get_decimals(value):
    # 100 -> 0
    # 5 -> 0
    # 0.8 -> 1
    # 0.12 -> 1
    # 0.09 -> 2
    # ...

    std_frm = "{:.0e}".format(value)

    decimals = 2

    if std_frm[2] == "+":
        step = 1

        while value % (step*10) == 0:
            step *= 10
    
    else:
        decimals = int(std_frm[3:])
        step = float(f"1e-{decimals}")

    return max(decimals, 2), step


class OWHistogram(widget.OWWidget, ConcurrentWidgetMixin):
    name = "Histogram"


    class Inputs:
        data = widget.Input("Data", Orange.data.Table, default=True)


    class Outputs:
        data = widget.Output("Data", Orange.data.Table, default=True)



    MIN_BINS = 2
    DEFAULT_BINS = 100
    MAX_BINS = 999
    


    want_main_area = False


    settingsHandler = settings.DomainContextHandler()

    hist_attr = settings.ContextSetting(None)
    bins = settings.Setting(DEFAULT_BINS)

    autocommit = settings.Setting(True)


    hist_model = DomainModel(DomainModel.MIXED, valid_types=Orange.data.ContinuousVariable)


    class Error(widget.OWWidget.Error):
        pass


    class Warning(widget.OWWidget.Warning):
        pass


    def __init__(self):
        widget.OWWidget.__init__(self)
        ConcurrentWidgetMixin.__init__(self)

        self.data = None
        self.hist_attr = None
        self.bins = self.DEFAULT_BINS
        
        gui.comboBox(
            self.controlArea, self, "hist_attr",
            contentsLength=12, searchable=True,
            callback=self.attr_changed, model=self.hist_model
        )

        vbox = gui.vBox(self.controlArea)
        hbox = gui.hBox(vbox)

        gui.widgetLabel(hbox, label="Bins:", labelWidth=50)

        le = lineEditIntRange(hbox, self, "bins", bottom=self.MIN_BINS,
                              top=self.MAX_BINS, default=self.DEFAULT_BINS,
                              callback=self.n_bins_changed)

        hbox.layout().addWidget(le)
        vbox.layout().addWidget(hbox)
        self.controlArea.layout().addWidget(vbox)


        gui.rubber(self.controlArea)

        gui.auto_commit(self.controlArea, self, "autocommit", "Send Data")


    # def set_minmax_size(self):
    #     span = 1

    #     if not (self.data is None or self.hist_attr is None):
    #         domain = Orange.data.Domain([self.hist_attr])
    #         data = self.data.transform(domain)

    #         span = np.nanmax(data.X) - np.nanmin(data.X)

    #     self.min_size = span / self.MAX_BINS
    #     self.max_size = span / self.MIN_BINS
    #     self.default_size = span / self.DEFAULT_BINS


    # def init_bin_size_params(self):
    #     decimals, step = get_decimals(self.min_size)

    #     self.spin_size.setDecimals(decimals)
    #     self.spin_size.setRange(self.min_size, self.max_size)
    #     self.spin_size.setSingleStep(step)
    #     self.spin_size.setValue(step)


    def get_attr_data(self):
        if self.data is None or self.hist_attr is None:
            return None
        
        attr = self.data.domain[self.hist_attr]
        return self.data.get_column(attr)
    
    
    

    def create_histogram(self):
        values = self.get_attr_data()

        if values is None:
            return None

        ys, xs = histogram(values, self.bins)

        vars = [Orange.data.ContinuousVariable(name=str(x)) for x in xs]

        domain = Orange.data.Domain(vars)

        return Orange.data.Table.from_numpy(domain, ys[np.newaxis, :])




    def init_attr_models(self):
        domain = self.data.domain if self.data else None
        self.hist_model.set_domain(domain)

        if not self.hist_attr:
            self.hist_attr = self.hist_model[0] if len(self.hist_model) >= 1 else None

    
    def attr_changed(self):
        self.commit.deferred()


    def n_bins_changed(self):
        self.commit.deferred()



    @Inputs.data
    def set_data(self, data):
        self.data = data
        self.init_attr_models()
        self.commit.now()


    


    @gui.deferred
    def commit(self):
        data = self.create_histogram()
        self.Outputs.data.send(data)




if __name__ == "__main__":  # pragma: no cover
    from Orange.widgets.utils.widgetpreview import WidgetPreview
    collagen = Orange.data.Table("collagen.csv")
    WidgetPreview(OWHistogram).run(set_data=collagen)






"""

import numpy as np
from scipy.signal import argrelextrema
from Orange.data import Domain, Table, DiscreteVariable



attr_name = "850.4969238281251 - 3799.27197265625"
bins = 100
max_clusters = 4



def getOtsuScores(arr, indices, var=np.pi*2):
    score = 0
    
    bounds = [0, *indices, len(arr)-1]
    
    i_s = np.arange(len(arr))
    
    pt = np.sum(arr * i_s)

    for i in range(len(bounds)-1):
        l, r = bounds[i], bounds[i+1]
        h = np.sum(arr[l:r]) / np.sum(arr)
        
        classes = len(indices) + 1
        min_expl = 1 / (classes*var)
        
        p = np.sum(i_s[l:r] * arr[l:r]) / h
        
        if h < min_expl:
            return 0
        
        score += h * (p - pt)**2
    
    return score



def getNextKs(ks, n):
    ks[-1] += 1

    if ks[-1] < n:
        return ks
    
    if len(ks) == 1:
        return None
    
    head = getNextKs(ks[:-1], n-1)
    
    if head is None:
        return None
    
    ks[:-1] = head
    ks[-1] = ks[-2] + 1
    
    return ks



def _otsu(arr, k_indices, k_count):
    ks = np.arange(k_count)
    
    best_indices = []
    best_score = None
    
    n = len(k_indices)
    
    while not ks is None:
        indices = k_indices[ks]
        score = getOtsuScores(arr, indices)
        
        if best_score is None or score > best_score:
            best_score = score
            best_indices = indices
        
        ks = getNextKs(ks, n)
        
    return best_score, best_indices



def multiOtsu(arr, max_ks=None):
    ## Assume the best thresholds will always be local minima.
    allowed_ks = argrelextrema(arr, np.less)[0]
    
    max_ks = min(max_ks, len(allowed_ks))
    
    best_score = best_indices = None
    
    for k_count in range(1, max_ks+1):
        score, indices = _otsu(arr, allowed_ks, k_count)
        
        if best_score is None or score > best_score:
            best_score = score
            best_indices = indices
    
    return best_indices


values = in_data.get_column(in_data.domain[attr_name])

hist, bin_edges = np.histogram(values, bins)

means = (bin_edges[:-1] + bin_edges[1:]) / 2


thresholds = np.concatenate(([np.min(values)], means[multiOtsu(hist, max_clusters-1)], [np.max(values)]))
names = [f"C{cluster+1}" for cluster in range(len(thresholds)+1)]


for i in range(len(thresholds)-1):
    lower = thresholds[i]
    upper = thresholds[i+1]
    
    valid = np.logical_and(values >= lower, values <= upper)
    
    values[valid] = i


out_data = in_data.add_column(DiscreteVariable(name="Cluster", values=names), values, to_metas=True)

"""