from PyQt5 import QtWidgets, QtGui, QtCore, QtSvg, uic
import numpy as np
import os
import json
import configparser
from collections import OrderedDict
from bresenham import bresenham
from .analysis import analyze, NoPathExistsException


VALUE_ROLE = QtCore.Qt.UserRole
CONFIG_FILE = 'static/gui.cfg'
LINE_MASK = 'static/pics/lines/{}.svg'
ARROW_MASK = 'static/pics/arrows/{}.svg'
DIRECTIONS = ['up', 'right', 'left', 'down']
DIRECTIONS_MAP = {b'^': 0, b'>': 1, b'<': 2, b'v': 3}
BASEDIR = os.path.dirname(__file__)


def filepath(rel_path):
    return os.path.join(BASEDIR, rel_path)

SVG_LINES = {i: QtSvg.QSvgRenderer(filepath(LINE_MASK.format(i))) for i in range(1, 16)}
SVG_ARROWS = {i: QtSvg.QSvgRenderer(filepath(ARROW_MASK.format(DIRECTIONS[i]))) for i in range(4)}


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
        self.init_size = cell_size
        self.array = None
        self.starts = None
        self.paths = None
        self.dirs = None
        self.last_mouse = None
        self.change_array(array)
        self.elements = elements

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
            for col in range(col_min, col_max):
                x, y = self.table2px(row, col)
                rect = QtCore.QRectF(x, y, self.cell_size, self.cell_size)
                white = QtGui.QColor(255, 255, 255)
                painter.fillRect(rect, QtGui.QBrush(white))
                self.elements[0].svg.render(painter, rect)
                if self.paths[row, col] != 0:
                    SVG_LINES[self.paths[row, col]].render(painter, rect)
                    if self.array[row, col] == 0:
                        SVG_ARROWS[self.dirs[row, col]].render(painter, rect)
                if self.array[row, col] != 0:
                    self.elements[self.array[row, col]].svg.render(painter, rect)

    def mousePressEvent(self, event):
        step = self.px2table(event.x(), event.y())
        if self.inside_array(*step):
            if self.put_on_cell(*step):
                self.update_array()
        self.last_mouse = step

    def mouseMoveEvent(self, event):
        step = self.px2table(event.x(), event.y())
        path = list(bresenham(*self.last_mouse, *step))
        any_change = False
        for step in path:
            if self.inside_array(*step):
                any_change |= self.put_on_cell(*step)
        if any_change:
            self.update_array()
        self.last_mouse = step

    def mouseReleaseEvent(self, event):
        self.last_mouse = None

    def inside_array(self, row, col):
        return 0 <= row < self.array.shape[0] and 0 <= col < self.array.shape[1]

    def put_on_cell(self, row, col):
        if self.array[row, col] == self.selected:
            return False
        elif (self.array[row, col] > 1) and (self.selected <= 1):  # was start and now is not
            self.starts.remove((row, col))
        elif (self.selected > 1) and (self.array[row, col] <= 1):  # wasnt start and now is
            self.starts.add((row, col))
        self.array[row, col] = self.selected
        return True

    def change_array(self, array):
        self.array = array
        self.starts = set()
        self.update_array()

    def update_array(self):
        self.make_paths()
        self.update_size()
        self.update()

    def make_paths(self):
        analysis = analyze(self.array)
        paths = np.zeros(self.array.shape, dtype=np.int8)
        dirs = np.zeros(self.array.shape, dtype=np.int8)
        for start in self.starts:
            try:
                path = analysis.path(*start)
                for step in path:
                    x, y = step
                    d = analysis.directions[x, y]
                    dirs[x, y] = DIRECTIONS_MAP.get(d, 0)
                    if d == b'<':
                        if paths[x, y] not in {2, 3, 6, 7, 10, 11, 14, 15}:
                            paths[x, y] += 2
                        if paths[x, y-1] < 8:
                            paths[x, y-1] += 8
                    elif d == b'>':
                        if paths[x, y] < 8:
                            paths[x, y] += 8
                        if paths[x, y+1] not in {2, 3, 6, 7, 10, 11, 14, 15}:
                            paths[x, y+1] += 2
                    elif d == b'v':
                        if paths[x, y] not in {4, 5, 6, 7, 12, 13, 14, 15}:
                            paths[x, y] += 4
                        if paths[x+1, y] % 2 == 0:
                            paths[x+1, y] += 1
                    elif d == b'^':
                        if paths[x, y] % 2 == 0:
                            paths[x, y] += 1
                        if paths[x-1, y] not in {4, 5, 6, 7, 12, 13, 14, 15}:
                            paths[x-1, y] += 4
            except NoPathExistsException:
                pass
        self.paths = paths
        self.dirs = dirs


    def update_size(self):
        size = self.table2px(*self.array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)

    # TODO: display zoom at status bar, wheel?
    def zoom_in(self):
        self.cell_size += max(int(self.cell_size * 0.1), 1)
        self.update_size()

    # TODO: display zoom at status bar, wheel?
    def zoom_out(self):
        if self.cell_size < 8:  # TODO: from config
            return
        self.cell_size -= max(int(self.cell_size * 0.1), 1)
        self.update_size()

    # TODO: display zoom at status bar
    def zoom_reset(self):
        self.cell_size = self.init_size
        self.update_size()


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
        self._setup_actions()

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
                self.grid.selected = int(item.data(VALUE_ROLE))

        for e in self.elements.values():
            item = QtWidgets.QListWidgetItem(e.name)
            item.setIcon(e.icon)
            item.setData(VALUE_ROLE, e.value)
            self.palette.addItem(item)
        self.palette.itemSelectionChanged.connect(item_activated)
        self.palette.setCurrentRow(1)

    def _setup_actions(self):
        action = self.window.findChild(QtWidgets.QAction, 'actionNew')
        action.triggered.connect(self.new_dialog)
        action = self.window.findChild(QtWidgets.QAction, 'actionAbout')
        action.triggered.connect(self.about_dialog)
        action = self.window.findChild(QtWidgets.QAction, 'actionZoomIn')
        action.triggered.connect(self.grid.zoom_in)
        action = self.window.findChild(QtWidgets.QAction, 'actionZoomOut')
        action.triggered.connect(self.grid.zoom_out)
        action = self.window.findChild(QtWidgets.QAction, 'actionZoomReset')
        action.triggered.connect(self.grid.zoom_reset)

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
