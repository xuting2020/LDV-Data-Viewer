import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QStatusBar, QWidget, QAction, QMenuBar, QMenu
from main_gui import MainWindow


if __name__=="__main__":
    app=QApplication(sys.argv)
    win=MainWindow()
    win.show()
    sys.exit(app.exec_())

