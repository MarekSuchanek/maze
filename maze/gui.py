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


class MazeGUIStatus:
    POS_MASK = "Position: {}, {}  "
    SIZE_MASK = "Size: {}×{}  "
    ZOOM_MASK = "Zoom: {}%  "
    DRAG_MASK = "Dragging: {}  "
    UNSAVED_TXT = "UNSAVED  "

    def __init__(self, statusbar):
        self.statusbar = statusbar
        self.position = QtWidgets.QLabel(statusbar)
        self.set_position(0, 0)
        statusbar.addWidget(self.position)
        self.size = QtWidgets.QLabel(statusbar)
        self.set_size(0, 0)
        statusbar.addWidget(self.size)
        self.zoom = QtWidgets.QLabel(statusbar)
        self.set_zoom(100)
        statusbar.addWidget(self.zoom)
        self.unsaved = QtWidgets.QLabel(statusbar)
        self.set_unsaved(True)
        statusbar.addWidget(self.unsaved)
        self.dragging = QtWidgets.QLabel(statusbar)
        self.set_dragging("")
        statusbar.addWidget(self.dragging)

    def set_position(self, row, col):
        self.position.setText(self.POS_MASK.format(row+1, col+1))

    def set_size(self, rows, cols):
        self.size.setText(self.SIZE_MASK.format(rows, cols))

    def set_zoom(self, percentage):
        self.zoom.setText(self.ZOOM_MASK.format(percentage))

    def set_unsaved(self, unsaved):
        self.unsaved.setText(self.UNSAVED_TXT if unsaved else '')

    def set_dragging(self, name):
        if name == "":
            self.dragging.setText("")
        else:
            self.dragging.setText(self.DRAG_MASK.format(name))


