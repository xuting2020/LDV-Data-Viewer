from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QCursor
from mpl_canvas import PhaAmp3DMplCanvas
import matplotlib.cm as cm


class PhaseAmplitude3DWindow(QMainWindow):
    def __init__(self,parent=None):

        super(PhaseAmplitude3DWindow, self).__init__(parent)

        self.init_window()

    def init_window(self):

        self.setWindowTitle("PhaseAmplitude3DWindow")
        self.resize(1000, 800)

        self.main_widget = QtWidgets.QWidget(self)

        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.canvas = PhaAmp3DMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(self.right_menu_show)


    def set_input_data(self, x, y, amplitude):
        self.x = x
        self.y = y
        self.amplitude = amplitude


    def plot(self):
        self.canvas.plot_3d_amplitude(self.x,self.y,self.amplitude,cm.jet)

    def right_menu_show(self):
        try:
            self.contextMenu = QMenu()
            self.act_save = self.contextMenu.addAction('SaveFig')
            self.contextMenu.popup(QCursor.pos())

            self.act_save.triggered.connect(self.save_fig)
            self.contextMenu.show()
        except Exception as e:
            print(e)

    def save_fig(self):
        fileName, ok = QFileDialog.getSaveFileName()
        print(fileName)
        self.canvas.fig.savefig(fileName, format='png', transparent=False, dpi=300, pad_inches = 0)

