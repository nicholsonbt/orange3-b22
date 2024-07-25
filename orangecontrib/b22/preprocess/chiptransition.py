import bottleneck
import numpy as np

from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
from scipy.spatial.qhull import ConvexHull, QhullError
from scipy.signal import savgol_filter
from sklearn.preprocessing import normalize as sknormalize

from extranormal3 import normal_xas, extra_exafs

import Orange
import Orange.data
from Orange.data import ContinuousVariable
from Orange.preprocess.preprocess import Preprocess

from orangecontrib.spectroscopy.data import getx

from orangecontrib.spectroscopy.preprocess.integrate import Integrate
from orangecontrib.spectroscopy.preprocess.emsc import EMSC
from orangecontrib.spectroscopy.preprocess.transform import Absorbance, Transmittance, \
    CommonDomainRef
from orangecontrib.spectroscopy.preprocess.utils import SelectColumn, CommonDomain, \
    CommonDomainOrder, CommonDomainOrderUnknowns, nan_extend_edges_and_interpolate, \
    remove_whole_nan_ys, interp1d_with_unknowns_numpy, interp1d_with_unknowns_scipy, \
    interp1d_wo_unknowns_scipy, edge_baseline, MissingReferenceException, \
    WrongReferenceException, replace_infs, transform_to_sorted_features, PreprocessException, \
    linear_baseline






class ChipTransition(Preprocess):

    def __init__(self, positions=[]):
        self.positions = positions

    def __call__(self, in_data):
        if len(self.positions) == 0:
            return in_data.copy()
        
        wavenumbers = np.array([float(attr.name) for attr in in_data.domain.attributes])
        
        order = np.argsort(wavenumbers)
        rev_order = np.argsort(order)
        
        diffs = np.diff(in_data.X[:, order], axis=1)

        diffs[:, self.positions] = 0

        diffs = np.hstack((diffs, np.zeros((diffs.shape[0], 1))))

        out_data = in_data.copy()
        out_data.X = np.cumsum(diffs, axis=1)[:, rev_order]

        return out_data

    

    @staticmethod
    def calculate_indices(ys, alpha, beta):
        # Calculate the mean value for each column.
        mean_row = np.nanmean(ys, axis=0)

        # Get the moving sum of the differences (such that noise is
        # minimised).
        diff = np.diff(mean_row)
        diff_sum = np.abs(diff[:-1] + diff[1:])

        # Set the fist and last moving diff sum values to 0.
        diff_sum[[0, -1]] = 0

        # Get the standard deviation of the moving diff sum array.
        std = np.std(diff_sum)

        # If a moving diff sum value is less than alpha * std, set it
        # to 0. This aims to remove noise without removing actual chip
        # transitions.
        diff_sum[diff_sum < alpha * std] = 0

        # Calculate the difference of the moving diff sum array.
        diff_sum_2 = np.abs(np.diff(diff_sum))

        noise_mask = np.hstack((True, diff_sum_2 > beta * std))

        diff_sum[noise_mask] = 0

        indices = np.where(diff_sum > 0)

        return indices[0]

        