class GridWidget(QtWidgets.QWidget):

    def __init__(self, array, status, elements, config):
        super().__init__()
        self.status = status
        self.config = config
        self.cell_size = int(config['cell_size'])
        self.init_size = int(config['cell_size'])
        self.min_cell_size = int(config['min_cell_size'])
        self.array = None
        self.starts = None
        self.paths = None
        self.dirs = None
        self.last_mouse = None
        self.observers = []
        self.change_array(array)
        self.elements = elements
        self.setMouseTracking(True)
        self.changed = False

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
        self.status.set_dragging(self.elements[self.selected].name)

    def mouseMoveEvent(self, event):
        step = self.px2table(event.x(), event.y())
        if not self.inside_array(*step):
            return
        self.status.set_position(*step)
        if self.last_mouse is None:
            return
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
        self.status.set_dragging("")

    def wheelEvent(self, event):
        if event.modifiers() != QtCore.Qt.ControlModifier:
            return
        event.accept()  # no propagation to scroll area
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def inside_array(self, row, col):
        return 0 <= row < self.array.shape[0] and \
               0 <= col < self.array.shape[1]

    def put_on_cell(self, row, col):
        if self.array[row, col] == self.selected:
            return False
        elif (self.array[row, col] > 1) and (self.selected <= 1):  # was start and now is not
            self.starts.remove((row, col))
        elif (self.selected > 1) and (self.array[row, col] <= 1):  # wasn't start and now is
            self.starts.add((row, col))
        self.array[row, col] = self.selected
        self.set_changed(True)
        return True

    def change_array(self, array):
        self.set_changed(False)
        self.array = array
        indices = list(np.where(array > 1))
        self.starts = set(zip(list(indices[0]), list(indices[1])))
        self.update_array()
        self.status.set_size(*array.shape)

    def update_array(self):
        self.make_paths()
        self.update_size()
        self.update()

    def set_changed(self, changed):
        self.changed = changed
        self.status.set_unsaved(changed)
        for o in self.observers:
            o.change_notice()

    def make_paths(self):
        analysis = analyze(self.array)
        paths = np.zeros(self.array.shape, dtype=np.int8)
        dirs = np.zeros(self.array.shape, dtype=np.int8)
        hor_set = frozenset([2, 3, 6, 7, 10, 11, 14, 15])
        ver_set = frozenset([4, 5, 6, 7, 12, 13, 14, 15])
        for start in self.starts:
            try:
                path = analysis.path(*start)
                for step in path:
                    x, y = step
                    d = analysis.directions[x, y]
                    dirs[x, y] = DIRECTIONS_MAP.get(d, 0)
                    if d == b'<':
                        if paths[x, y] not in hor_set:
                            paths[x, y] += 2
                        if paths[x, y-1] < 8:
                            paths[x, y-1] += 8
                    elif d == b'>':
                        if paths[x, y] < 8:
                            paths[x, y] += 8
                        if paths[x, y+1] not in hor_set:
                            paths[x, y+1] += 2
                    elif d == b'v':
                        if paths[x, y] not in ver_set:
                            paths[x, y] += 4
                        if paths[x+1, y] % 2 == 0:
                            paths[x+1, y] += 1
                    elif d == b'^':
                        if paths[x, y] % 2 == 0:
                            paths[x, y] += 1
                        if paths[x-1, y] not in ver_set:
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

    def zoom_in(self):
        self.cell_size += max(int(self.cell_size * 0.1), 1)
        self.update_size()
        self.status.set_zoom(100 * self.cell_size // self.init_size)

    def zoom_out(self):
        if self.cell_size < self.min_cell_size:
            return
        self.cell_size -= max(int(self.cell_size * 0.1), 1)
        self.update_size()
        self.status.set_zoom(100 * self.cell_size // self.init_size)

    def zoom_reset(self):
        self.cell_size = self.init_size
        self.update_size()
        self.status.set_zoom(100)

    def save_to_file(self, filename):
        np.savetxt(filename, self.array, fmt='%d')

    def load_from_file(self, filename):
        array = np.loadtxt(filename, dtype=np.int8)
        self.change_array(array)

    def add_observer(self, observer):
        self.observers.append(observer)


class MazeMainWindow(QtWidgets.QMainWindow):

    def __init__(self, maze_gui):
        super().__init__()
        self.gui = maze_gui

    def closeEvent(self, event):
        if self.gui.ask_save():
            event.accept()
            self.close()
        else:
            event.ignore()


class MazeGUI:

    def __init__(self, config):
        self.app = QtWidgets.QApplication([])
        self.config = config['gui']
        self.filename = None
        self._setup_elements()
        self.window = MazeMainWindow(self)
        with open(filepath('static/ui/mainwindow.ui')) as f:
            uic.loadUi(f, self.window)
        statusbar = self.window.findChild(QtWidgets.QStatusBar, 'statusbar')
        self.status = MazeGUIStatus(statusbar)
        self._setup_grid()
        self._setup_palette()
        self._setup_actions()

    def _find(self, type, name):
        return self.window.findChild(type, name)

    def _setup_elements(self):
        self.elements = OrderedDict()
        with open(filepath(self.config['palette'])) as f:
            data = json.load(f, object_pairs_hook=OrderedDict)
            data = [(int(k), MazeElement(v, k)) for k, v in data.items()]
            self.elements = OrderedDict(data)

    def _setup_grid(self):
        new_array = np.zeros(
            (
                int(self.config['init_rows']),
                int(self.config['init_cols'])
            ),
            dtype=np.int8
        )
        self.grid = GridWidget(new_array, self.status,
                               self.elements, self.config)
        scroll_area = self._find(QtWidgets.QScrollArea, 'scrollArea')
        scroll_area.setWidget(self.grid)
        self.grid.add_observer(self)

    def change_notice(self):
        if self.window.windowTitle().endswith(' *'):
            return
        self.window.setWindowTitle(self.window.windowTitle() + ' *')

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
        action = self.window.findChild(QtWidgets.QAction, 'actionOpen')
        action.triggered.connect(self.file_open)
        action = self.window.findChild(QtWidgets.QAction, 'actionSave')
        action.triggered.connect(self.file_save)
        action = self.window.findChild(QtWidgets.QAction, 'actionSaveAs')
        action.triggered.connect(self.file_save_as)
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

    def file_open(self):
        if not self.ask_save():
            return  # don't want to open now
        paths = self.file_dialog(False)
        if len(paths) > 0:
            self.grid_open(paths[0])

    def file_save(self):
        if self.filename is None:
            self.file_save_as()
        else:
            self.grid_save(self.filename)

    def file_save_as(self):
        paths = self.file_dialog(True)
        if len(paths) > 0:
            self.grid_save(paths[0])

    def ask_save(self):
        if not self.grid.changed:
            return True  # no changes, continue
        reply = QtWidgets.QMessageBox.question(
            self.window, 'Maze - Unsaved changes',
            'Do you want to save unsaved changes?',
            buttons = QtWidgets.QMessageBox.Yes |
                      QtWidgets.QMessageBox.No |
                      QtWidgets.QMessageBox.Cancel,
            defaultButton = QtWidgets.QMessageBox.Cancel
        )
        if reply == QtWidgets.QMessageBox.Cancel:
            return False  # cancel action
        elif reply == QtWidgets.QMessageBox.Yes:
            self.file_save()
        return True  # can continue (save/unsaved)

    def grid_save(self, filename):
        try:
            self.grid.save_to_file(filename)
            self.set_file(filename)
        except:
            err = QtWidgets.QErrorMessage(self.window)
            err.showMessage("Couldn't save to selected file: {}".format(filename))

    def grid_open(self, filename):
        try:
            self.grid.load_from_file(filename)
            self.set_file(filename)
        except:
            err = QtWidgets.QErrorMessage(self.window)
            err.showMessage("Couldn't open selected file: {}".format(filename))

    def set_file(self, filename):
        self.window.setWindowTitle('Maze: '+filename)
        self.filename = filename

    def reset_file(self):
        self.window.setWindowTitle('Maze')
        self.filename = None

    def file_dialog(self, save):
        dialog = QtWidgets.QFileDialog(self.window)
        if save:
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            dialog.setWindowTitle('Maze - Save as')
        else:
            dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
            dialog.setWindowTitle('Maze - Open')
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        dialog.setDirectory(QtCore.QDir.home())
        dialog.setNameFilters([
            self.window.tr('Text Files (*.txt)'),
            self.window.tr('All Files (*)')
        ])
        dialog.setDefaultSuffix('.txt')
        if dialog.exec():
            return dialog.selectedFiles()
        return []

    def new_dialog(self):
        if not self.ask_save():
            return  # don't want to new now
        dialog = QtWidgets.QDialog(self.window)
        with open(filepath('static/ui/newmaze.ui')) as f:
            uic.loadUi(f, dialog)
        fill_select = dialog.findChild(QtWidgets.QComboBox, 'selectFill')
        for e in self.elements.values():
            fill_select.addItem(e.icon, e.name, e.value)
        result = dialog.exec()
        if result == QtWidgets.QDialog.Rejected:
            return
        cols = dialog.findChild(QtWidgets.QSpinBox, 'widthBox').value()
        rows = dialog.findChild(QtWidgets.QSpinBox, 'heightBox').value()
        fill = fill_select.currentData()
        self.grid.change_array(np.full((rows, cols), fill, dtype=np.int8))
        self.reset_file()

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
