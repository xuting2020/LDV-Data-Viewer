from PyQt5 import QtCore, QtWidgets
from data_import2 import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.tri import Triangulation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
#初始化窗口
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot_scatter(self, data):
        raise NotImplemented

    def set_on_pick(self, on_pick):
        self.fig.canvas.mpl_connect('pick_event', on_pick)

class XYMplCanvas(MplCanvas):#这个类实现的是椭圆形散点图上的功能
#继承MplCanvas
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(XYMplCanvas, self).__init__()
        self.arrow = None

    def plot_scatter(self, data):#画椭圆形散点图
        x = data["x"]
        y = data["y"]
        dz = data["max_dz_show"]
        min_x = np.min(x)
        max_x = np.max(x)
        min_y = np.min(y)
        max_y = np.max(y)
        self.axes.set_xlim([min_x-0.0001, max_x+0.0001])
        self.axes.set_ylim([min_y-0.0001, max_y+0.0001])
        self.axes.scatter(x, y, picker=5, c=dz)

    def mark_point(self,x,y):#choose point功能，用小箭头标出选择的点
        if self.arrow is not None:
            self.arrow.remove()
            self.arrow = None
        base_width = 0.000002
        self.arrow = self.axes.arrow(x,y-base_width*10,0,4*base_width,width=base_width,color='r')
        self.axes.figure.canvas.draw()


class BCMplCanvas(MplCanvas):#这个类实现的是红色的筛选点的散点图上的功能
    # 继承MplCanvas
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        super(BCMplCanvas, self).__init__()
        self.arrow = None #初始化choose point的小箭头，不显示

        self.lines = None #初始化cursor（不显示 cursor）
        self.cid = None #初始化cursor状态
        self.on_click_id = None #初始化选择点的id
        self.bound = None #初始化cursor边界
        self.bound_text = None #初始化cursor值

    def mark_point(self,x,y):#用箭头arrow标记点
        if self.arrow is not None:#选择新的点时将原来的arrow清除掉
            self.arrow.remove()
            self.arrow = None
        base_width = 0.01 #设置箭头粗细
        self.arrow = self.axes.arrow(x,y-base_width*10,0,4*base_width,width=base_width,color='r')
        self.axes.figure.canvas.draw()

    def plot_scatter(self, data):#画用于筛选的散点图
        z = data["all_data"]["B"]
        amplitude = np.max(np.abs(z), axis=1)
        print(amplitude.shape)
        temp_y = np.log(data["all_data"]["contrast"])
        temp_x = np.log(amplitude)
        # dz = np.max(z, axis=1) - np.min(z, axis=1)
        self.axes.scatter(temp_x, temp_y, picker=5, c=temp_y, cmap=plt.get_cmap('Reds'))

    def set_on_cursor(self, on_cursor):#设置cursor的状态
        if self.cid is not None and on_cursor is None:
            self.fig.canvas.mpl_disconnect(self.cid)
            return
        self.cid = self.fig.canvas.mpl_connect('motion_notify_event', on_cursor)#cursor为移动状态

    def set_on_click(self, on_click):#click cursor 之后固定cursor，cursor进入固定状态
        if self.on_click_id is not None and on_click is None:
            self.fig.canvas.mpl_disconnect(self.on_click_id)
            return
        self.on_click_id = self.fig.canvas.mpl_connect('button_press_event', on_click)

    def draw_cursor(self, x, ymin, ymax):#画出cursor
        if self.lines is not None:
            self.lines.remove() #remove残留的cursor
            self.lines = None
        self.lines = self.axes.vlines(x, ymin, ymax, colors='r', linestyles = "dashed")#设置cursor的形状，颜色等
        self.axes.figure.canvas.draw()

    def draw_bound(self, x, ymin, ymax):#获得cursor的坐标并显示
        if self.lines is not None:
            self.lines.remove()
            self.lines = None

        if self.bound is not None:
            self.bound.remove()

        if self.bound_text is not None:
            self.bound_text.remove()

        self.bound = self.axes.vlines(x, ymin, ymax, colors='r', linestyles="dashed")
        self.bound_text = self.axes.text(x, ymax, "{:.2f}".format(x)) #显示两位小数

        self.axes.figure.canvas.draw()

