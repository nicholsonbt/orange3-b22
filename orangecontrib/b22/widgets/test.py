import numpy as np

data = np.array([
    [[1, 5]],
    [[2, 6]],
    [[3, 7]],
    [[4, 8]],
])

data = data.reshape((-1, data.shape[-1]))

lower = np.min(data, axis=0)

print(lower)