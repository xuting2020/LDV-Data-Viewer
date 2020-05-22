
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtWidgets

from PyQt5.QtCore import QDir
from PyQt5.QtGui import QIcon, QPixmap, QFont, QCursor
from PyQt5.QtCore import QDate

import sys

from data import *
from mpl_canvas import *
from signal_window import SignalWindow
from phase_amplitude_window import PhaseAmplitudeWindow
from process import *


class MainWindow(QMainWindow):#设置mainwindow：LDV Data Viewer
    '''
    main window: LDV Data Viewer
    init args:
        freq_hi(default: 21e6)
        freq_lo(default: 19e6)
        fs(read from config files)
        filter_applied(default: False; to mark if "apply" button is clicked)
        select_applied(default: False; to mark if user has switched view and chose points
        time_from_ind(default: 0; the start time index of time window)
        time_to_ind(default: 6000; the end time index of time window)
    '''
    def __init__(self,parent=None):

        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("LDV Data Viewer")
        self.resize(600, 600)
        self.init_menubar()

        # NOTE All the frequency unit in the program is Hz, we only use MHz to input and display text box
        self.freq_hi = 21e6
        self.freq_lo = 19e6
        self.fs = 500e6#初始化filter的频率参数（后面要把这个从config files里面读取出来）
        self.filter_applied = False #初始不应用filter
        self.select_applied = False #choose point初始化，不选择
        self.time_from_ind = 0
        self.time_to_ind = 6000

    def init_menubar(self):#设置main window 的菜单栏
        '''
        to set the menubar of main window(LDV Data Viewer)
        '''
        self.menubar = self.menuBar()  # 获取窗体的菜单栏

        self.file = self.menubar.addMenu("File")
        self.file.addAction("New File")

        self.open = QAction("Open", self)# open compressed file
        self.open.setShortcut("Ctrl+O")  # 设置快捷键
        self.file.addAction(self.open)

        self.save = QAction("Save", self)
        self.save.setShortcut("Ctrl+S")  # 设置快捷键
        self.file.addAction(self.save)

        self.compress = QAction("Compress",self)#压缩数据文件
        self.file.addAction(self.compress)

        self.edit = self.file.addMenu("Edit")
        self.edit.addAction("copy")  # Edit下这是copy子项
        self.edit.addAction("paste")  # Edit下设置paste子项

        self.quit = QAction("Quit", self)  # 注意如果改为：self.file.addMenu("Quit") 则表示该菜单下必须柚子菜单项；会有>箭头
        self.file.addAction(self.quit)

        self.file.triggered[QAction].connect(self.on_file_menu)


    def on_file_menu(self,qaction):
        print(qaction.text()+" is triggered!")
        if qaction.text() == "Open":
            print("open file")
            self.open_file()
            # self.data = self.open_fake_file()
            self.update_menubar()
            self.show_scatter(scatter_name="bc_scatter", data=self.data)#默认主界面初始为bc_scatter以选取点
        elif qaction.text() == "Compress":
            self.compress_file()

    def open_file(self):
        '''
        read compressed file and store needed data
        stored args:
            data['z'] = data['all_data']['B'] * 1e9(unit is nm)
            data['max_dz'] = max(z) - min(z)
            data['max_dz_show'] = data['max'].copy()(max_dz_show can be modifiled)
            max_id = data['z'].shape[0]-1(means the number of points）
            time_window_indexes: default as 0-12 us(index: 0-6000)
            time_window_z: z in the interval of time window
        '''
        file_name, _ = QFileDialog.getOpenFileName()#获取文件路径
        self.data = import_compressed_data(file_name)#读取数据
        # print('data', self.data.keys())
        self.data["all_data"]["B"] *= 1e9 # z to nano
        # print('alldata', self.data["all_data"].keys())
        # print("B", self.data["all_data"]["B"].shape)
        self.data["z"] = self.data["all_data"]["B"]#获取 z
        # print('z', self.data["z"].shape)
        self.data["max_dz"] = np.max(self.data["z"], axis=1) - np.min(self.data["z"], axis=1)#找到z的最大值
        self.data["max_dz_show"] = self.data["max_dz"].copy()#copy max_dz，max_dz_show可在画图时修改
        self.max_id = self.data['z'].shape[0]-1#找到z的最大index，即点的个数

        time_window_indexs = list(range(int(self.time_from_ind), int(self.time_to_ind)))#初始time window为0-12us
        self.time_window_z = self.data["z"][:, time_window_indexs]#根据time window 参数来获取z的值
        # print("time_window_z", self.time_window_z.shape)

    def compress_file(self):
        '''
        compress data folder and save as 'compressed' in original folder
        '''
        folder_name = QFileDialog.getExistingDirectory()#获取文件夹名称
        x, y, t, allData = import_folder(folder_name, ['A', 'B'], 'mean')
        data = {}
        data['x'] = x
        data['y'] = y
        data['time'] = t
        data['all_data'] = allData

        save_file = os.path.join(folder_name, 'compressed')#压缩后的文件保存在原文件夹下面，名为 compressed
        save_dict_to_hdf5(data, save_file)#将folder压缩为hdf5 file

        info_box = QMessageBox(self)#显示工作状态
        info_box.setWindowTitle("compress")
        info_box.setText("Compress Done!")
        info_box.exec()
        info_box.show()

    def update_menubar(self):
        self.more_info = self.menubar.addMenu("MoreInfo")
        # self.fig_3d = self.menubar.addMenu("Fig3d")

    def show_scatter(self, scatter_name, data):#画出散点图，有两幅
        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget_name = scatter_name

        l = QtWidgets.QVBoxLayout(self.main_widget)

        if self.main_widget_name == "xy_scatter":#这个散点图使用数据 z,图形呈椭圆形，蓝色
            self.canvas = XYMplCanvas(self.main_widget, width=5, height=4, dpi=100)
            self.canvas.plot_scatter(data)
            self.canvas.set_on_pick(self.on_pick)
        elif self.main_widget_name == "bc_scatter":#这个散点图使用了数据z和contrast，主要用于选点，红色
            self.canvas = BCMplCanvas(self.main_widget, width=5, height=4, dpi=100)
            self.canvas.plot_scatter(data)
            self.canvas.set_on_pick(self.on_pick)


        l.addWidget(self.canvas)
        input_layout = self.set_input_layout()
        l.addLayout(input_layout)#设置输入栏

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)#设置主界面

        self.main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(self.right_menu_show)#设置右键菜单

        self.pick_event_flag = False


    def on_pick(self, event):# pick point and get its index
        print("point", event.ind[0], "clicked")
        self.pick_event_flag = True
        self.picked_ind = event.ind[0]

    def set_input_layout(self):#设置输入栏
        input_layout = QHBoxLayout()

        self.band_filter_label = QLabel(self)
        self.band_filter_label.setFixedSize(80, 30)
        self.band_filter_label.setText("Band Filter:  ")#设置滤波器label
        input_layout.addWidget(self.band_filter_label)

        self.freq_hi_label = QLabel(self)
        self.freq_hi_label.setFixedSize(50, 30)
        self.freq_hi_label.setText("Freq hi:")
        input_layout.addWidget(self.freq_hi_label, alignment = QtCore.Qt.AlignLeft)

        self.freq_hi_input = QTextEdit(self)
        self.freq_hi_input.setFixedSize(50,30)
        self.freq_hi_input.setText(str(self.freq_hi/1e6)) # NOTE we transfer frequency unit to MHz
        input_layout.addWidget(self.freq_hi_input, alignment = QtCore.Qt.AlignLeft)

        self.freq_hi_unit_label = QLabel(self)
        self.freq_hi_unit_label.setFixedSize(50, 30)
        self.freq_hi_unit_label.setText("MHz")
        input_layout.addWidget(self.freq_hi_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.freq_lo_label = QLabel(self)
        self.freq_lo_label.setText("Freq lo:")
        self.freq_lo_label.setFixedSize(50,30)
        input_layout.addWidget(self.freq_lo_label, alignment = QtCore.Qt.AlignLeft)

        self.freq_lo_input = QTextEdit(self)
        self.freq_lo_input.setFixedSize(50,30)
        self.freq_lo_input.setText(str(self.freq_lo/1e6)) # NOTE we transfer frequency unit to MHz
        input_layout.addWidget(self.freq_lo_input, alignment = QtCore.Qt.AlignLeft)

        self.freq_lo_unit_label = QLabel(self)
        self.freq_lo_unit_label.setFixedSize(50, 30)
        self.freq_lo_unit_label.setText("MHz")
        input_layout.addWidget(self.freq_lo_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.freq_fs_label = QLabel(self)
        self.freq_fs_label.setText("FS:")
        self.freq_fs_label.setFixedSize(20,30)
        input_layout.addWidget(self.freq_fs_label, alignment = QtCore.Qt.AlignLeft)

        self.freq_fs_input = QTextEdit(self)
        self.freq_fs_input.setFixedSize(50,30)
        self.freq_fs_input.setText(str(self.fs/1e6)) # NOTE we transfer frequency unit to MHz
        input_layout.addWidget(self.freq_fs_input, alignment = QtCore.Qt.AlignLeft)

        self.fs_unit_label = QLabel(self)
        self.fs_unit_label.setFixedSize(50, 30)
        self.fs_unit_label.setText("MHz")
        input_layout.addWidget(self.fs_unit_label, alignment=QtCore.Qt.AlignLeft)

        self.input_apply_btn = QPushButton(self)
        self.input_apply_btn.setText("Apply")
        self.input_apply_btn.setFixedSize(50,30)
        self.input_apply_btn.clicked.connect(self.on_apply_all) # apply band filter to all points
        input_layout.addWidget(self.input_apply_btn, alignment = QtCore.Qt.AlignLeft)

        self.choose_point_label = QLabel(self)
        self.choose_point_label.setFixedSize(90, 30)
        self.choose_point_label.setText("Choose Point")
        input_layout.addWidget(self.choose_point_label)

        self.point_input = QLineEdit(self)
        self.point_input.setFixedSize(50,30)
        self.point_input.setText(str(self.max_id))
        self.point_input.editingFinished.connect(self.on_choose_point)#use index to mark a point
        input_layout.addWidget(self.point_input)

        self.switch_view_btn = QPushButton(self)
        self.switch_view_btn.setFixedSize(100, 30)
        self.switch_view_btn.setText("SwitchView")
        self.switch_view_btn.clicked.connect(self.on_switch_view_btn)#switch between bc_sactter and xy_scatter
        input_layout.addWidget(self.switch_view_btn)

        input_layout.setContentsMargins(0,0,0,0)#各label紧密排列
        input_layout.addStretch(0)

        return input_layout


    def on_apply_all(self):#获取高低截止频率
        self.freq_lo = float(self.freq_lo_input.toPlainText()) * 1e6 # input MHz to Hz
        self.freq_hi = float(self.freq_hi_input.toPlainText()) * 1e6
        print(self.freq_hi)
        print(self.freq_lo)

        self.filter_z = filtfilter(self.time_window_z, self.freq_lo, self.freq_hi, self.fs)#得到滤波后的值
        print("filter_z",self.filter_z.shape)
        self.data["all_data"]["B"] = self.filter_z
        self.data["max_dz"] = np.max(self.filter_z, axis=1) - np.min(self.filter_z, axis=1)
        self.data["max_dz_show"] = self.data["max_dz"].copy()#将滤波后的值copy，用于画图时对其修改

        self.filter_applied = True #将filter_applied置为True,否则画三维图时会弹出warning

    def on_choose_point(self):#输入点的index选点功能
        self.point_id = int(self.point_input.text())
        #为了避免输入的index溢出，始终让输入值小于等于最大的index
        if self.point_id > self.max_id:
            self.point_id = self.max_id
            self.point_input.setText(str(self.max_id))
        print("point id", self.point_id)
        #在两幅散点图上均可使用choose point功能
        if self.main_widget_name == 'xy_scatter':
            self.point_x_axis= self.data['x'][self.point_id]
            self.point_y_axis = self.data['y'][self.point_id]
            print("point_x_axis",self.point_x_axis)
            print("point_y_axis",self.point_y_axis)
            self.canvas.mark_point(x=self.point_x_axis, y=self.point_y_axis)
        elif self.main_widget_name == 'bc_scatter':
            z = np.mean(self.data["all_data"]["B"], axis=2)
            amplitude = np.max(np.abs(z), axis=1)
            self.point_y_axis = np.log(self.data["all_data"]["contrast"])[self.point_id]
            self.point_x_axis = np.log(amplitude)[self.point_id]
            self.canvas.mark_point(x=self.point_x_axis, y=self.point_y_axis)

    def on_switch_view_btn(self):#切换两幅散点图
        if self.main_widget_name == "xy_scatter":#判断当前的scatter图类型
            self.show_scatter("bc_scatter", self.data)#切换到另一幅scatter图
        elif self.main_widget_name == "bc_scatter":
            self.show_scatter("xy_scatter", self.data)

    def right_menu_show(self):#设置右键菜单
        try:
            self.contextMenu = QMenu()
            #各右键名称
            self.act_property = self.contextMenu.addAction('Property')
            self.act_plot = self.contextMenu.addAction('Plot')
            self.act_plot_pha_amp = self.contextMenu.addAction('Phase Amp')
            self.act_preview = self.contextMenu.addAction('Preview Filter')
            self.act_cursor = self.contextMenu.addAction('Cursor')
            self.act_save = self.contextMenu.addAction('SaveFig')
            self.contextMenu.popup(QCursor.pos())  # 2菜单显示的位置
            #各右键功能连接的函数
            self.act_property.triggered.connect(self.property_handler)
            self.act_plot.triggered.connect(self.plot_handler)
            self.act_plot_pha_amp.triggered.connect(self.plot_phase_amp)
            self.act_preview.triggered.connect(self.preview_handler)
            self.act_cursor.triggered.connect(self.cursor_handler)
            self.act_save.triggered.connect(self.save_fig)
            self.contextMenu.show()
        except Exception as e:
            print(e)

    def property_handler(self):#右键菜单property，显示point info
        print('property_handler')
        if self.pick_event_flag:
            print('id', self.picked_ind)
            point_info_box = QMessageBox(self)  
            point_info_box.setWindowTitle("Info")
            if self.main_widget_name == "xy_scatter":#显示点的id，以及点的坐标
                info = "id: " + str(self.picked_ind) \
                 + "\nx : " + str(self.data["x"][self.picked_ind]) \
                 + "\ny : " + str(self.data["y"][self.picked_ind])
            elif self.main_widget_name == "bc_scatter":
                z = np.mean(self.data["all_data"]["B"], axis=2)
                amplitude = np.max(np.abs(z), axis=1)
                temp_y = np.log(self.data["all_data"]["contrast"])
                temp_x = np.log(amplitude)
                info = "id: " + str(self.picked_ind) \
                    + "\nx: " + str(temp_x[self.picked_ind]) \
                    + "\ny: " + str(temp_y[self.picked_ind])

            point_info_box.setText(info)
            point_info_box.exec()
            point_info_box.show()

    def time_window_update(self, time_from_ind, time_to_ind):#更新time window
        #获得time window参数并保存
        self.time_from_ind = time_from_ind
        self.time_to_ind = time_to_ind
        time_window_indexs = list(range(int(self.time_from_ind), int(self.time_to_ind)))
        self.time_window_z = self.data["z"][:, time_window_indexs]
        print("time_window_z", self.time_window_z.shape)

    def plot_handler(self):#右键菜单plot功能实现
        print('plot_handler')
        if self.pick_event_flag:
            print('id', self.picked_ind)
            #将各参数传入SignalWindow
            self.signal_win = SignalWindow(freq_hi=self.freq_hi,freq_lo=self.freq_lo,fs=self.fs,\
                                           time_from_ind=self.time_from_ind, time_to_ind=self.time_to_ind)
            self.signal_win.set_input_data(self.data)
            self.signal_win.plot_z(self.picked_ind)#通过picked_ind画出该点的时域图
            self.signal_win.plot_freq_domain(self.picked_ind)#通过picked_ind画出该点的频域图
            # 将Signal Window里面time window参数（apply all之后）传递到主界面
            self.signal_win.set_time_window_callback(self.time_window_update)
            self.signal_win.show()

    def preview_handler(self):#右键菜单preview功能
        print('preview_handler')
        if self.pick_event_flag:
            print('id', self.picked_ind)
            self.signal_win = SignalWindow(mode='preview',freq_hi=self.freq_hi,freq_lo=self.freq_lo,fs=self.fs,\
                                           time_from_ind=self.time_from_ind, time_to_ind=self.time_to_ind)
            self.signal_win.set_input_data(self.data)
            self.signal_win.plot_z(self.picked_ind)#通过picked_ind画出该点的时域图
            self.signal_win.plot_band_filter_z(self.picked_ind)#通过picked_ind画出该点滤波后的时域图
            self.signal_win.plot_freq_domain(self.picked_ind, filtered=True)#通过picked_ind画出该点滤波后的频域图
            self.signal_win.show()

    def plot_phase_amp(self):#右键菜单PhaAmp功能，进入新的窗口

        if not self.filter_applied:
            info_box = QMessageBox(self)
            info_box.setWindowTitle("Warning")#没有apply band filter将会提出warning并返回原界面
            info_box.setText("Filter not applied!")
            info_box.exec()
            info_box.show()
            return

        if not self.select_applied:
            info_box = QMessageBox(self)
            info_box.setWindowTitle("Warning")#没有选择点直接在bc_scatter进入PhaAmp窗口会出现warning
            info_box.setText("Switchview and choose point!")
            info_box.exec()
            info_box.show()
            return

        self.pha_amp_win = PhaseAmplitudeWindow()

        x = self.data['x'][self.lt_indexs]
        y = self.data['y'][self.lt_indexs]
        filter_z = self.filter_z[self.lt_indexs]
        self.pha_amp_win.set_input_data(x, y, filter_z)#传入PhaAmp窗口需要的数据
        self.pha_amp_win.plot()
        self.pha_amp_win.show()

    def cursor_handler(self):#右键菜单cursor功能
        if self.main_widget_name == "xy_scatter":#xy_scatter不需要cursor，pass掉
            pass
        elif self.main_widget_name == "bc_scatter":#bc_scatter利用cursor选择点，获得cursor横坐标
            self.canvas.set_on_cursor(self.on_cursor_move)
            self.canvas.set_on_click(self.on_cursor_click)

    def on_cursor_move(self, event):#plot cursor
        x, y = event.xdata, event.ydata
        if x is not None and y is not None:
            print('x=%1.2f, y=%1.2f' % (x, y))
            z = self.data["all_data"]["B"]
            amplitude = np.max(np.abs(z), axis=1)
            print(amplitude.shape)
            temp_y = np.log(self.data["all_data"]["contrast"])
            temp_x = np.log(amplitude)
            ymin = np.min(temp_y)
            ymax = np.max(temp_y)
            self.canvas.draw_cursor(x, ymin, ymax)

    def on_cursor_click(self, event):#cursor固定后获得cursor的值（横坐标）用于选点
        print("cursor click")

        self.canvas.set_on_cursor(None)
        x, y = event.xdata, event.ydata #捕捉鼠标的横纵坐标
        print('x=%1.2f, y=%1.2f' % (x, y))
        z = self.data["all_data"]["B"]
        amplitude = np.max(np.abs(z), axis=1)
        print(amplitude.shape)
        temp_y = np.log(self.data["all_data"]["contrast"])
        temp_x = np.log(amplitude)
        ymin = np.min(temp_y)
        ymax = np.max(temp_y)
        self.canvas.draw_bound(x, ymin, ymax)

        self.lt_indexs = np.where(temp_x < x)[0]#得到不符合要求的点的index
        gt_indexs = np.where(temp_x >= x)[0]#得到符合要求的点的index
        print("lt_indexs",self.lt_indexs, self.lt_indexs.shape)

        lt_max_dz = self.data['max_dz'][self.lt_indexs]
        print('lt_max_dz', lt_max_dz.shape)
        min_lt_max_dz = np.min(lt_max_dz)*0.1#将不符合要求的点的z值缩小为符合要求的点的值的十分之一，即饱和掉
        self.data['max_dz_show'] = self.data['max_dz'].copy()#将筛选后的数据保存到max_dz_show
        self.data['max_dz_show'][gt_indexs] = min_lt_max_dz

        self.select_applied = True #筛选完成，将select_applied置为True，避免warning

    def save_fig(self):#右键菜单save_fig
        fileName, ok = QFileDialog.getSaveFileName()
        print(fileName)
        self.canvas.fig.savefig(fileName, format='png', transparent=False, dpi=300, pad_inches = 0)

# if __name__ == "__main__":
#     pass