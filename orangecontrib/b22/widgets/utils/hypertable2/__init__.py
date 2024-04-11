import numpy as np
import awkward as ak

import Orange.data

from orangecontrib.b22.widgets.utils.hypertable2.utils import Keys, get_data, \
    rotate_coordinates, otsu, estimate_linear_step_size, estimate_linspace, digitize, closest_indices

from orangecontrib.b22.widgets.utils.hypertable2.utils.ndindexarray import NDIndexArray

from orangecontrib.spectroscopy.utils import values_to_linspace


from scipy import spatial

import itertools, time





class Hypertable:
    def __init__(self, keys, table, indices, linspaces):
        assert(all([Hypertable.has_key(table, key) for key in keys]))

        self.keys = keys
        self.table = table
        self.indices = indices
        self.linspaces = linspaces



    def get_slice_indices(self, indices):
        return NDIndexArray([n for _,_,n in self.linspaces], self.indices)[indices].flatten()
    

    def get_keys_data(self):
        return np.column_stack([key.get_data(self.table) for key in self.keys])
    

    @property
    def X(self):
        return self._get_data(self.table.X)
    
    @property
    def Y(self):
        return self._get_data(self.table.Y)
    
    @property
    def metas(self):
        return self._get_data(self.table.metas)
    

    def _get_data(self, data):
        shape = [n for _,_,n in self.linspaces]
        inds = NDIndexArray(shape, self.indices)

        func = lambda indices, data=data: get_data(indices, data)

        transformed = np.vectorize(func, otypes=[object])(inds.arr)

        return np.stack(transformed.ravel()).reshape(transformed.shape + (-1,))


    @classmethod
    def from_table(cls, table):
        indices = []
        shape = []
        linspaces = []

        keys = calculate_keys(table)

        for key in keys:
            data = key.get_data(table)
            ls = estimate_linspace(data)
            inds = closest_indices(data, ls)

            linspaces.append(ls)
            indices.append(inds)
            shape.append(ls[2])

        indices = np.column_stack(indices).astype(int)

        print(indices)

        return cls(keys, table, indices, linspaces)



    def has_key(cls, key):
        if isinstance(cls, Orange.data.Table):
            return key.variable in cls.domain
        
        if isinstance(cls, Hypertable):
            return Hypertable.has_key(cls.table, key)
        
        raise ValueError
    

    def squash_to(self, attrs):
        keep = list(map(self.get_key_dim, attrs))
        keys = [self.keys[i] for i in keep]
        indices = self.indices[:,keep]
        linspaces = [self.linspaces[i] for i in keep]

        return self.__class__(keys, self.table, indices, linspaces)



    def get_key_dim(self, index):
        if isinstance(index, str):
            for i, k in enumerate(self.keys):
                if k.get_name() == index:
                    return i
                
        if isinstance(index, Orange.data.Variable):
            for i, k in enumerate(self.keys):
                if k.variable == index:
                    return i
                
        if isinstance(index, Keys.Key):
            for i, k in enumerate(self.keys):
                if k == index:
                    return i
                
        raise IndexError(f"key '{index}' not found")
    

    def __getitem__(self, index):
        # Index Cases:
        #  - int:
        #  - List<int>:

        if isinstance(index, list):
            if all(isinstance(i, int) for i in index):
                print("List of ints")
            
            if all(isinstance(i, str) for i in index):
                pass


        # <int> 1 -> RowInstance
        # <slice> :4 -> Table (rows)
        # <list<int>> [1,3,5] -> Table (rows)
        # <str> map_x -> ERROR
        # <Variable> map_x -> ERROR
        # <Tuple> (1,0) -> Value

        if isinstance(index, slice):
            pass

        if isinstance(index, int):
            pass



        return self.table[index]


        #  - str:
        #  - Variable:
        #  - Key: squash_to([key])
        
        #  - List<str>:
        #  - List<Variable>:
        #  - List<Key>: squash_to(keys)
        if isinstance(index, Keys.Key):
            return self.squash_to([index])
        










