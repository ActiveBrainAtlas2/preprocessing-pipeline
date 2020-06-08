from PyQt5.QtCore import Qt, QRectF, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QPixmap
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame

class ImageViewer(QGraphicsView):
    click = pyqtSignal(QPoint)

    def __init__(self, parent):
        super(ImageViewer, self).__init__(parent)

        self.zoom = 0
        self.empty = True
        self.scene = QGraphicsScene(self)
        self.photo = QGraphicsPixmapItem()
        self.scale_factor = 0

        self.scene.addItem(self.photo)
        self.setScene(self.scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)

    def set_photo(self, img_fp=None):
        pix_map = QPixmap(img_fp)
        self.zoom = 0
        if pix_map and not pix_map.isNull():
            self.empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.photo.setPixmap(pix_map)
        else:
            self.empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self.photo.setPixmap(QPixmap())
        self.fitInView()

    def set_drag_mode(self, drag_mode):
        if not self.photo.pixmap().isNull():
            if drag_mode == 0:
                self.setDragMode(QGraphicsView.NoDrag)
            elif drag_mode == 1:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
            else:
                raise ValueError(drag_mode + ' is not a valid drag_mode')

    def fitInView(self, scale=True):
        rect = QRectF(self.photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if not self.empty:
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())

                view_rect = self.viewport().rect()
                scene_rect = self.transform().mapRect(rect)
                self.scale_factor = min(view_rect.width() / scene_rect.width(),
                             view_rect.height() / scene_rect.height())
                self.scale(self.scale_factor, self.scale_factor)

            self.zoom = 0

    def wheelEvent(self, event):
        if not self.empty:
            if event.angleDelta().y() > 0:
                self.scale_factor = 1.25
                self.zoom += 1
            else:
                self.scale_factor = 0.8
                self.zoom -= 1

            if self.zoom > 0:
                self.scale(self.scale_factor, self.scale_factor)
            elif self.zoom == 0:
                self.fitInView()
            else:
                self.zoom = 0

    def mousePressEvent(self, event):
        if self.photo.isUnderMouse():
            self.click.emit(QPoint(event.pos()))

        super(ImageViewer, self).mousePressEvent(event)
