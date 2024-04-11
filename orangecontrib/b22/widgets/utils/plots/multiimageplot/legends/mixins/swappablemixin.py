from AnyQt import QtCore, QtGui

from orangecontrib.spectroscopy.widgets.owhyper import ImageColorLegend




class SwappableMixin:
    def __init__(self):
        self.swap_meta = {
            "pos" : None,
            "scenePos" : None,
            "distance" : None,
            "leftDown" : None,
            "pen" : None,
        }

        self.setFlag(self.ItemIsMovable)
        self.setup_meta()


    def update_positions(self):
        for legend in self.legends:
            legend.update_position()

    def update_position(self):
        self.swap_meta["pos"] = self.pos()
        self.swap_meta["scenePos"] = self.scenePos()


    def setup_meta(self):
        self.update_position()
        self.swap_meta["distance"] = 0
        self.swap_meta["leftDown"] = False


    def closest_index(self, pos):
        best_i = None
        best_dist = None

        for i, pos_i in enumerate(self.parent.legends.scene_positions):
            dist = abs(pos.x() - pos_i.x())

            if best_dist is None or best_dist > dist:
                best_dist = dist
                best_i = i
            
        return best_i
    

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.update_positions()
            self.swap_meta["distance"] = 0
            self.swap_meta["leftDown"] = True


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.setCursor(QtCore.Qt.ArrowCursor)

            if self.swap_meta["distance"] == 0:
                self.highlight()

            else:
                old_index = self.closest_index(self.swap_meta["scenePos"])

                new_index = self.closest_index(self.scenePos())

                self.parent.move_plot(old_index, new_index)

            self.update_positions()
            self.swap_meta["distance"] = 0
            self.swap_meta["leftDown"] = False



    def itemChange(self, change, value):
        if change == self.ItemPositionChange and self.swap_meta["leftDown"]:
            if self.swap_meta["pos"] is not None:
                self.swap_meta["distance"] += abs(value.x() - self.swap_meta["pos"].x())

            if self.swap_meta["distance"] > 0:
                self.setCursor(QtCore.Qt.ClosedHandCursor)

            # Get the limits of the ViewBox
            vb = self.getViewBox()
            if vb is not None:
                rect = vb.viewRect()  # Returns a QRectF
                if not rect.contains(value):
                    # Adjust value to keep it inside the ViewBox
                    if value.x() < rect.left():
                        value.setX(rect.left())
                    elif value.x() > rect.right():
                        value.setX(rect.right())
            return QtCore.QPointF(value.x(), self.y())
        return None
