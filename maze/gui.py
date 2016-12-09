from PyQt5 import QtWidgets, QtGui, QtCore, QtSvg, uic
import numpy as np
import os
import json
import configparser
from collections import OrderedDict


VALUE_ROLE = QtCore.Qt.UserRole
CONFIG_FILE = 'static/gui.cfg'
BASEDIR = os.path.dirname(__file__)


def filepath(rel_path):
    return os.path.join(BASEDIR, rel_path)


class MazeElement:

    def __init__(self, values, key):
        self.name = values['name']
        self.img_path = filepath(values['img'])
        self.value = key
        self.svg = QtSvg.QSvgRenderer(self.img_path)
        self.icon = QtGui.QIcon(self.img_path)


class GridWidget(QtWidgets.QWidget):

    def __init__(self, array, elements, cell_size=32):
        super().__init__()
        self.cell_size = cell_size
        self.array = array
        self.elements = elements
        size = self.table2px(*array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)

    def px2table(self, x, y):
        return y // self.cell_size, x // self.cell_size

    def table2px(self, row, column):
        return column * self.cell_size, row * self.cell_size

    def paintEvent(self, event):
        rect = event.rect()
        row_min, col_min = self.px2table(rect.left(), rect.top())
        row_min = max(row_min, 0)
        col_min = max(col_min, 0)
        row_max, col_max = self.px2table(rect.right(), rect.bottom())
        row_max = min(row_max + 1, self.array.shape[0])
        col_max = min(col_max + 1, self.array.shape[1])
        painter = QtGui.QPainter(self)
        for row in range(row_min, row_max):
            for column in range(col_min, col_max):
                x, y = self.table2px(row, column)
                rect = QtCore.QRectF(x, y, self.cell_size, self.cell_size)
                white = QtGui.QColor(255, 255, 255)
                painter.fillRect(rect, QtGui.QBrush(white))
                self.elements[0].svg.render(painter, rect)
                if self.array[row, column] != 0:
                    self.elements[self.array[row, column]].svg.render(painter, rect)

    def mousePressEvent(self, event):
        row, column = self.px2table(event.x(), event.y())
        if 0 <= row < self.array.shape[0] and 0 <= column < self.array.shape[1]:
            self.array[row, column] = self.selected
            self.update(*self.table2px(row, column), self.cell_size, self.cell_size)

    def change_array(self, array):
        size = self.table2px(*array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)
        self.update()


class MazeGUI:

    def __init__(self, config):
        self.app = QtWidgets.QApplication([])
        self.config = config['gui']
        self._setup_elements()
        self.window = QtWidgets.QMainWindow()
        with open(filepath('static/ui/mainwindow.ui')) as f:
            uic.loadUi(f, self.window)
        self._setup_grid()
        self._setup_palette()
        self._setup_dialogs()

    def _find(self, type, name):
        return self.window.findChild(type, name)

    def _setup_elements(self):
        self.elements = OrderedDict()
        with open(filepath(self.config['palette'])) as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
            data = [(int(k), MazeElement(v, k)) for k,v in data.items()]
            self.elements = OrderedDict(data)

    def _setup_grid(self):
        new_array = np.zeros(
            (
                int(self.config['init_rows']),
                int(self.config['init_cols'])
            ),
            dtype=np.int8
        )
        self.grid = GridWidget(new_array, self.elements, int(self.config['cell_size']))
        scroll_area = self._find(QtWidgets.QScrollArea, 'scrollArea')
        scroll_area.setWidget(self.grid)

    def _setup_palette(self):
        self.palette = self._find(QtWidgets.QListWidget, 'palette')

        def item_activated():
            for item in self.palette.selectedItems():
                self.grid.selected = item.data(VALUE_ROLE)

        for e in self.elements.values():
            item = QtWidgets.QListWidgetItem(e.name)
            item.setIcon(e.icon)
            item.setData(VALUE_ROLE, e.value)
            self.palette.addItem(item)
        self.palette.itemSelectionChanged.connect(item_activated)
        self.palette.setCurrentRow(1)

    def _setup_dialogs(self):
        action = self.window.findChild(QtWidgets.QAction, 'actionNew')
        action.triggered.connect(self.new_dialog)
        action = self.window.findChild(QtWidgets.QAction, 'actionAbout')
        action.triggered.connect(self.about_dialog)

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
        self.grid.change_array(np.zeros((rows, cols), dtype=np.int8))

    def about_dialog(self):
        dialog = QtWidgets.QDialog(self.window)
        with open(filepath('static/ui/help.ui')) as f:
            uic.loadUi(f, dialog)
        dialog.exec()


def main():
    cfg = configparser.ConfigParser()
    cfg.read(filepath(CONFIG_FILE))
    gui = MazeGUI(cfg)
    gui.run()
