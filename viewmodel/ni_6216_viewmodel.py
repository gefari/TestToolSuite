from PySide6.QtCore import QObject, Signal
from model.ni6216daqmx_model import Ni6216DaqMx

class NI6216ViewModel(QObject):
    connection_changed = Signal(bool)
    generation_state_changed = Signal(bool)
    status_message = Signal(str)

    def __init__(self, usb_searcher: Ni6216DaqMx, parent=None):
        super().__init__(parent)
        self._usb_searcher = usb_searcher

        self._usb_searcher.connection_changed.connect(self.connection_changed)
        self._usb_searcher.generation_state_changed.connect(self.generation_state_changed)
        self._usb_searcher.status_message.connect(self.status_message)

    @property
    def is_connected(self) -> bool:
        return self._usb_searcher.is_connected

    @property
    def is_generating(self) -> bool:
        return self._usb_searcher.is_generating

    def start_generation(self):
        self._usb_searcher.start_generation()   # pure delegation

    def stop_generation(self):
        self._usb_searcher.stop_generation()    # pure delegation

