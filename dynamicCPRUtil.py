
import sys
import threading
from PyQt4.QtCore import QThread
import datetime
import time
from PyQt4 import QtCore
from PyQt4.QtGui import (QApplication, QSlider, QWidget, QVBoxLayout,
                         QHBoxLayout, QLabel, QPushButton)
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import random


def timedelta_to_time(the_timedelta):
    hours, remainder = map(int, divmod(the_timedelta.total_seconds(), 3600))
    minutes, seconds = map(int, divmod(remainder, 60))
    return datetime.time(hours, minutes, seconds)


class ThreadForRepeatedAction(threading.Thread):
    """
    A thread that calls a function repeatedly at a definite interval
    """

    def __init__(self, interval, func, *args, **kwargs):
        """

        :param interval: the interval the func is called
        :param func: the func to call
        :param args: args of the func
        :param kwargs: kwargs of the func
        """
        threading.Thread.__init__(self)
        self.interval = interval
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.again = True  # to stop the loop

    def run(self):
        while self.again:
            self.timer = threading.Timer(self.interval, self.func, self.args,
                                         self.kwargs)
            self.timer.setDaemon(True)
            self.timer.start()
            self.timer.join()

    def stop(self):
        self.again = False  # to stop the loop
        if self.timer.isAlive():
            self.timer.cancel()  # to kill the timer


class QThreadWaiting(QThread):
    """
    A thread that calls a function repeatedly at a definite interval
    """

    def __init__(self, interval, func, *args, **kwargs):
        """

        :param interval: the interval the func is called
        :param func: the func to call
        :param args: args of the func
        :param kwargs: kwargs of the func
        """
        QThread.__init__(self)
        self.interval = interval
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        time.sleep(self.interval)
        self.func(*self.args, **self.kwargs)

    def stop(self):
        if self.timer.isAlive():
            self.timer.cancel()  # to kill the timer


class QCustomSlider(QWidget):
    def __init__(self, sliderOrientation=None):
        super(QCustomSlider, self).__init__()
        self._slider = QSlider(sliderOrientation)

        self.setLayout(QVBoxLayout())

        self._labelTicksWidget = QWidget(self)
        self._labelTicksWidget.setLayout(QHBoxLayout())
        self._labelTicksWidget.layout().setContentsMargins(0, 0, 0, 0)

        self.layout().addWidget(self._slider)
        self.layout().addWidget(self._labelTicksWidget)

    def setTickLabels(self, listWithLabels):
        lengthOfList = len(listWithLabels)
        for index, label in enumerate(listWithLabels):
            label = QLabel(str(label))
            label.setContentsMargins(0, 0, 0, 0)
            if index > lengthOfList/3:
                label.setAlignment(QtCore.Qt.AlignCenter)
            if index > 2*lengthOfList/3:
                label.setAlignment(QtCore.Qt.AlignRight)
            self._labelTicksWidget.layout().addWidget(label)

    def setRange(self, mini, maxi):
        self._slider.setRange(mini, maxi)

    def setPageStep(self, value):
        self._slider.setPageStep(value)

    def setTickInterval(self, value):
        self._slider.setTickInterval(value)

    def setTickPosition(self, position):
        self._slider.setTickPosition(position)

    def setValue(self, value):
        self._slider.setValue(value)

    def onValueChangedCall(self, function):
        self._slider.valueChanged.connect(function)

# if __name__ == "__main__":
#     def stop_thread(the_thread):
#         the_thread.stop()
#
#     def print_time():
#         print(time.time())
#
#     duree = timedelta(hours=0, minutes=0, seconds=10)
#     the_signal = signal("time_elapsed")
#     the_signal.connect(stop_thread)
#
#     print("Main", threading.currentThread())
#
#     t0 = ThreadForRepeatedAction(1, print_time)
#     t1 = ThreadForRepeatedAction(duree.total_seconds(), the_signal.send, t0)
#
#     t1.start()
#     print("t1", t1.ident)
#     t0.start()
#     print("t0", t0.ident)
#     t1.again = False
#     print("before join")
#     t1.join()
#     print("after join")


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     print(threading.currentThread())
#
#     def my_print(what):
#         print(what)
#
#     worker = QThreadWaiting(5, my_print, "ok thread")
#     worker.start()
#     print(worker.currentThreadId())
#
#     print("before join")
#     i = 0
#     while i < 10:
#         print(i)
#         time.sleep(1)
#         i += 1
#     worker.wait()
#     print("after join")
#     i = 0
#     while i < 10:
#         print(i)
#         time.sleep(1)
#         i += 1

class MyTest():
    def __init__(self):
        self.__my_list = []

    @property
    def my_list(self):
        return self.__my_list


class MyPlotWidget(QWidget):
    def __init__(self):
        super(MyPlotWidget, self).__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fig = plt.Figure(figsize=(10, 7))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.graph = self.fig.add_subplot(111)
        self.graph.set_xlim(0, 50)
        self.graph.set_ylim(0, 50)
        self.xdata = [0]
        self.ydata = [random.randint(0, 50)]
        self.curve, = self.graph.plot(self.xdata, self.ydata, "-*b")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(2000)

        self.button = QPushButton("Stop")
        self.button.clicked.connect(self.timer.stop)
        layout.addWidget(self.button)

    def update_graph(self):
        self.xdata.append(self.xdata[-1] + 1)
        self.ydata.append(random.randint(0, 50))
        self.curve.set_data(self.xdata, self.ydata)
        self.canvas.draw()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    # wslider = QCustomSlider(QtCore.Qt.Horizontal)
    # wslider.setTickLabels(range(0, 101, 5))
    # wslider.setRange(0, 101)
    # wslider.setTickInterval(5)
    # wslider.setTickPosition(QSlider.TicksBothSides)
    # wslider.show()
    myplot = MyPlotWidget()
    myplot.show()
    sys.exit(app.exec_())