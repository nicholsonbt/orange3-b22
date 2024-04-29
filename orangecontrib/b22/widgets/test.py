import numpy as np
import random


class PerlinNoise:
    def __init__(self, seed, amplitude=1, frequency=1, octaves=1, use_mem=True):
        self.seed = random.Random(seed).random()
        self.amplitude = amplitude
        self.frequency = frequency
        self.octaves = octaves
        self.use_mem = use_mem

        if self.use_mem:
            self.memory = dict()


    def get_at(self, x):
        return random.Random(self.seed + x).uniform(-1,1)
    

    def noise(self, x):
        if not self.use_mem:
            return self.get_at(x)

        if x not in self.memory:
            self.memory[x] = self.get_at(x)

        return self.memory[x]
    

    def interp_noise(self, x):
        lower = int(x)
        upper = lower + 1

        v = x - lower

        v0 = self.noise(lower - 1)
        v1 = self.noise(lower)
        v2 = self.noise(upper)
        v3 = self.noise(upper + 1)

        p = (v3 - v2) - (v0 - v1)
        q = (v0 - v1) - p
        r = v2 - v0
        s = v1

        return p * v**3 + q * v**2 + r * v + s
        

    def __call__(self, x):
        frequency = self.frequency
        amplitude = self.amplitude
        result = 0
        for _ in range(self.octaves):
            result += self.interp_noise(x * frequency) * amplitude
            frequency *= 2
            amplitude /= 2

        return result





def noise_1d(xs, seed=None, amplitude=1, frequency=1, octaves=1):
    if seed is None:
        seed = random.random()

    noise = PerlinNoise(seed, amplitude, frequency, octaves, False)

    return [noise(x) for x in xs]


def composites(x, ys, n, lower, upper):
    ws = np.random.random((n, ys.shape[0])) * (upper-lower) + lower
    return np.dot(ws, ys)


def triangle(n):
    return type(n)(n * (n+1) / 2)


import matplotlib.pyplot as plt
import math



class Figure:
    def __init__(self, n, ratio=(1,1)):
        self.rows, self.cols = self.calculate_rows_cols(n, ratio)
        self.fig, self.axs = plt.subplots(self.rows, self.cols)


    def calculate_rows_cols(self, n, ratio=1):
        w_ratio, h_ratio = ratio

        k = math.sqrt(n / (w_ratio * h_ratio))
        w = int(round(w_ratio * k, 0))
        h = math.ceil(n / w)

        return h, w
    

    def __getitem__(self, index):
        row, col = self.get_row_col(index)
        return self.axs[row, col]


    def get_row_col(self, index):
        row = index // self.rows
        col = index % self.rows

        return row, col


if __name__ == "__main__":
    from sklearn.decomposition import FastICA

    n = 4
    m = 1000
    seed = 0

    x = np.linspace(0, 100, 1024)

    ys = np.array([noise_1d(x, seed=i+seed) for i in range(n)])


    data = composites(x, ys, m, 0, 1)

    data /= data.std(axis=0)

    ica = FastICA(n_components=n)
    ica.fit(data)

    components = ica.components_

    fig = Figure(2 + 2*triangle(n-1))

    for i in range(n):
        y = ys[i,:]
        fig[0].plot(x, y, label=f"y{i}")
        fig[0].title.set_text("Independent Sources:")

    for i in range(components.shape[0]):
        c = components[i,:]
        fig[1].plot(x, c, label=f"c{i}")
        fig[1].title.set_text("Mixed Signals:")

    i = 2
    for j in range(ys.shape[0]-1):
        for k in range(j+1, ys.shape[0]):
            fig[i].scatter(ys[j], ys[k])
            fig[i].title.set_text(f"Gaussiananity of sources {j} and {k}:")
            i+=1

    for j in range(ys.shape[0]-1):
        for k in range(j+1, ys.shape[0]):
            fig[i].scatter(data[j], data[k])
            fig[i].title.set_text(f"Gaussiananity of mixed {j} and {k}:")
            i+=1

    fig[0].legend()
    fig[1].legend()
    plt.tight_layout()
    plt.show()








# import numpy as np
# from scipy import signal

# np.random.seed(0)
# n_samples = 2000
# k = 3
# time = np.linspace(0, 8, n_samples)

# s1 = np.sin(2 * time)  # Signal 1 : sinusoidal signal
# s2 = np.sign(np.sin(3 * time))  # Signal 2 : square signal
# s3 = signal.sawtooth(2 * np.pi * time)  # Signal 3: saw tooth signal

# S = np.c_[s1, s2, s3]
# S += 0.2 * np.random.normal(size=S.shape)  # Add noise



# # S /= S.std(axis=0)  # Standardize data

# # print(S)
# # Mix data
# A = np.array([[1, 1, 1], [0.5, 2, 1.0], [1.5, 1.0, 2.0], [1, 2, 0.1]])  # Mixing matrix
# X = np.dot(S, A.T)  # Generate observations

# from sklearn.decomposition import PCA, FastICA

# # Compute ICA
# ica = FastICA(n_components=k, whiten="arbitrary-variance")
# S_ = ica.fit_transform(X)  # Reconstruct signals
# A_ = ica.mixing_  # Get estimated mixing matrix

# # We can `prove` that the ICA model applies by reverting the unmixing.
# # assert np.allclose(X, np.dot(S_, A_.T) + ica.mean_)

# # For comparison, compute PCA
# pca = PCA(n_components=k)
# H = pca.fit_transform(X)  # Reconstruct signals based on orthogonal components

# import matplotlib.pyplot as plt

# plt.figure()

# models = [X, S, S_, H]
# names = [
#     "Observations (mixed signal)",
#     "True Sources",
#     "ICA recovered signals",
#     "PCA recovered signals",
# ]
# colors = ["red", "steelblue", "orange"]

# for ii, (model, name) in enumerate(zip(models, names), 1):
#     plt.subplot(4, 1, ii)
#     plt.title(name)
#     for sig, color in zip(model.T, colors):
#         plt.plot(sig, color=color)

# plt.tight_layout()
# plt.show()