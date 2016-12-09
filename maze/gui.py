from PyQt5 import QtWidgets, QtGui, QtCore, QtSvg, uic
import numpy as np
import os
dir = os.path.dirname(__file__)

def filepath(rel_path):
    return os.path.join(dir, rel_path)

CELL_SIZE = 32
SVG_GRASS = QtSvg.QSvgRenderer(filepath('static/pics/grass.svg'))
SVG_WALL = QtSvg.QSvgRenderer(filepath('static/pics/wall.svg'))
VALUE_ROLE = QtCore.Qt.UserRole

ITEMS = [  # TODO: from config
    ('Grass', 'static/pics/grass.svg', 0),
    ('Wall', 'static/pics/wall.svg', -1),
    ('Strong wall', 'static/pics/wall2.svg', -2),
    ('Castle', 'static/pics/castle.svg', 1),
]

def pixels_to_logical(x, y):
    return y // CELL_SIZE, x // CELL_SIZE


def logical_to_pixels(row, column):
    return column * CELL_SIZE, row * CELL_SIZE


class GridWidget(QtWidgets.QWidget):
    def __init__(self, array):
        super().__init__()
        self.array = array
        size = logical_to_pixels(*array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)

    def paintEvent(self, event):
        rect = event.rect()
        row_min, col_min = pixels_to_logical(rect.left(), rect.top())
        row_min = max(row_min, 0)
        col_min = max(col_min, 0)
        row_max, col_max = pixels_to_logical(rect.right(), rect.bottom())
        row_max = min(row_max + 1, self.array.shape[0])
        col_max = min(col_max + 1, self.array.shape[1])
        painter = QtGui.QPainter(self)
        for row in range(row_min, row_max):
            for column in range(col_min, col_max):
                x, y = logical_to_pixels(row, column)
                rect = QtCore.QRectF(x, y, CELL_SIZE, CELL_SIZE)
                white = QtGui.QColor(255, 255, 255)
                painter.fillRect(rect, QtGui.QBrush(white))
                SVG_GRASS.render(painter, rect)
                if self.array[row, column] < 0:
                    SVG_WALL.render(painter, rect)

    def mousePressEvent(self, event):
        row, column = pixels_to_logical(event.x(), event.y())
        if 0 <= row < self.array.shape[0] and 0 <= column < self.array.shape[1]:
            self.array[row, column] = self.selected
            self.update(*logical_to_pixels(row, column), CELL_SIZE, CELL_SIZE)


class MazeGUI:

    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.window = QtWidgets.QMainWindow()
        with open(filepath('static/ui/mainwindow.ui')) as f:
            uic.loadUi(f, self.window)
        self.grid = GridWidget(np.zeros((20, 20), dtype=np.int8))
        scroll_area = self._find(QtWidgets.QScrollArea, 'scrollArea')
        scroll_area.setWidget(self.grid)
        self.palette = self._find(QtWidgets.QListWidget, 'palette')

    def _find(self, type, name):
        return self.window.findChild(type, name)

    def _setup_palette(self):
        def item_activated():
            for item in self.palette.selectedItems():
                self.grid.selected = item.data(VALUE_ROLE)

        for x in ITEMS:
            item = QtWidgets.QListWidgetItem(x[0])
            item.setIcon(QtGui.QIcon(filepath(x[1])))
            item.setData(VALUE_ROLE, x[2])
            self.palette.addItem(item)
        self.palette.itemSelectionChanged.connect(item_activated)
        self.palette.setCurrentRow(1)
        action = self.window.findChild(QtWidgets.QAction, 'actionNew')
        action.triggered.connect(self.new_dialog)

    def run(self):
        self.window.show()
        return self.app.exec()

    def new_dialog(self):
        dialog = QtWidgets.QDialog(self.window)
        with open(filepath('static/ui/newmaze.ui')) as f:
            uic.loadUi(f, dialog)
        result = dialog.exec()
        if result == QtWidgets.QDialog.Rejected:
            return
        cols = dialog.findChild(QtWidgets.QSpinBox, 'widthBox').value()
        rows = dialog.findChild(QtWidgets.QSpinBox, 'heightBox').value()
        self.grid.array = np.zeros((rows, cols), dtype=np.int8)
        size = logical_to_pixels(rows, cols)
        self.grid.setMinimumSize(*size)
        self.grid.setMaximumSize(*size)
        self.grid.resize(*size)
        self.grid.update()


def main():
    gui = MazeGUI()
    gui.run()
