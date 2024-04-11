import numpy as np




class Key:
    def __init__(self, variable, range_func=None):
        self.variable = variable

        if not range_func:
            range_func = lambda self, table: np.unique(self.get_values(table))
        self.range_func = range_func


    def get_name(self):
        return self.variable.name
    

    def get_data(self, table):
        return table.get_column(self.variable)
    

    def get_values(self, table):
        data = self.get_data(table)

        for i, val in enumerate(data):
            data[i] = self.variable.repr_val(val)

        return data
    

    def get_range(self, table):
        return self.range_func(self, table)
    

    def __repr__(self, *args):
        repr_args = ", ".join([repr(arg) for arg in args])
        return f"{self.__class__.__name__}({repr(self.variable)}, {repr_args})" 
    

    def __str__(self):
        return str(self.variable)
    

    def leaf_str(self):
        return str(self.variable)




class CompositeKey(Key):
    def __init__(self, variable, *keys, range_func=None):
        Key.__init__(self, variable, range_func=range_func)
        self.keys = keys


    def get_data(self, table):
        return np.column_stack([key.get_data(table) for key in self.keys])
    
    
    def get_values(self, table):
        data = self.get_data(table)

        for i, row in enumerate(data):
            for j, val in enumerate(row):
                self.keys[j].repr_val(val)
                data[i, j] = val
    

    def __repr__(self):
        return Key.__repr__(self, *self.keys)
    

    def __str__(self):
        return f"{Key.__str__(self)}: {self.leaf_str()}"
    

    def leaf_str(self):
        return "[" + ", ".join([key.leaf_str() for key in self.keys]) + "]"
    




class CalculatedKey(Key):
    def __init__(self, variable, func, key, range_func=None, meta=None):
        Key.__init__(self, variable, range_func=range_func)
        self.func = func
        self.key = key
        self.meta = meta
    

    def get_data(self, table):
        return self.func(self.key.get_data(table))
    
    
    def __repr__(self):
        return Key.__repr__(self, self.func, self.key)
    

    def __str__(self):
        return f"{Key.__str__(self)}: {self.leaf_str()}"
    

    def leaf_str(self):
        return f"f({self.key.leaf_str()})"
