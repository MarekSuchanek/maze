from PyQt5 import QtWidgets, QtGui, QtCore, QtSvg, uic
import numpy
import os
dir = os.path.dirname(__file__)

def filepath(rel_path):
    return os.path.join(dir, rel_path)

CELL_SIZE = 32
SVG_GRASS = QtSvg.QSvgRenderer(filepath('static/pics/grass.svg'))
SVG_WALL = QtSvg.QSvgRenderer(filepath('static/pics/wall.svg'))
VALUE_ROLE = QtCore.Qt.UserRole

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


def new_dialog(window, grid):
    dialog = QtWidgets.QDialog(window)
    with open(filepath('static/ui/newmaze.ui')) as f:
        uic.loadUi(f, dialog)
    result = dialog.exec()
    if result == QtWidgets.QDialog.Rejected:
        return
    cols = dialog.findChild(QtWidgets.QSpinBox, 'widthBox').value()
    rows = dialog.findChild(QtWidgets.QSpinBox, 'heightBox').value()
    grid.array = numpy.zeros((rows, cols), dtype=numpy.int8)
    size = logical_to_pixels(rows, cols)
    grid.setMinimumSize(*size)
    grid.setMaximumSize(*size)
    grid.resize(*size)
    grid.update()

def main():
    app = QtWidgets.QApplication([])
    window = QtWidgets.QMainWindow()
    with open(filepath('static/ui/mainwindow.ui')) as f:
        uic.loadUi(f, window)

    array = numpy.zeros((15, 20), dtype=numpy.int8)
    array[:, 5] = -1

    grid = GridWidget(array)

    scroll_area = window.findChild(QtWidgets.QScrollArea, 'scrollArea')
    scroll_area.setWidget(grid)

    itemG = QtWidgets.QListWidgetItem('Grass')
    icon = QtGui.QIcon(filepath('static/pics/grass.svg'))
    itemG.setIcon(icon)
    itemG.setData(VALUE_ROLE, 0)
    itemW = QtWidgets.QListWidgetItem('Wall')
    icon = QtGui.QIcon(filepath('static/pics/wall.svg'))
    itemW.setIcon(icon)
    itemW.setData(VALUE_ROLE, -1)
    palette = window.findChild(QtWidgets.QListWidget, 'palette')
    palette.addItem(itemG)
    palette.addItem(itemW)

    def item_activated():
        for item in palette.selectedItems():
            grid.selected = item.data(VALUE_ROLE)

    palette.itemSelectionChanged.connect(item_activated)
    palette.setCurrentRow(1)
    action = window.findChild(QtWidgets.QAction, 'actionNew')
    action.triggered.connect(lambda: new_dialog(window, grid))
    window.show()
    return app.exec()

main()
