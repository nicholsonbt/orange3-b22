import numpy as np

from AnyQt import QtCore, QtWidgets



def improved_binning(values, step_size, k):
    lower = np.min(values) - step_size
    upper = np.max(values) + step_size
    n = int(np.round((upper - lower) / step_size, decimals=0)) + 2

    ls = np.linspace(lower, upper, n)

    sub_step = step_size / k

    min_i_s = []
    min_c = None
    
    for i in range(k):
        edges = ls + sub_step * i
        digitized = np.digitize(values, edges)
        count = np.unique(digitized).size

        if min_c is None or min_c > count:
            min_c = count
            min_i_s = [i]

        elif min_c == count:
            min_i_s.append(i)

    i = np.median(min_i_s)
    edges = ls + sub_step * i
    digitized = np.digitize(values, edges)

    left = edges[digitized-1]
    right = edges[digitized]

    return (left + right) / 2




def bin_combine(xs, ys, n=10):
    order = np.argsort(xs, axis=1)

    new_xs = np.take_along_axis(xs, order, axis=1)
    new_ys = np.take_along_axis(ys, order, axis=1)
    step_sizes = np.median(np.diff(new_xs, axis=1), axis=1)
    step_size = np.median(step_sizes)

    binned = improved_binning(xs.flatten(), step_size / n, n).reshape(xs.shape)

    new_xs, inverse = np.unique(binned, return_inverse=True)
    indices = inverse.reshape(binned.shape)

    new_ys = np.full((xs.shape[0], new_xs.size), fill_value=np.nan)

    new_ys[np.arange(xs.shape[0])[:, np.newaxis], indices] = ys

    return new_xs, new_ys



class FormBox(QtWidgets.QWidget):
    def __init__(self, parent,
                 fieldGrowthPolicy=QtWidgets.QFormLayout.FieldsStayAtSizeHint,
                 formAlignment=QtCore.Qt.AlignRight,
                 labelAlignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                 **kwargs):
        
        QtWidgets.QWidget.__init__(self, parent)

        self.form = QtWidgets.QFormLayout(
            fieldGrowthPolicy=fieldGrowthPolicy,
            formAlignment=formAlignment,
            labelAlignment=labelAlignment,
            **kwargs
        )

        self.setLayout(self.form)



    def addRow(self, label, widget):
        self.form.addRow(label, widget)




class FormAction(QtWidgets.QWidgetAction):
    def __init__(self, parent, **kwargs):
        QtWidgets.QWidgetAction.__init__(self, parent)

        self.form_box = FormBox(parent)

        self.setDefaultWidget(self.form_box)


    def addRow(self, label, widget):
        self.form_box.addRow(label, widget)
