from AnyQt import QtCore, QtGui, QtWidgets

import Orange.data
from Orange.widgets import settings, gui

from orangecontrib.spectroscopy.widgets.gui import lineEditDecimalOrNone, \
    pixels_to_decimals, float_to_str_decimals
from orangecontrib.spectroscopy.widgets.owhyper import _color_palettes, \
    color_palette_model, get_levels, color_palette_table

from orangecontrib.b22.widgets.utils.plots.multiimageplot.items.imageitems import ImageItemFactory



class ImageColourSettingMixin:
    threshold_low = settings.Setting(0.0, schema_only=True)
    threshold_high = settings.Setting(1.0, schema_only=True)
    level_low = settings.Setting(None, schema_only=True)
    level_high = settings.Setting(None, schema_only=True)
    palette_index = settings.Setting(0)


    def __init__(self):
        self.fixed_levels = None  # fixed level settings for categoric data


    def add_choose_colour_settings(self, menu):
        choose_colour_settings = QtWidgets.QWidgetAction(self)

        box = gui.vBox(None)
        box.setContentsMargins(0, 0, 0, 5)
        self.color_cb = gui.comboBox(box, self, "palette_index", label="Color:",
                                     labelWidth=50, orientation=QtCore.Qt.Horizontal)
        self.color_cb.setIconSize(QtCore.QSize(64, 16))
        palettes = _color_palettes
        model = color_palette_model(palettes, self.color_cb.iconSize())
        model.setParent(self)
        self.color_cb.setModel(model)
        self.palette_index = min(self.palette_index, len(palettes) - 1)
        self.color_cb.activated.connect(self.update_color_schema)

        form = QtWidgets.QFormLayout(
            formAlignment=QtCore.Qt.AlignLeft,
            labelAlignment=QtCore.Qt.AlignLeft,
            fieldGrowthPolicy=QtWidgets.QFormLayout.AllNonFixedFieldsGrow
        )

        def limit_changed():
            self.update_levels()
            self.reset_thresholds()

        self._level_low_le = lineEditDecimalOrNone(box, self, "level_low", callback=limit_changed)
        self._level_low_le.validator().setDefault(0)
        form.addRow("Low limit:", self._level_low_le)

        self._level_high_le = lineEditDecimalOrNone(box, self, "level_high", callback=limit_changed)
        self._level_high_le.validator().setDefault(1)
        form.addRow("High limit:", self._level_high_le)

        self._threshold_low_slider = lowslider = gui.hSlider(
            box, self, "threshold_low", minValue=0.0, maxValue=1.0,
            step=0.05, ticks=True, intOnly=False,
            createLabel=False, callback=self.update_levels)
        self._threshold_high_slider = highslider = gui.hSlider(
            box, self, "threshold_high", minValue=0.0, maxValue=1.0,
            step=0.05, ticks=True, intOnly=False,
            createLabel=False, callback=self.update_levels)

        form.addRow("Low:", lowslider)
        form.addRow("High:", highslider)
        box.layout().addLayout(form)

        choose_colour_settings.setDefaultWidget(box)
        menu.addAction(choose_colour_settings)

        self.update_legend_visible()


    def update_legend_visible(self):
        pass
        # if self.fixed_levels is not None or self.parent.value_type == 2:
        #     print("Legend now invisible")
        # else:
        #     print("Legend now visible")


    def update_levels(self):
        if not self.data:
            return

        ### Make scatter friendly!!!
        if self.fixed_levels is not None:
            levels = list(self.fixed_levels)

        else:
            imdata = self.linked_image.get_data()

            if imdata is not None and imdata.ndim == 2:
                levels = get_levels(imdata)
            elif imdata is not None and imdata.shape[2] == 1:
                levels = get_levels(imdata[:, :, 0])
            elif imdata is not None and imdata.shape[2] == 3:
                return
            else:
                levels = [0, 255]
        ###

        prec = pixels_to_decimals((levels[1] - levels[0])/1000)

        rounded_levels = [float_to_str_decimals(levels[0], prec),
                          float_to_str_decimals(levels[1], prec)]

        self._level_low_le.validator().setDefault(rounded_levels[0])
        self._level_high_le.validator().setDefault(rounded_levels[1])

        self._level_low_le.setPlaceholderText(rounded_levels[0])
        self._level_high_le.setPlaceholderText(rounded_levels[1])

        enabled_level_settings = self.fixed_levels is None
        self._level_low_le.setEnabled(enabled_level_settings)
        self._level_high_le.setEnabled(enabled_level_settings)
        self._threshold_low_slider.setEnabled(enabled_level_settings)
        self._threshold_high_slider.setEnabled(enabled_level_settings)

        if self.fixed_levels is not None:
            self.linked_image.setLevels(self.fixed_levels)
            return

        # if not self.threshold_low < self.threshold_high:
        #     # TODO this belongs here, not in the parent
        #     self.parent.Warning.threshold_error()
        #     return
        # else:
        #     self.parent.Warning.threshold_error.clear()

        ll = float(self.level_low) if self.level_low is not None else levels[0]
        lh = float(self.level_high) if self.level_high is not None else levels[1]

        ll_threshold = ll + (lh - ll) * self.threshold_low
        lh_threshold = ll + (lh - ll) * self.threshold_high

        self.linked_image.setLevels([ll_threshold, lh_threshold])
        self.set_range(ll_threshold, lh_threshold)

    def update_color_schema(self):
        if not self.data:
            return
        
        # image_type = ImageItemFactory.get(self.linked_image)

        #print(self.linked_image.imdata)

        # if self.parent.value_type == 1:
        #     dat = self.data.domain[self.parent.attr_value]
        #     if isinstance(dat, Orange.data.DiscreteVariable):
        #         # use a defined discrete palette
        #         self.linked_image.setLookupTable(dat.colors)
        #         return

        # # use a continuous palette
        data = self.color_cb.itemData(self.palette_index, role=QtCore.Qt.UserRole)
        _, colors = max(data.items())
        cols = color_palette_table(colors)
        self.linked_image.setLookupTable(cols)
        self.set_colors(cols)


    def reset_thresholds(self):
        self.threshold_low = 0.
        self.threshold_high = 1.
    

    def update(self):
        self.update_levels()
        self.update_color_schema()