def predict_angles(coordinates):
    tree = spatial.cKDTree(coordinates)
    _, indices = tree.query(coordinates, k=2)
    closest = coordinates[indices[:, 1], :]
    diffs = np.sort(np.abs(coordinates - closest), axis=1)
    steps = np.median(diffs, axis=0)


    n = len(steps)
    possible_angles = [[
        -np.arctan2(steps[i], steps[j]),
        -np.arctan2(steps[j], steps[i]),
        ] for i in range(n-1) for j in range(i+1, n)]
    
    possible_angles = []

    for i in range(n-1):
        for j in range(i+1, n):
            a = -np.arctan2(steps[i], steps[j])
            b = -np.arctan2(steps[j], steps[i])

            if np.isclose(a, b):
                possible_angles.append([np.mean([a, b])])
            
            else:
                possible_angles.append([a, b])

    # Get all permutations of the angles.
    permutations = itertools.product(*possible_angles)

    # Test each permutation to see which has the smallest linspace.
    # The best values are initialised to an angle of 0.
    best_rotations = None
    best_linspaces = None

    for rotations in permutations:

        transformed = rotate_coordinates(coordinates, rotations).T
        linspaces = map(values_to_linspace, transformed)
        linspaces = [(x0, x1, 1) if np.isclose(x0, x1) else (x0, x1, n) for x0, x1, n in linspaces]

        # Check if current linspaces are less than best_linspaces.
        if best_linspaces is None or np.prod([n for _, _, n in linspaces]) < np.prod([n for _, _, n in best_linspaces]):
            best_linspaces = linspaces
            best_rotations = rotations
    
    return best_rotations



def calculate_continuous_keys(table, continuous):
    coordinates = np.column_stack([
        table.get_column(var) for var in continuous
    ])

    angles = predict_angles(coordinates)
    origin = np.nanmean(coordinates, axis=0)

    funcs = [lambda values, angles=angles, origin=origin, col=col: rotate_coordinates(values, angles, origin=origin)[:,col]
             for col in range(coordinates.shape[1])]
    
    map_keys = [Keys.Key(var) for var in continuous]
    map_id = Keys.CompositeKey(Orange.data.ContinuousVariable("id"), *map_keys)

    meta = {"angles" : angles, "origin" : origin}

    return [Keys.CalculatedKey(var, funcs[i], map_id, meta=meta) for i, var in enumerate(continuous)]



def calculate_discrete_keys(table, discrete):
    return []



def calculate_strings_keys(table, strings):
    return []



def calculate_times_keys(table, times):
    return []



def calculate_keys(table):
    # 1. Select only variables with more than one value.
    continuous = []
    discrete = []
    strings = []
    times = []

    for var in table.domain.metas:
        if len(np.unique(table.get_column(var))) <= 1:
            continue

        if type(var) is Orange.data.ContinuousVariable:
            continuous.append(var)

        elif type(var) is Orange.data.DiscreteVariable:
            discrete.append(var)
        
        elif type(var) is Orange.data.StringVariable:
            strings.append(var)

        elif type(var) is Orange.data.TimeVariable:
            times.append(var)

        else:
            raise Exception

    continuous_keys = calculate_continuous_keys(table, continuous)
    discrete_keys = calculate_discrete_keys(table, discrete)
    strings_keys = calculate_strings_keys(table, strings)
    times_keys = calculate_times_keys(table, times)

    return continuous_keys + discrete_keys + strings_keys + times_keys









if __name__ == "__main__":
    table = Orange.data.Table("C:\\Users\\ixy94928\\Documents\\Pipelines\\Data\\control.tab")
    

    h = Hypertable.from_table(table)
    # <int> 1 -> RowInstance
    # <slice> :4 -> Table (rows)
    # <list<int>> [1,3,5] -> Table (rows)
    # <str> map_x -> ERROR
    # <Variable> map_x -> ERROR
    # <Tuple> (1,0) -> Value
    x = h[[1,0]]
    print(type(x))

    # print(h.X[:4,:4,:4])

    # print(h.squash_to(["map_x", "map_y"]).metas)

    # print(h.squash_to(["map_y", "map_x"]).metas)
    

