import traceback

from PyQt6 import QtCore


class Signals(QtCore.QObject):
    error = QtCore.pyqtSignal(Exception, str)
    finish = QtCore.pyqtSignal(object)


class Runnable(QtCore.QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

        self._sigs = Signals()
        self.finished = self._sigs.finish
        self.errored = self._sigs.error

    @QtCore.pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        result = None
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as e:
            self.errored.emit(e, traceback.format_exc())
        finally:
            self.finished.emit(result)