class ZMplCanvas(FigureCanvas): #该类用于画单个点的全部图

    def __init__(self, parent=None, ax_num=2, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        if ax_num == 2:
            self.axes = self.fig.add_subplot(211)
            self.axes2 = self.fig.add_subplot(212)
        elif ax_num == 4:
            self.axes = self.fig.add_subplot(221)
            self.axes2 = self.fig.add_subplot(222)
            self.axes3 = self.fig.add_subplot(223)
            self.axes4 = self.fig.add_subplot(224)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.lines = None
        self.left_bound = None
        self.right_bound = None
        self.cid = None
        self.on_click_id = None
        self.left_bound_text = None
        self.right_bound_text = None

    def plot_z(self, z, start_time=0.0):
        Fs = 500e6
        t = np.arange(len(z)) / Fs * 1e6 # to us
        t += start_time
        self.axes.plot(t, z)
        self.axes.set_xlabel('Time (us)')
        self.axes.set_ylabel('Amplitude (nm)')

    def plot_freq_domain(self, z):

        Fs = 500e6  # sampling rate采样率
        n = len(z) # length of the signal
        print('len z', n)
        k = np.arange(n)
        T = n / Fs
        frq = k / T  # two sides frequency range
        frq1 = frq[range(int(n / 2))]  # one side frequency range
        frq1 /= 1e6 # to MHz
        fft_z = np.fft.fft(z) / n  # fft computing and normalization 归一化
        fft_z_amp = abs(fft_z[range(int(n / 2))])

        self.axes2.plot(frq1, fft_z_amp)
        self.axes2.set_xlabel('Frequency (MHz)')
        self.axes2.set_ylabel('Amplitude')


    def plot_band_filter_z(self, band_filter_z, start_time=0.0):
        Fs = 500e6
        t = np.arange(len(band_filter_z)) / Fs * 1e6  # to us
        t += start_time #加上time window的开始时间，使得cursor坐标正确
        self.axes.plot(t, band_filter_z)

    def plot_time_window_z(self, time_window_z, start_time=0.0):
        Fs = 500e6
        t = np.arange(len(time_window_z)) / Fs * 1e6  # to us
        t += start_time
        self.axes.plot(t, time_window_z)
        self.axes.set_xlabel('Time (us)')
        self.axes.set_ylabel('Amplitude (nm)')

    def set_on_cursor(self, on_cursor):
        if self.cid is not None and on_cursor is None:
            self.fig.canvas.mpl_disconnect(self.cid)
            return
        self.cid = self.fig.canvas.mpl_connect('motion_notify_event', on_cursor)

    def set_on_click(self, on_click):
        if self.on_click_id is not None and on_click is None:
            self.fig.canvas.mpl_disconnect(self.on_click_id)
            return
        self.on_click_id = self.fig.canvas.mpl_connect('button_press_event', on_click)

    def draw_cursor(self, x, ymin, ymax):
        if self.lines is not None:
            self.lines.remove()
            self.lines = None
        self.lines = self.axes.vlines(x, ymin, ymax, colors='r', linestyles = "dashed")
        self.axes.figure.canvas.draw()

    def draw_bound(self, x, ymin, ymax, bound):
        if self.lines is not None:
            self.lines.remove()
            self.lines = None

        if bound == "left":
            if self.left_bound is not None:
                self.left_bound.remove()
            if self.left_bound_text is not None:
                self.left_bound_text.remove()
            self.left_bound = self.axes.vlines(x, ymin, ymax, colors='r', linestyles="dashed")
            self.left_bound_text = self.axes.text(x, ymax, "{:.2f}".format(x))
        elif bound == "right":
            if self.right_bound is not None:
                self.right_bound.remove()
            if self.right_bound_text is not None:
                self.right_bound_text.remove()
            self.right_bound = self.axes.vlines(x, ymin, ymax, colors='r', linestyles="dashed")
            self.right_bound_text = self.axes.text(x, ymax, "{:.2f}".format(x))
        self.axes.figure.canvas.draw()

    def draw_point(self, ind, z):
        self.axes.plot(ind, z, 'ro', markersize=3)
        self.axes.text(ind, z, "{:.2f}".format(z))
        self.axes.figure.canvas.draw()

    def clear(self):
        self.axes.clear()

    def plot_env_z(self, env_z,start_time=0.0):
        Fs = 500e6
        t = np.arange(len(env_z)) / Fs * 1e6 + start_time
        self.axes3.plot(t,env_z)
        self.axes3.set_xlabel('Time (us)')
        self.axes3.set_ylabel('Envelope (nm)')
        self.axes3.set_title("Envelope")

    def plot_chA(self,chA):
        Fs = 500e6
        t = np.arange(len(chA)) / Fs * 1e6
        self.axes4.plot(t, chA)
        self.axes4.set_xlabel('Time (us)')
        self.axes4.set_title("chA")


class PhaAmpMplCanvas(FigureCanvas):#该类用于画二维图和三维图

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        # plot 4 figures
        self.axes = self.fig.add_subplot(221)
        self.axes2 = self.fig.add_subplot(222)
        self.axes3 = self.fig.add_subplot(223)
        self.axes4 = self.fig.add_subplot(224,projection='3d')

        self.image3 = None
        self.cnt = 0


    def plot_phase(self,x,y,angle,V):# plot phase
        triangles = Triangulation(x, y)
        self.axes.tricontourf(triangles, angle, 20)
        image1 = self.axes.tricontourf(triangles, angle, V)
        self.fig.colorbar(image1, ax=self.axes)
        self.axes.set_title("Phase")
        # self.axes.figure.canvas.draw()

    def plot_amplitude(self,x,y,amplitude,V): # plot amplitude
        triangles = Triangulation(x, y)
        self.axes2.tricontourf(triangles, amplitude,V)
        image2 = self.axes2.tricontourf(triangles, amplitude, V)
        self.fig.colorbar(image2, ax=self.axes2)
        self.axes2.set_title("Amplitude")
        # self.axes2.figure.canvas.draw()

    def plot_smoothed_amplitude(self,x,y,amplitude,V): # plot smoothed amplitude
        self.cnt += 1
        print("cnt", self.cnt)
        triangles = Triangulation(x, y)
        self.axes3.tricontourf(triangles, amplitude, 20)
        self.image3 = self.axes3.tricontourf(triangles, amplitude, V) # image is colorbar
        self.fig.colorbar(self.image3, ax=self.axes3)
        self.axes3.set_title("Amplitude(Smoothed)"+str(self.cnt))
        # self.axes3.figure.canvas.draw()

    def plot_3D_smoothed_amplitude(self,x,y,amp_smoothed,cmap_in): # plot_3D_smoothed_amplitude
        # self.axes4 = Axes3D(self.fig)
        triangles = Triangulation(x, y)
        image4 = self.axes4.plot_trisurf(x, y, amp_smoothed, triangles=triangles.triangles, cmap=cmap_in)
        self.fig.colorbar(image4, ax=self.axes4)
        self.axes4.set_title("3D-Amplitude(Smoothed)")
        # self.axes4.figure.canvas.draw()

class PhaAmp3DMplCanvas(FigureCanvas): #这个class用来画3D图（包括3D_amplitude 和 3D_smoothed_amplitude）

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.axes = self.fig.add_subplot(111,projection='3d')

    def plot_3d_amplitude(self,x,y,amp,cmap_in):
        triangles = Triangulation(x, y)
        image = self.axes.plot_trisurf(x, y, amp, triangles=triangles.triangles, cmap=cmap_in)
        self.fig.colorbar(image, ax=self.axes)
        self.axes.figure.canvas.draw()