import re
import numpy as np

import Orange.data

from orangecontrib.b22.widgets.utils.hypertable.domain import DimensionDomain



class Hypertable:
    def __init__(self, dim_domain, table):
        self.domain = dim_domain
        self.table = table


    def get_coordinates(self):
        coords = np.column_stack([
            self.table.get_column(attr) for attr in self.domain.dim_keys
        ])

        return coords
    

    @classmethod
    def from_table(cls, table, dim_keys, squash_metric="mean"):
        print("--- 1")
        dim_domain = DimensionDomain.from_table(table, dim_keys, squash_metric=squash_metric)
        print("--- 14")

        return cls(dim_domain, table)
    

    def _get_data(self, data, percentage_offset=0.1):
        linspaces = self.domain.linspaces

        raster_grid = DimensionDomain.get_raster_grid(*linspaces)

        # Not quite, but deals with if n is 1, and works decently.
        offsets = np.array([
            (x1 - x0) if n == 1 else
            ((x1 - x0) / (n-1)) * percentage_offset / 2.0
            for x0, x1, n in linspaces
        ])

        coords = self.get_coordinates()

        rotated = DimensionDomain.rotate_coordinates(coords, -self.domain.rotations)

        corrected_coords = DimensionDomain.align_coords_to_raster_grid(raster_grid, rotated, offsets)
        
        new_data = DimensionDomain.rasterize_coordinates(data, corrected_coords, raster_grid, squash_metric=self.domain._squash_metric)

        shape = [n for _, _, n in linspaces] + [-1]
        
        return new_data.reshape(shape)
    

    def squash_dimension(self, dim_key):
        # Uses a squash dimension value to be quicker than redoing
        # everything (about 1/500 of the time taken).
        new_domain = self.domain.squash_dimension(dim_key)
        return type(self)(new_domain, self.table)
    

    def squash_to(self, dim_keys):
        # DOESN'T WORK WHEN DIM_KEY DUPLICATES!!!!!
        # ALSO DOESN'T ORDER THEM!!!!!
        # (Maybe a different method such as 'view' should be used instead?)
        new_domain = self.domain

        for key in self.domain.dim_keys:
            if key not in dim_keys:
                new_domain = new_domain.squash_dimension(key)

        return type(self)(new_domain, self.table)
    

    def get_dim_cols(self):
        dim_vars = {
            "attributes" : [],
            "class_vars" : [],
            "metas" : [],
        }

        for dim_key in self.domain.dim_keys:
            attr = self.table.domain[dim_key]

            if attr in self.table.domain.attributes:
                dim_vars["attributes"].append(attr)

            elif attr in self.table.domain.class_vars:
                dim_vars["class_vars"].append(attr)

            else:
                dim_vars["metas"].append(attr)

        nd = Orange.data.Domain(
            dim_vars["attributes"],
            class_vars=dim_vars["class_vars"], 
            metas=dim_vars["metas"],
        )

        return self.table.transform(nd)


    

    def transform(self, table):
        def split_name(name):
            match = re.search(r'(.*\S)\s*\((\d+)\)$', name)
            if match:
                return match.group(1), int(match.group(2))
            else:
                return name, 0

        def rename_duplicates(primary, secondary):
            new_names = []

            unique = list(set(primary + secondary))

            for name in secondary:
                if name in new_names or name in primary:
                    while name in unique:
                        name_base, number = split_name(name)
                        name = name_base + " (" + str(number+1) + ")"
                
                    unique.append(name)
                
                new_names.append(name)

            return new_names
        

        def rename(domain_a, domain_b):
            names_a = [x.name for x in domain_a]
            names_b = [x.name for x in domain_b]

            new_names = rename_duplicates(names_a, names_b)

            attrs = [domain_b[i].renamed(new_names[i]) for i in range(len(new_names))]

            nd = Orange.data.Domain(attrs)

            return nd


        def get_attr_data(primary, secondary):
            nd = rename(primary.domain, secondary.domain.attributes)
            return secondary.transform(nd)
        
        
        # Assert same number of rows.
        assert(self.table.X.shape[0] == table.X.shape[0])

        

        dim_data = self.get_dim_cols()
        attr_data = get_attr_data(self.table, table)

        new_table = Orange.data.Table.concatenate([dim_data, attr_data], axis=1)

        return type(self)(self.domain, new_table)
        
        
    
    @property
    def X(self):
        return self._get_data(self.table.X)

    @property
    def Y(self):
        return self._get_data(self.table.Y)

    @property
    def metas(self):
        return self._get_data(self.table.metas)
    


    def _get_data(self, data, percentage_offset=0.1):
        linspaces = self.domain.linspaces

        raster_grid = DimensionDomain.get_raster_grid(*linspaces)

        # Not quite, but deals with if n is 1, and works decently.
        offsets = np.array([
            (x1 - x0) if n == 1 else
            ((x1 - x0) / (n-1)) * percentage_offset / 2.0
            for x0, x1, n in linspaces
        ])

        coords = self.get_coordinates()

        rotated = DimensionDomain.rotate_coordinates(coords, -self.domain.rotations)

        corrected_coords = DimensionDomain.align_coords_to_raster_grid(raster_grid, rotated, offsets)
        
        new_data = DimensionDomain.rasterize_coordinates(data, corrected_coords, raster_grid, squash_metric=self.domain._squash_metric)

        shape = [n for _, _, n in linspaces] + [-1]
        
        return new_data.reshape(shape)


    @classmethod
    def from_table_rows(cls, source, row_indices):
        """
        Construct a new table by selecting rows from the source table.

        :param source: an existing table
        :type source: Orange.data.Table
        :param row_indices: indices of the rows to include
        :type row_indices: a slice or a sequence
        :return: a new table
        :rtype: Orange.data.Table
        """
        print(1)
        percentage_offset=0.1

        offsets = np.array([
            (x1 - x0) if n == 1 else
            ((x1 - x0) / (n-1)) * percentage_offset / 2.0
            for x0, x1, n in source.domain.linspaces
        ])

        print(2)

        linspaces = [np.linspace(x0, x1, int(n)) for  x0, x1, n in source.domain.linspaces]
        coords = [linspaces[i][row_indices[i]] for i in range(len(linspaces))]

        print(3)

        subset = DimensionDomain.linspaces_coords_to_raster_grid(coords)

        print(4)
        
        raster_grid = DimensionDomain.get_raster_grid(*source.domain.linspaces)

        print(5)

        rotated = DimensionDomain.rotate_coordinates(source.get_coordinates(), -source.domain.rotations)

        print(6)

        superset = DimensionDomain.align_coords_to_raster_grid(raster_grid, rotated, offsets)

        print(7)

        try:
            indices = [np.where((superset == row).all(axis=1))[0][0] for row in subset]
        except:
            print("ERROR!")
            print([np.where((superset == row).all(axis=1)) for row in subset])
            raise(ValueError("Something is wrong."))
        
        print(8)

        table = source.table[indices]

        print(9)

        dim_domain = DimensionDomain.from_table(table, source.domain._dim_keys, squash_metric=source.domain._squash_metric)

        print(10)

        return cls(dim_domain, table)



        # # Not quite, but deals with if n is 1, and works decently.
        # offsets = np.array([
        #     (x1 - x0) if n == 1 else
        #     ((x1 - x0) / (n-1)) * percentage_offset / 2.0
        #     for x0, x1, n in linspaces
        # ])

        # coords = source.get_coordinates()

        # rotated = DimensionDomain.rotate_coordinates(coords, -source.domain.rotations)

        # corrected_coords = DimensionDomain.align_coords_to_raster_grid(raster_grid, rotated, offsets)


        # raster_grid = DimensionDomain.get_raster_grid(*source.domain.linspaces)
        # coords = source.get_coordinates()

        # print(DimensionDomain.get_subset(coords, raster_grid))
        #new_coords = coords[row_indices]



        # self = cls()
        # self.domain = source.domain
        # with self.unlocked_reference():
        #     self.X = source.X[row_indices]
        #     if self.X.ndim == 1:
        #         self.X = self.X.reshape(-1, len(self.domain.attributes))
        #     self.Y = source.Y[row_indices]
        #     self.metas = source.metas[row_indices]
        #     if self.metas.ndim == 1:
        #         self.metas = self.metas.reshape(-1, len(self.domain.metas))
        #     self.W = source.W[row_indices]
        #     self.name = getattr(source, 'name', '')
        #     self.ids = source.ids[row_indices]
        #     self.attributes = deepcopy(getattr(source, 'attributes', {}))
        # return self


    def get_column(self, column):
        pass



    def __getitem__(self, key):
        if isinstance(key, Orange.data.Variable):
            return self.get_column(key)
        
        return self.from_table_rows(self, key)
        # if isinstance(key, Integral):
        #     return RowInstance(self, key)
        # if not isinstance(key, tuple):
        #     return self.from_table_rows(self, key)

        # if len(key) != 2:
        #     raise IndexError("Table indices must be one- or two-dimensional")

        # row_idx, col_idx = key
        # if isinstance(row_idx, Integral):
        #     if isinstance(col_idx, (str, Integral, Variable)):
        #         col_idx = self.domain.index(col_idx)
        #         var = self.domain[col_idx]
        #         if 0 <= col_idx < len(self.domain.attributes):
        #             val = self.X[row_idx, col_idx]
        #         elif col_idx == len(self.domain.attributes) and self._Y.ndim == 1:
        #             val = self._Y[row_idx]
        #         elif col_idx >= len(self.domain.attributes):
        #             val = self._Y[row_idx,
        #                           col_idx - len(self.domain.attributes)]
        #         else:
        #             val = self.metas[row_idx, -1 - col_idx]
        #         if isinstance(col_idx, DiscreteVariable) and var is not col_idx:
        #             val = col_idx.get_mapper_from(var)(val)
        #         return Value(var, val)
        #     else:
        #         row_idx = [row_idx]

        # # multiple rows OR single row but multiple columns:
        # # construct a new table
        # attributes, col_indices = self.domain._compute_col_indices(col_idx)
        # if attributes is not None:
        #     n_attrs = len(self.domain.attributes)
        #     r_attrs = [attributes[i]
        #                for i, col in enumerate(col_indices)
        #                if 0 <= col < n_attrs]
        #     r_classes = [attributes[i]
        #                  for i, col in enumerate(col_indices)
        #                  if col >= n_attrs]
        #     r_metas = [attributes[i]
        #                for i, col in enumerate(col_indices) if col < 0]
        #     domain = Domain(r_attrs, r_classes, r_metas)
        # else:
        #     domain = self.domain
        # return self.from_table(domain, self, row_idx)

    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            self._set_row(value, key)
            return

        # if len(key) != 2:
        #     raise IndexError("Table indices must be one- or two-dimensional")
        # row_idx, col_idx = key

        # # single row
        # if isinstance(row_idx, Integral):
        #     if isinstance(col_idx, slice):
        #         col_idx = range(*slice.indices(col_idx, self.X.shape[1]))
        #     if not isinstance(col_idx, str) and isinstance(col_idx, Iterable):
        #         col_idx = list(col_idx)
        #     if not isinstance(col_idx, str) and isinstance(col_idx, Sized):
        #         if isinstance(value, (Sequence, np.ndarray)):
        #             values = value
        #         elif isinstance(value, Iterable):
        #             values = list(value)
        #         else:
        #             raise TypeError("Setting multiple values requires a "
        #                             "sequence or numpy array")
        #         if len(values) != len(col_idx):
        #             raise ValueError("Invalid number of values")
        #     else:
        #         col_idx, values = [col_idx], [value]
        #     if isinstance(col_idx, DiscreteVariable) \
        #             and self.domain[col_idx] != col_idx:
        #         values = self.domain[col_idx].get_mapper_from(col_idx)(values)
        #     for val, col_idx in zip(values, col_idx):
        #         if not isinstance(val, Integral):
        #             val = self.domain[col_idx].to_val(val)
        #         if not isinstance(col_idx, Integral):
        #             col_idx = self.domain.index(col_idx)
        #         if col_idx >= 0:
        #             if col_idx < self.X.shape[1]:
        #                 self.X[row_idx, col_idx] = val
        #             elif self._Y.ndim == 1 and col_idx == self.X.shape[1]:
        #                 self._Y[row_idx] = val
        #             else:
        #                 self._Y[row_idx, col_idx - self.X.shape[1]] = val
        #         else:
        #             self.metas[row_idx, -1 - col_idx] = val

        # # multiple rows, multiple columns
        # attributes, col_indices = self.domain._compute_col_indices(col_idx)
        # if col_indices is ...:
        #     col_indices = range(len(self.domain.variables))
        # n_attrs = self.X.shape[1]
        # if isinstance(value, str):
        #     if not attributes:
        #         attributes = self.domain.attributes
        #     for var, col in zip(attributes, col_indices):
        #         val = var.to_val(value)
        #         if 0 <= col < n_attrs:
        #             self.X[row_idx, col] = val
        #         elif col >= n_attrs:
        #             if self._Y.ndim == 1 and col == n_attrs:
        #                 self._Y[row_idx] = val
        #             else:
        #                 self._Y[row_idx, col - n_attrs] = val
        #         else:
        #             self.metas[row_idx, -1 - col] = val
        # else:
        #     attr_cols = np.fromiter(
        #         (col for col in col_indices if 0 <= col < n_attrs), int)
        #     class_cols = np.fromiter(
        #         (col - n_attrs for col in col_indices if col >= n_attrs), int)
        #     meta_cols = np.fromiter(
        #         (-1 - col for col in col_indices if col < 0), int)
        #     if value is None:
        #         value = Unknown

        #     if not isinstance(value, (Real, np.ndarray)) and \
        #             (len(attr_cols) or len(class_cols)):
        #         raise TypeError(
        #             "Ordinary attributes can only have primitive values")
        #     if len(attr_cols):
        #         if self.X.size:
        #             self.X[row_idx, attr_cols] = value
        #     if len(class_cols):
        #         if self._Y.size:
        #             if self._Y.ndim == 1 and np.all(class_cols == 0):
        #                 if isinstance(value, np.ndarray):
        #                     yshape = self._Y[row_idx].shape
        #                     if value.shape != yshape:
        #                         value = value.reshape(yshape)
        #                 self._Y[row_idx] = value
        #             else:
        #                 self._Y[row_idx, class_cols] = value
        #     if len(meta_cols):
        #         if self._metas.size:
        #             self.metas[row_idx, meta_cols] = value




if __name__ == "__main__":
    import Orange.data
    
    table = Orange.data.Table("C:\\Users\\ixy94928\\Documents\\QUASAR\\2023-05-04-05_j77-fixed-caf2-aps-cps\\j77 control si 2x2 binning.0")
    hypertable = Hypertable.from_table(table, ["map_x", "map_y"])

    line = Orange.data.Table("C:\\Users\\ixy94928\\Documents\\line.xyz")

    hypertable = Hypertable.from_table(line, ["map_x", "map_y"])

    print(hypertable[:100,:100])

    x = hypertable.squash_to(["map_x", "map_y"])

    print(hypertable.X.shape)
    print(x.X.shape)

