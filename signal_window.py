
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtWidgets

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
from mpl_canvas import *


class SignalWindow(QMainWindow):
    def __init__(self, parent=None, mode='plot', freq_hi=None, freq_lo=None, fs=None, time_from_ind=0, time_to_ind=-1):

        super(SignalWindow, self).__init__(parent)

        # NOTE All the frequency unit in the program is Hz, we only use MHz to input and display text box
        self.freq_hi = freq_hi
        self.freq_lo = freq_lo
        self.fs = fs

        self.time_from_ind = time_from_ind # 按照0-6000获得的时间点，ind=6000等价于time=12us
        self.time_to_ind = time_to_ind
        self.time_from = self.time_from_ind * 1e6 / self.fs #time window 结束时间
        self.time_to = self.time_to_ind * 1e6 / self.fs #time window开始时间

        self.left_bound = None #左光标
        self.right_bound = None #右光标

        self.init_window(mode)
        self.init_menubar()

    def init_window(self, mode): #初始化 Signal Window

        self.mode = mode

        self.setWindowTitle("Signal Window")
        self.resize(1000, 800)

        self.main_widget = QtWidgets.QWidget(self)

        if mode == "plot" or mode == "preview":#plot对应右键plot，preview对应右键preview
            ax_num = 2 #画2张图
        elif mode == "env_fig":#对应界面按键 env_fig
            ax_num = 4 #画4张图

        self.layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.canvas = ZMplCanvas(self.main_widget, ax_num=ax_num, width=5, height=4, dpi=100)
        self.layout.addWidget(self.canvas)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        if mode == "plot" or mode == "env_fig":
            input_layout = self.set_input_layout()
            self.layout.addLayout(input_layout)
        elif mode == "preview":
            preview_layout = self.set_preview_layout()
            self.layout.addLayout(preview_layout)

        self.main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(self.right_menu_show)

    def init_menubar(self): #设置菜单栏
        self.menubar = self.menuBar()  # 获取窗体的菜单栏

        self.file_menu = self.menubar.addMenu("File")
        self.file_menu.addAction("Edit")
        self.file_menu.addAction("Save")

        self.cursor_menu = self.menubar.addMenu("Cursor")
        self.cursor_menu.addAction("LeftBound")
        self.cursor_menu.addAction("RightBound")
        self.cursor_menu.addAction("ExitCursor")
        self.cursor_menu.triggered[QAction].connect(self.on_cursor)

        self.tool_menu = self.menubar.addMenu("Tools")
        self.tool_menu.addAction("Max")
        self.tool_menu.addAction("Min")
        self.tool_menu.addAction("Mark")
        self.tool_menu.triggered[QAction].connect(self.on_tool)

    def set_input_data(self, data):#获取该界面需要的数据
        self.data = data

    def plot_z(self, index):#plot time_domain figure
        self.data_index = index
        self.z = self.data["z"][index, :]
        self.time_window_z = self.z[int(self.time_from_ind): int(self.time_to_ind)]
        self.canvas.plot_z(self.time_window_z, self.time_from)

    def plot_band_filter_z(self, index):#plot filtered time_domain figure
        self.data_index = index
        self.z = self.data["z"][index, :]
        self.time_window_z = self.z[int(self.time_from_ind): int(self.time_to_ind)]
        self.band_filter_z = filtfilter(self.time_window_z, self.freq_lo, self.freq_hi, self.fs)
        self.canvas.plot_band_filter_z(self.band_filter_z, self.time_from)

    def plot_freq_domain(self, index, filtered=False):#plot frequency domain figure
        self.data_index = index
        self.z = self.data["z"][index, :]
        self.time_window_z = self.z[int(self.time_from_ind): int(self.time_to_ind)]
        if filtered:
            self.band_filter_z = band_filter(self.time_window_z, self.freq_lo, self.freq_hi, self.fs)
            self.canvas.plot_freq_domain(self.band_filter_z)
        else:
            self.canvas.plot_freq_domain(self.time_window_z)

    def set_input_layout(self): #设置输入栏
        input_layout = QHBoxLayout()#输入栏水平放置
        #label 为各输入的名称， input为获取的输入值
        self.time_window_label = QLabel(self)
        self.time_window_label.setFixedSize(120, 30)#设置标签的长度
        self.time_window_label.setText("Time Window:  ")#输入名称标签
        input_layout.addWidget(self.time_window_label)

        self.from_label = QLabel(self)
        self.from_label.setFixedSize(40, 30)
        self.from_label.setText("From:")
        input_layout.addWidget(self.from_label, alignment=QtCore.Qt.AlignLeft)

        self.from_input = QTextEdit(self)
        self.from_input.setFixedSize(50, 30)
        self.from_input.setText(str(self.time_from))#time window 开始时间，将输入转为string
        input_layout.addWidget(self.from_input, alignment=QtCore.Qt.AlignLeft)

        self.from_unit_label = QLabel(self)
        self.from_unit_label.setFixedSize(20, 30)
        self.from_unit_label.setText("us")#设置单位为us
        input_layout.addWidget(self.from_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.to_label = QLabel(self)
        self.to_label.setText("To:")
        self.to_label.setFixedSize(20, 30)
        input_layout.addWidget(self.to_label, alignment=QtCore.Qt.AlignLeft)

        self.to_input = QTextEdit(self)
        self.to_input.setFixedSize(50, 30)
        self.to_input.setText(str(self.time_to))#time window 结束时间，将输入转为string
        input_layout.addWidget(self.to_input, alignment=QtCore.Qt.AlignLeft)

        self.to_unit_label = QLabel(self)
        self.to_unit_label.setText("us")
        self.to_unit_label.setFixedSize(20, 30)
        input_layout.addWidget(self.to_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.input_apply_btn = QPushButton(self)
        self.input_apply_btn.setText("Apply")
        self.input_apply_btn.setFixedSize(50, 30)
        self.input_apply_btn.clicked.connect(self.on_time_window)#将time window应用到当前选取点
        input_layout.addWidget(self.input_apply_btn, alignment=QtCore.Qt.AlignLeft)

        self.input_apply_all_btn = QPushButton(self)
        self.input_apply_all_btn.setText("Apply All")
        self.input_apply_all_btn.setFixedSize(80, 30)
        self.input_apply_all_btn.clicked.connect(self.on_time_window_apply_all)#将time window应用到全部点
        input_layout.addWidget(self.input_apply_all_btn, alignment=QtCore.Qt.AlignLeft)

        self.envelope_fig_btn = QPushButton(self)
        self.envelope_fig_btn.setText("More Fig")
        self.envelope_fig_btn.setFixedSize(100, 30)
        self.envelope_fig_btn.clicked.connect(self.on_more_fig_plot)#连接到画4张图的函数
        input_layout.addWidget(self.envelope_fig_btn, alignment=QtCore.Qt.AlignLeft)

        self.time_domain_fig_btn = QPushButton(self)
        self.time_domain_fig_btn.setText("Time domain Fig")
        self.time_domain_fig_btn.setFixedSize(140, 30)
        self.time_domain_fig_btn.clicked.connect(self.on_time_domain_plot)#连接到plot time domain figure的函数
        input_layout.addWidget(self.time_domain_fig_btn, alignment=QtCore.Qt.AlignLeft)

        input_layout.setContentsMargins(0, 0, 0, 0)#使各标签紧密排列
        input_layout.addStretch(0)

        return input_layout                     #返回设置好的输入栏

    def set_preview_layout(self):#设置preview的输入栏
        preview_layout = QHBoxLayout()#输入栏水平放置

        self.band_filter_label = QLabel(self)
        self.band_filter_label.setFixedSize(130, 30)
        self.band_filter_label.setText("Freq-Band Filter:  ")
        preview_layout.addWidget(self.band_filter_label)

        #设置frequency filter的上下截止频率
        self.freq_lo_label = QLabel(self)
        self.freq_lo_label.setText("Freq lo:")
        self.freq_lo_label.setFixedSize(80, 30)
        preview_layout.addWidget(self.freq_lo_label, alignment=QtCore.Qt.AlignLeft)

        self.freq_lo_input = QTextEdit(self)
        self.freq_lo_input.setFixedSize(50, 30)
        self.freq_lo_input.setText(str(self.freq_lo/1e6)) # NOTE we transfer frequency unit to MHz
        preview_layout.addWidget(self.freq_lo_input, alignment=QtCore.Qt.AlignLeft)

        self.freq_lo_unit_label = QLabel(self)
        self.freq_lo_unit_label.setFixedSize(50, 30)
        self.freq_lo_unit_label.setText("MHz")
        preview_layout.addWidget(self.freq_lo_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.freq_hi_label = QLabel(self)
        self.freq_hi_label.setFixedSize(80, 30)
        self.freq_hi_label.setText("Freq hi:")
        preview_layout.addWidget(self.freq_hi_label, alignment=QtCore.Qt.AlignLeft)

        self.freq_hi_input = QTextEdit(self)
        self.freq_hi_input.setFixedSize(50, 30)
        self.freq_hi_input.setText(str(self.freq_hi / 1e6))  # NOTE we transfer frequency unit to MHz
        preview_layout.addWidget(self.freq_hi_input, alignment=QtCore.Qt.AlignLeft)

        self.freq_hi_unit_label = QLabel(self)
        self.freq_hi_unit_label.setFixedSize(50, 30)
        self.freq_hi_unit_label.setText("MHz")
        preview_layout.addWidget(self.freq_hi_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.input_preview_btn = QPushButton(self)
        self.input_preview_btn.setText("Preview")
        self.input_preview_btn.setFixedSize(80, 30)
        self.input_preview_btn.clicked.connect(self.on_preview_clicked)
        preview_layout.addWidget(self.input_preview_btn, alignment=QtCore.Qt.AlignLeft)

        preview_layout.setContentsMargins(0, 0, 0, 0)#使各标签紧密排列
        preview_layout.addStretch(0)
        return preview_layout            #返回设置好的输入栏

    def on_time_window(self):#获得time window的开始时间和结束时间（float型）
        self.time_from = float(self.from_input.toPlainText())
        self.time_to = float(self.to_input.toPlainText())

        self.time_from_ind = self.time_from * self.fs/1e6 #将time index（0~6000）转化为time（0~12 us）
        if int(self.time_to) == -1:
            self.time_to_ind = -1 #如果输入时间大于12us，将时间置为最大值，此处为12us
        else:
            self.time_to_ind = self.time_to * self.fs/1e6

        self.time_window_z = self.z[int(self.time_from_ind): int(self.time_to_ind)]#截取数据中time window所选取的那段
        print("time_window",self.time_window_z.shape)

        if self.mode == "plot":#plot 模式下plot time_domain 和 freq_domain
            self.init_window(mode=self.mode)
            self.canvas.plot_time_window_z(self.time_window_z, start_time=self.time_from)
            self.canvas.plot_freq_domain(self.time_window_z)
        if self.mode == "env_fig":#env_fig 模式下画出四张图
            self.on_more_fig_plot()

    def on_time_window_apply_all(self):#将time window的开始与结束时间保存以便其他函数使用
        self.on_time_window()
        self.time_window_callback(self.time_from_ind, self.time_to_ind)#返回time index

    def set_time_window_callback(self, time_window_update):#将time window apply to all之后，更新所有点的time window
        self.time_window_callback = time_window_update

    def on_cursor(self, qaction):#设置光标
        print(qaction.text() + " is triggered!")
        if qaction.text() == "LeftBound":
            print("LeftBound")
            self.canvas.set_on_cursor(self.on_left_bound)
            self.canvas.set_on_click(self.on_click)
        elif qaction.text() == "RightBound":
            print("RightBound")
            self.canvas.set_on_cursor(self.on_right_bound)
            self.canvas.set_on_click(self.on_click)
        elif qaction.text() == "ExitCursor":
            self.canvas.set_on_cursor(None)

    def on_tool(self, qaction):

        if self.left_bound == None or self.right_bound == None:#光标未设置好时不能获取最值
            return
        #获取光标内最小值
        if qaction.text() == "Min":
            print("Min")
            bound_z = self.time_window_z[int(self.left_bound): int(self.right_bound)]
            min_z = np.min(bound_z)
            min_z_ind = np.argmin(bound_z) + int(self.left_bound)
            # NOTE here we should plus time from to get a correct time position in figure
            ind_to_time = min_z_ind * 1.0 / (self.fs/1e6) + self.time_from
            print("min_z_ind", min_z_ind)
            print("min_z", min_z)
            self.canvas.draw_point(ind_to_time, min_z)
        #获取光标内最大值
        elif qaction.text() == "Max":
            bound_z = self.time_window_z[int(self.left_bound): int(self.right_bound)]
            max_z = np.max(bound_z)
            max_z_ind = np.argmax(bound_z) + int(self.left_bound)
            # NOTE here we should plus time from to get a correct time position in figure
            ind_to_time = max_z_ind * 1.0 / (self.fs/1e6)+ self.time_from
            print("max_z_ind", max_z_ind)
            print("ind_to_time", ind_to_time)
            print("max_z", max_z)
            self.canvas.draw_point(ind_to_time, max_z)

    def on_click(self, event):#固定光标后显示光标值
        self.canvas.set_on_cursor(None)
        x, y = event.xdata, event.ydata
        ymin = np.min(self.time_window_z)
        ymax = np.max(self.time_window_z)
        print('x=%1.2f, y=%1.2f' % (x, y))#光标值显示一位小数
        print("time from ", self.time_from, "time to", self.time_to)
        if self.bound_side == "left":
            # be careful, x got from figure include time, should minus time from so that we can get right index for time filter z
            self.left_bound = (x - self.time_from) * self.fs/1e6 # fs freq unit MHz
            print("left bound", self.left_bound)
            self.canvas.draw_bound(x, ymin, ymax, "left")
        elif self.bound_side == "right":
            self.right_bound = (x - self.time_from) * self.fs/1e6 # fs freq unit MHz
            print("right bound", self.right_bound)
            self.canvas.draw_bound(x, ymin, ymax, "right")

        self.canvas.set_on_click(None)#移动光标之后将原来的光标清除

    def on_left_bound(self, event):#获取光标左边界
        x, y = event.xdata, event.ydata
        self.bound_side = "left"
        if x is not None and y is not None:
            # print('x=%1.2f, y=%1.2f' % (x, y))
            ymin = np.min(self.time_window_z)
            ymax = np.max(self.time_window_z)
            self.canvas.draw_cursor(x, ymin, ymax)

    def on_right_bound(self, event):#获取光标右边界
        x, y = event.xdata, event.ydata
        self.bound_side = "right"
        if x is not None and y is not None:
            # print('x=%1.2f, y=%1.2f' % (x, y))
            ymin = np.min(self.time_window_z)
            ymax = np.max(self.time_window_z)
            self.canvas.draw_cursor(x, ymin, ymax)

    def on_preview_clicked(self):#在preview界面需要进行的操作
        #获取filter上下截止频率
        self.freq_hi = float(self.freq_hi_input.toPlainText())*1e6
        self.freq_lo = float(self.freq_lo_input.toPlainText())*1e6 #NOTE: MHz to Hz

        self.init_window("preview")#刷新界面

        self.band_filter_z = filtfilter(self.time_window_z, self.freq_lo, self.freq_hi, self.fs)#获取滤波后的数据
        self.canvas.plot_z(self.time_window_z, self.time_from)#plot time domain
        self.canvas.plot_band_filter_z(self.band_filter_z, self.time_from)#plot filtered time domain figure
        self.canvas.plot_freq_domain(self.band_filter_z)#plot filtered frequency domain figure

    def on_time_domain_plot(self):#将界面模式设置为"plot",画时域图与频域图
        self.mode = "plot"
        self.on_time_window()#刷新界面

    def on_more_fig_plot(self):#将界面模式设置为"env_fig",画该点的另外四张图
        env_z = calc_env_z(self.time_window_z)
        chA = self.data["all_data"]["A"][self.data_index, :]
        print("A", self.data["all_data"]["A"].shape)
        print("chA", chA.shape)

        self.init_window(mode='env_fig')
        self.canvas.plot_time_window_z(self.time_window_z, start_time=self.time_from)#plot time_domain fig
        self.canvas.plot_freq_domain(self.time_window_z)#plot frequency domain fig
        self.canvas.plot_env_z(env_z, start_time=self.time_from)#plot amplitude envelope
        self.canvas.plot_chA(chA)#plot chA

    def right_menu_show(self):#设置右键菜单Savefig，保存图片
        try:
            self.contextMenu = QMenu()
            self.act_save = self.contextMenu.addAction('SaveFig')
            self.contextMenu.popup(QCursor.pos())

            self.act_save.triggered.connect(self.save_fig)
            self.contextMenu.show()
        except Exception as e:
            print(e)

    def save_fig(self):#设置图片保存路径与方式
        fileName, ok = QFileDialog.getSaveFileName()#获得保存路径
        print(fileName)
        self.canvas.fig.savefig(fileName, format='png', transparent=False, dpi=300, pad_inches = 0)