from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtWidgets
import matplotlib.cm as cm
from phase_amplitude_3d_window import PhaseAmplitude3DWindow

from PyQt5.QtCore import QDir
from PyQt5.QtGui import QIcon, QPixmap, QFont, QCursor
from PyQt5.QtCore import QDate

import sys

from data import *
from process import *
from data_import2 import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from mpl_canvas import PhaAmpMplCanvas
from process import *

class PhaseAmplitudeWindow(QMainWindow):
    def __init__(self,parent=None):

        super(PhaseAmplitudeWindow, self).__init__(parent)

        self.smooth_factor = 1000

        self.init_window()

    def init_window(self):
        #初始化窗口
        self.setWindowTitle("PhaseAmplitudeWindow")
        self.resize(1000, 800)

        self.main_widget = QtWidgets.QWidget(self)

        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.canvas = PhaAmpMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        self.layout.addLayout(self.set_layout())

        self.main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(self.right_menu_show)

    def set_layout(self):
        layout = QHBoxLayout()
        self.smoothed_amplitude_3D_btn = QPushButton(self)
        self.smoothed_amplitude_3D_btn.setText("3D_smoothed_amp")
        self.smoothed_amplitude_3D_btn.setFixedSize(150, 30)
        self.smoothed_amplitude_3D_btn.clicked.connect(self.on_smoothed_amp_clicked)
        layout.addWidget(self.smoothed_amplitude_3D_btn, alignment=QtCore.Qt.AlignLeft)

        self.amplitude_3D_btn = QPushButton(self)
        self.amplitude_3D_btn.setText("3D_amp")
        self.amplitude_3D_btn.setFixedSize(100, 30)
        self.amplitude_3D_btn.clicked.connect(self.on_amp_clicked)
        layout.addWidget(self.amplitude_3D_btn, alignment=QtCore.Qt.AlignLeft)

        self.smooth_factor_label = QLabel(self)
        self.smooth_factor_label.setFixedSize(130, 30)
        self.smooth_factor_label.setText("Smooth factor:")
        layout.addWidget(self.smooth_factor_label, alignment=QtCore.Qt.AlignLeft)

        self.smooth_factor_text = QTextEdit(self)
        self.smooth_factor_text.setFixedSize(80, 30)
        self.smooth_factor_text.setText(str(self.smooth_factor))
        layout.addWidget(self.smooth_factor_text, alignment=QtCore.Qt.AlignLeft)

        self.input_apply_btn = QPushButton(self)
        self.input_apply_btn.setText("Apply")
        self.input_apply_btn.setFixedSize(50, 30)
        self.input_apply_btn.clicked.connect(self.on_smooth_factor)
        layout.addWidget(self.input_apply_btn, alignment=QtCore.Qt.AlignLeft)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(0)

        return layout

    def on_smoothed_amp_clicked(self):
        self.pha_amp_3d_win = PhaseAmplitude3DWindow()
        self.pha_amp_3d_win.set_input_data(self.x,self.y,self.smoothed_amplitude)#输入PhaAmp窗口画图需要的数据
        self.pha_amp_3d_win.plot()
        self.pha_amp_3d_win.show()

    def on_amp_clicked(self): # to plot 3D_amplitude
        self.pha_amp_3d_win = PhaseAmplitude3DWindow()#弹出显示3D图的新窗口
        self.pha_amp_3d_win.set_input_data(self.x, self.y, self.amplitude)
        self.pha_amp_3d_win.plot()
        self.pha_amp_3d_win.show()


    def set_input_data(self, x, y, filter_z): # 将输入数据保存到类
        self.x = x
        self.y = y
        self.filter_z = filter_z
        # print('x',self.x.shape)
        # print('y',self.y.shape)
        # print('filter_z',filter_z.shape)


    def plot(self):
        angle,amplitude,V = phase_amplitude(self.x,self.y,self.filter_z) #计算需要的值
        print("Smooth factor", self.smooth_factor)
        a_smooth = interpolate.SmoothBivariateSpline(self.x, self.y, amplitude, s=self.smooth_factor)
        amp_smoothed = np.abs(a_smooth.ev(self.x, self.y))

        self.amplitude = amplitude
        self.smoothed_amplitude = amp_smoothed

        self.canvas.plot_phase(self.x, self.y, angle, V)
        self.canvas.plot_amplitude(self.x,self.y,amplitude,V)
        self.canvas.plot_smoothed_amplitude(self.x,self.y,amp_smoothed,V)
        self.canvas.plot_3D_smoothed_amplitude(self.x,self.y,amp_smoothed,cm.jet)


    def on_smooth_factor(self):
        self.smooth_factor = int(self.smooth_factor_text.toPlainText())
        plt.clf()
        self.plot()

    def right_menu_show(self):#设置右键菜单savefig
        try:
            self.contextMenu = QMenu()
            self.act_save = self.contextMenu.addAction('SaveFig')
            self.contextMenu.popup(QCursor.pos())

            self.act_save.triggered.connect(self.save_fig)
            self.contextMenu.show()
        except Exception as e:
            print(e)

    def save_fig(self):#保存图片，默认格式png
        fileName, ok = QFileDialog.getSaveFileName()
        print(fileName)
        self.canvas.fig.savefig(fileName, format='png', transparent=False, dpi=300, pad_inches = 0)


