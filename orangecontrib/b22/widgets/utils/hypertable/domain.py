import itertools
import numpy as np

# Only required for representing the class instance as a string.
from pandas import DataFrame 

from scipy import spatial

from orangecontrib.spectroscopy.utils import values_to_linspace




class DimensionDomain:
    #region Magic Methods:
    def __init__(self, dim_keys, real_center, real_area, rotations, pixel_area, squash_metric="mean"):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        dim_keys : np.ndarray (N)
            The dimension names as externally shown (map_x, map_y,
            time, etc).
        real_center : np.ndarray (N)
            The center position of the hypertable in real space.
        real_area : np.ndarray (N)
            The area over which the hypertable covers in real space.
        rotations : np.ndarray ((n/2)*(n-1))
            The angles by which the hypertable must be rotated for it's
            pixel coordinates to coincide with their real positions.
        pixel_area : np.ndarray (N)
            The expected number of pixels in each dimension.

        Notes
        -----
        As the hypertable has rotational freedom, there could be
        confusion as to whether a given coordinate / dimension is
        relative to the hypertable or to the real world. For the sake
        of simplicity, all internal values will be relative to the
        hypertable (unless otherwise stated), and a method for
        converting between the two will be supplied.
        """
        self._dim_keys = dim_keys
        self._real_center = real_center
        self._real_area = real_area
        self._rotations = rotations
        self._pixel_area = pixel_area
        self._squash_metric = squash_metric
    

    def __repr__(self):
        tables = "\n\n".join([str(self.__repr__dimensions_dataframe()),
                            str(self.__repr__rotations_dataframe()),
        ])

        additional = "\n".join([
            f"Dimensions: {self.ndim}",
            f"Pixel Count: {self.size}",
            f"Real Area: {self.real_size}",
        ])

        return tables + "\n\n" + additional
    
    #endregion


    #region Properties:

    @property
    def shape(self) -> tuple:
        return tuple(self.pixel_area)
    
    @property
    def size(self) -> int:
        return np.prod(self.pixel_area)
    
    @property
    def real_size(self) -> int:
        return np.prod(self.real_area)

    @property
    def ndim(self) -> int:
        return self.dim_keys.size

    @property
    def dim_keys(self) -> np.ndarray:
        return self._dim_keys
    
    @property
    def dim_names(self) -> np.ndarray:
        return np.array([f"x{str(i)}" for i in range(self.ndim)])

    @property
    def real_center(self) -> np.ndarray:
        return self._real_center
    
    @property
    def real_area(self) -> np.ndarray:
        return self._real_area

    @property
    def rotation_names(self) -> np.ndarray:
        names = self.dim_names
        n = self.ndim
        return np.array([names[i] + names[j] for i in range(n-1) for j in range(i+1, n)])
    
    @property
    def rotations(self) -> np.ndarray:
        return self._rotations
    
    @property
    def pixel_area(self) -> np.ndarray:
        return self._pixel_area
    
    @property
    def pixel_size(self) -> np.ndarray:
        return self.real_area / self.pixel_area
    
    @property
    def linspaces(self) -> list:
        real_offset = self.real_area / 2.0

        return list(zip(
            self.real_center - real_offset,
            self.real_center + real_offset,
            self.pixel_area
        ))
    
    #endregion


    #region Public Methods:

    def get_dim_key_index(self, dim_key):
        try:
            return np.where(self.dim_keys == dim_key)[0][0]
        except IndexError:
            raise ValueError(f"'{dim_key}' not found in list of dimension keys")
        

    def squash_dimension(self, dim_key):
        index = self.get_dim_key_index(dim_key)

        # Get dimension name and rotation names:
        dim_name = self.dim_names[index]
        rot_names = self.rotation_names
        rotations = self.rotations

        # Remove unneeded rotations first, as dim_names is based on
        # dim_keys.
        for i in range(len(rot_names)-1, -1, -1):
            if dim_name in rot_names[i]:
                rotations = np.delete(rotations, i)

        dim_keys = np.delete(self.dim_keys, index)
        real_center = np.delete(self.real_center, index)
        real_area = np.delete(self.real_area, index)
        pixel_area = np.delete(self.pixel_area, index)

        return type(self)(dim_keys, real_center, real_area, rotations, pixel_area)
    
    #endregion


    #region Protected Methods:
    #endregion


    #region Private Methods:

    def __repr__dimensions_dataframe(self):
        headers = np.array([
            "Dim Name:",
            "Dim Key:",
            "Real Center:",
            "Real Area:",
            "Pixel Area:",
            "Pixel Size:",
            "Real Start:",
            "Real Stop:",
        ])

        data = np.array([
            [
                self.dim_names[i],
                self.dim_keys[i],
                self.real_center[i],
                self.real_area[i],
                self.pixel_area[i],
                self.pixel_size[i],
                self.linspaces[i][0],
                self.linspaces[i][1],
            ] for i in range(self.ndim)
        ])

        return DataFrame(data, columns=headers)
    

    def __repr__rotations_dataframe(self):
        headers = np.array([
            "Plane:",
            "Angle:",
        ])

        data = np.array([
            [
                self.rotation_names[i],
                self.rotations[i],
            ] for i in range(len(self.rotation_names))
        ])

        return DataFrame(data, columns=headers)
    
    #endregion


    #region Class Methods:

    @classmethod
    def from_table(cls, table, dim_keys, squash_metric="mean"):
        print("--- 2")
        # Get the hypercube axis columns.
        coordinates = np.column_stack([
            table.get_column(attr) for attr in dim_keys
        ])
        print("--- 3")

        #coordinates = DimensionDomain.rotate_coordinates(coordinates, [10])

        # Calculate the Euclidean distance between all coordinates.
        tree = spatial.cKDTree(coordinates)
        #dist_matrix = np.linalg.norm(coordinates[:, np.newaxis] - coordinates, axis=2)
        print("--- 4")

        # Remove (by setting to infinity) all distances of 0 so that
        # the any points closest coordinate ISN'T itself.
        _, indices = tree.query(coordinates, k=2)
        # dist_matrix[dist_matrix == 0] = np.inf
        print("--- 5")

        # Get the index of the smallest distance for all coordinates
        # and get said closest coordinate's value.
        closest = coordinates[indices[:, 1], :]
        # closest = coordinates[np.argmin(dist_matrix, axis=0), :]
        print("--- 6")

        # Find the median of the absolute step size.
        diffs = np.sort(np.abs(coordinates - closest), axis=1)
        print("--- 7")

        steps = np.median(diffs, axis=0)
        print("--- 8")

        # Given the step size found, calculate the possible gradients,
        # and use these to calculate the possible angles by which the
        # hypercube has been rotated.
        n = len(steps)
        possible_angles = [[
            -np.arctan2(steps[i], steps[j]),
            -np.arctan2(steps[j], steps[i]),
            ] for i in range(n-1) for j in range(i+1, n)]
        
        print("--- 9")
        
        possible_angles = []

        for i in range(n-1):
            for j in range(i+1, n):
                a = -np.arctan2(steps[i], steps[j])
                b = -np.arctan2(steps[j], steps[i])

                if np.isclose(a, b):
                    possible_angles.append([np.mean([a, b])])
                
                else:
                    possible_angles.append([a, b])
        
        print("--- 10")

        # Get all permutations of the angles.
        permutations = list(itertools.product(*possible_angles))

        print("--- 11")

        # Test each permutation to see which has the smallest linspace.
        # The best values are initialised to an angle of 0.
        best_rotations = None
        best_transformed = None
        best_linspaces = None

        for permutation in permutations:
            rotations = [*permutation]
            transformed = DimensionDomain.rotate_coordinates(coordinates, rotations)
            transposed_transformed = transformed.T
            linspaces = [values_to_linspace(col) for col in transposed_transformed]
            
            linspaces = [(x0, x1, 1) if np.isclose(x0, x1) else (x0, x1, n) for x0, x1, n in linspaces]

            # Check if current linspaces are less than best_linspaces.
            if best_linspaces is None or np.prod([n for _, _, n in linspaces]) < np.prod([n for _, _, n in best_linspaces]):
                best_linspaces = linspaces
                best_rotations = rotations
                best_transformed = transformed
        
        print("--- 12")

        # Calculate center_position, rotations, real_area, and
        # pixel_area from the best values.
        transformed = best_transformed
        center_position = np.mean(best_transformed, axis=0)
        rotations = np.array([-rotation for rotation in best_rotations])
        start, stop, pixel_area = [np.array(x) for x in zip(*best_linspaces)]
        real_area = stop - start

        print("--- 13")

        return cls(np.array(dim_keys), center_position, real_area, rotations, pixel_area, squash_metric=squash_metric)

    #endregion


    #region Static Methods:

    @staticmethod
    def get_subset(pixel_coords, raster_grid):
        #print(pixel_coords)
        #print(raster_grid)
        subset_dict = DimensionDomain.get_mappings(pixel_coords)
        indices = [subset_dict.get(tuple(row), [pixel_coords.shape[0]]) for row in raster_grid]
        return indices


    @staticmethod
    def get_mappings(pixel_coords):
        # Create a dictionary of pixel_coords keys and index values.
        subset_dict = dict()

        for i, row in enumerate(pixel_coords):
            t_row = tuple(row)
            if t_row not in subset_dict:
                subset_dict[t_row] = []
            
            subset_dict[t_row].append(i)

        #subset_dict = {tuple(row): i for i, row in enumerate(pixel_coords)}
        return subset_dict
    

    @staticmethod
    def rasterize_coordinates(data, pixel_coords, raster_grid, squash_metric="mean"):
        """Reorder data from the pixel_coords space to the raster_grid
        space.

        Parameters
        ----------
        data : np.ndarray
            A 2d numpy array where each row holds the data for a different
            pixel coordinate (n, m).
        pixel_coords : np.ndarray
            A 2d numpy array where each row holds the coordinates of some
            row of data in the data array (n, p).
        raster_grid : np.ndarray
            A 2d numpy array where each row holds the coordinates of some
            pixel in a regular grid (q, p).

        Returns
        -------
        np.ndarray
            A 2d numpy array of rearanged data rows, where added rows have
            nan values (q, m).

        Notes
        -----
        This function assumes that:
            - All inputs are 2d numpy arrays,
            - Data and pixel_coords have the same number of rows,
            - Pixel_coords and raster_grid have the same number of cols,
            - Pixel_coords and raster_grid don't contain duplicates,
            - Raster_grid has at least as many rows as pixel_coords,
            - All pixel_coord rows are in raster_grid,
        """
        # For each linspace_coord, get it's index in pixel_coords. Default
        # is the maximum index + 1.
        indices = DimensionDomain.get_subset(pixel_coords, raster_grid)

        # Create and add a nan row to the data, and reshape to match the
        # raster_grid.
        nan_row = np.full((1, data.shape[1]), np.nan)
        new_data = np.concatenate((data, nan_row), axis=0)[indices]

        if squash_metric == "sum":
            new_data = np.nansum(new_data, axis=1)

        elif squash_metric == "median":
            new_data = np.nanmedian(new_data, axis=1)
        
        else:
            new_data = new_data[:,0]

        return new_data


    @staticmethod
    def get_raster_grid(*linspaces):
        """Calculates all grid coordinates given some set of linspaces.

        Given the linspaces (lsx, lsy, ...), calcuates some grid of
        coordinates where each column is a different linspace axis.

        Parameters
        ----------
        *linspaces : [tuple]
            Some collection of linspaces to be used to create a grid of
            coordinates.

        Returns
        -------
        np.ndarray
            A raster grid.
        """
        if len(linspaces) == 0:
            raise Exception("At least one linspace is required.")
        
        if len(linspaces) == 1:
            x0, x1, n = linspaces[0]
            return np.linspace(x0, x1, int(n))[...,None]
        
        linspace_coords = [np.linspace(x0, x1, int(n)) for  x0, x1, n in linspaces]

        return DimensionDomain.linspaces_coords_to_raster_grid(linspace_coords)
    

    @staticmethod
    def linspaces_coords_to_raster_grid(linspaces):
        if len(linspaces) == 1:
            return np.array([linspaces[0]])
        
        lss = linspaces.copy()

        lss[0], lss[1] = lss[1], lss[0]

        grid = np.meshgrid(*lss)
        raster_grid = np.array(list(zip(*[mesh.ravel() for mesh in grid])))

        # Swap columns 0 and 1 back.
        raster_grid[:, [0, 1]] = raster_grid[:, [1, 0]]

        return raster_grid
    

    @staticmethod
    def align_coords_to_raster_grid(raster_grid, pixel_coords, offsets):
        """Aligns pixel coordinates to a grid by finding the nearest grid
        coordinate within a specified offset.

        Parameters
        ----------
        grid_coords : np.ndarray
            The coordinates of the grid points.
        pixel_coords : np.ndarray
            The coordinates of the pixels to be aligned.
        offsets : float or np.ndarray
            The maximum distance a pixel can be from a grid point to be
            considered aligned.

        Returns
        -------
        np.ndarray
            The grid coordinates reordered to match the raster grid.

        Raises
        ------
        Exception
            If a pixel coordinate is aligned to multiple grid coordinates.
        Exception
            If a pixel coordinate is not aligned to any grid coordinates.
        """
        # Create upper and lower coord positions.
        lower = raster_grid - offsets
        upper = raster_grid + offsets

        # Get the raster_grid index for each pixel_coord, where said
        # coord is within the hypercube formed by the raster_grid
        # +/- the offsets given.
        mask = (pixel_coords[:, None] >= lower) & (pixel_coords[:, None] <= upper)
        valid_indices = np.where(mask.all(axis=2))[1]

        # Handle the case where a given row is in multiple actual rows.
        _, counts = np.unique(valid_indices, return_counts=True)
        #if np.any(counts != 1):
        #    raise Exception("This should be unreachable!")

        # Handle the case where a given row is in no actual rows.
        # if pixel_coords.shape[0] > valid_indices.shape[0]:
        #     print(pixel_coords)
        #     print(pixel_coords.shape)
        #     print(valid_indices)
        #     print(valid_indices.shape)
        #     raise Exception("At least one coordinate isn't in the grid.")

        # Return the reordered raster_grid (mimics rounding the
        # pixel_coords to their nearest raster_grid).
        return raster_grid[valid_indices]
        

    @staticmethod
    def rotate_coordinates(coordinates, rotations, origin=None, radians=True):
        """_summary_

        _extended_summary_

        Parameters
        ----------
        coordinates : _type_
            _description_
        rotations : _type_
            _description_
        origin : _type_, optional
            _description_, by default None
        radians : bool, optional
            _description_, by default True

        Returns
        -------
        _type_
            _description_
        """
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
        matrices = []
        index = 0
        for i in range(n-1):
            for j in range(i + 1, n):
                matrix = np.eye(n)
                matrix[[i, j], [i, j]] = np.cos(rotations[index])
                matrix[i, j] = -np.sin(rotations[index])
                matrix[j, i] = np.sin(rotations[index])
                matrices.append(matrix)
                index += 1

        # Translate the coordinates to center on the origin.
        rotated_coordinates = coordinates - origin

        # Rotate the coordinates.
        for rotation_matrix in matrices:
            rotated_coordinates = np.dot(rotated_coordinates, rotation_matrix)

        # Return the rotated coordinates, translated back to their
        # original center position.
        return rotated_coordinates + origin

    #endregion
