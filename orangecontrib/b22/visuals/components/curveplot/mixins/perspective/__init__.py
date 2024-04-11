from orangecontrib.b22.visuals.components.curveplot.mixins.perspective.cascademixin import CascadeMixin
from orangecontrib.b22.visuals.components.curveplot.mixins.perspective.waterfallmixin import WaterfallMixin





class PerspectiveMixin:
    mixins = [CascadeMixin, WaterfallMixin]

    def __init__(self, *args, **kwargs):
        self.mixins = [mixin(self, *args, **kwargs) for mixin in self.mixins]


    def add_actions(self, menu):
        for mixin in self.mixins:
            mixin.add_actions(menu)


    def setup(self):
        for mixin in self.mixins:
            mixin.setup()


    def calculate(self, x, ys):
        for mixin in self.mixins:
            if mixin.selected_perpective:
                return mixin.calculate(x, ys)
        
        return x, ys
    

    def update_selected(self, selected_mixin):
        for mixin in self.mixins:
            if mixin != selected_mixin:
                mixin.apply(flag=False)
            
