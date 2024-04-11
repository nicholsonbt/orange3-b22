import numpy as np
from functools import reduce
import itertools




def rotation_matrix(i, j, rotation, n):
    matrix = np.eye(n)
    matrix[[i, j], [i, j]] = np.cos(rotation)
    matrix[i, j] = -np.sin(rotation)
    matrix[j, i] = np.sin(rotation)
    return matrix




def rotate_coordinates(coordinates, rotations, origin=None, radians=True):
    # The number of degrees of rotation in n-dimensional space is
    # (n/2)*(n-1).
    n = coordinates.shape[1]
    assert(len(rotations) == n * (n-1) / 2)

    # The point to rotate around.
    if origin is None:
        origin = np.mean(coordinates, axis=0)

    # If angles are measured in degrees, convert to radians.
    if not radians:
        rotations = np.radians(rotations)

    # Calculate the rotation matrices.
    matrices = [rotation_matrix(i, j, rotations[index], n)
                for index, (i, j) in enumerate(itertools.combinations(range(n), 2))]

    # Translate the coordinates to center on the origin.
    rotated_coordinates = coordinates - origin

    # Rotate the coordinates.
    rotated_coordinates = reduce(np.dot, matrices, rotated_coordinates)

    # Return the rotated coordinates, translated back to their original center position.
    return rotated_coordinates + origin




def otsu(steps, n=10):
    def otsu_intraclass_variance(arr, thresh):
        return np.nansum([np.nanmean(cls) * np.nanvar(arr, where=cls) for cls in [arr >= thresh, arr < thresh]])
    
    return min(
        np.linspace(np.nanmin(steps), np.nanmax(steps), n),
        key=lambda th: otsu_intraclass_variance(steps, th),
    )




def estimate_linear_step_size(values):
    sorted_values = np.sort(values)
    steps = np.diff(sorted_values)
    thresh =  otsu(steps)
    steps = steps[steps > thresh]
    return np.nanmean(steps)




def estimate_linspace(values, p=0.2):
    step = estimate_linear_step_size(values)
    start = np.nanmean(values[values < np.nanmin(values) + step*p])
    stop = np.nanmean(values[values > np.nanmax(values) - step*p])
    n = int(np.round((stop - start) / step) + 1)

    return (start, stop, n)




def digitize(values, linspace):
    indices = closest_indices(values, linspace)
    return np.linspace(*linspace)[indices]




def closest_indices(values, linspace):
    start, stop, n = linspace
    step = (stop - start) / (n-1) # Approximate step value from linspace.

    bins = np.linspace(start, stop + step, n+1) - step / 2.0

    return np.searchsorted(bins, values, side='right') - 1




def get_data(indices, data):
    if len(indices) == 0:
        return np.full(data[1].shape, np.nan)
    
    if len(indices) == 1:
        return data[indices[0]]
    
    return np.nanmean(data[indices], axis=0)
