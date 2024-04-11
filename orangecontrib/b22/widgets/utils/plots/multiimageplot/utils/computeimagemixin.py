
import numpy as np

from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItemFactory
from orangecontrib.b22.widgets.utils.plots.multiimageplot.legends import Legend

from orangecontrib.spectroscopy.widgets.owhyper import UndefinedImageException, InterruptException, \
    ImageTooBigException, IMAGE_TOO_BIG, split_to_size





class ComputeImageMixin:
    @staticmethod
    def compute_image(index, image_type, plane, image_values, image_values_fixed_levels, state):
        if plane is None or plane.table is None:
            raise UndefinedImageException

        def progress_interrupt(i: float):
            if state.is_interruption_requested():
                raise InterruptException

        class Result():
            pass
        res = Result()

        progress_interrupt(0)

        print(f"compute_image ({index})")

        res.index = index
        res.image_type = image_type
        res.domain = plane.domain
        res.coords = plane.get_coordinates()
        res.image_values_fixed_levels = image_values_fixed_levels

        progress_interrupt(0)

        if plane.domain.size > IMAGE_TOO_BIG:
            raise ImageTooBigException(plane.domain.shape)

        channels = image_values(plane.table[:1]).X.shape[1]

        d = np.full((*plane.domain.shape, channels), float("nan"))
        res.d = d

        step = 100

        print("loop")

        for slice_x in split_to_size(plane.domain.shape[0], step):
            print(f"X: {slice_x}")
            for slice_y in split_to_size(plane.domain.shape[1], step):
                print(f"Y: {slice_y}")
                plane_part = plane[slice_x, slice_y]
                print(1)

                img_vals = image_values(plane_part.table)
                print(2)

                part = plane_part.transform(img_vals).X
                print(3)

                d[slice_x, slice_y, :] = part
                print(4)

                progress_interrupt(0)
                state.set_partial_result(res)
                print("-")

        progress_interrupt(0)

        print(f"computed")

        return res


    def draw(self, res, finished=False):
        index = res.index

        print("draw")

        imdata = res.d
        domain = res.domain
        image_type = res.image_type
        coords = res.coords
        image_values_fixed_levels = res.image_values_fixed_levels
        

        if len(self.order) <= index:
            raise Exception("ERROR!")
        
        image = ImageItemFactory.generate(image_type)
        legend = Legend(self, index)

        #image.set_data(imdata, domain, image_values_fixed_levels)

        print("images")

        #self.images.images[index] = image
        self.images.images[index].set_data(imdata, domain, coords, image_values_fixed_levels)
        self.legends.legends[index] = legend
        legend.added.emit()

        if finished:
            self.image_updated.emit()

        print("done")


    def on_done(self, res):
        self.draw(res, finished=True)


    def on_partial_result(self, res):
        self.draw(res)


    def on_exception(self, ex: Exception):
        if isinstance(ex, InterruptException):
            return

        if isinstance(ex, ImageTooBigException):
            self.parent.parent.Error.image_too_big(ex.args[0][0], ex.args[0][1])
        #     self.image_updated.emit()
        # elif isinstance(ex, UndefinedImageException):
        #     self.image_updated.emit()
        else:
            raise ex
