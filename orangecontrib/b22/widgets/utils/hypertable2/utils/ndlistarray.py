import numpy as np




class NDListArray:
    def __init__(self, shape):
        arr = np.empty(shape, dtype=object)

        for index in np.ndindex(arr.shape):
            arr[index] = []

        self.__arr = arr


    @property
    def arr(self):
        return self.__arr.copy()


    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.__arr)})"
    

    def __str__(self):
        return str(self.__arr)


    @classmethod
    def from_numpy(cls, arr):
        obj = cls(())
        obj.__arr = arr
        return obj
    

    def flatten(self):
        return np.concatenate(self.__arr.flatten())


    def __getitem__(self, index):
        return self.from_numpy(self.__arr[index])
    

    def __setitem__(self, index, value):
        self.__arr[index] = value

    
    def append(self, index, value):
        self.__arr[index].append(value)

        
    def pop(self, index, i):
        return self.__arr[index].pop(i)