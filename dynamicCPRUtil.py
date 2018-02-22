
import sys
import threading
from PyQt4.QtCore import QThread
from PyQt4.QtGui import QApplication
import time


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print(threading.currentThread())

    def my_print(what):
        print(what)

    worker = QThreadWaiting(5, my_print, "ok thread")
    worker.start()
    print(worker.currentThreadId())

    print("before join")
    i = 0
    while i < 10:
        print(i)
        time.sleep(1)
        i += 1
    worker.wait()
    print("after join")
    i = 0
    while i < 10:
        print(i)
        time.sleep(1)
        i += 1
