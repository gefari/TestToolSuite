from PySide6.QtCore import QObject, Signal
from model.ni6216daqmx_model import Ni6216DaqMx

class NI6216ViewModel(QObject):
    connection_changed = Signal(bool)
    generation_state_changed = Signal(bool)
    status_message = Signal(str)

    def __init__(self, daq_model: Ni6216DaqMx, parent=None):
        super().__init__(parent)
        self._daq_model = daq_model

        self._daq_model.connection_changed.connect(self.connection_changed)
        self._daq_model.generation_state_changed.connect(self.generation_state_changed)
        self._daq_model.status_message.connect(self.status_message)

    @property
    def is_connected(self) -> bool:
        return self._daq_model.is_connected

    @property
    def is_generating(self) -> bool:
        return self._daq_model.is_generating

    def start_generation(self):
        self._daq_model.start_generation()   # pure delegation

    def stop_generation(self):
        self._daq_model.stop_generation()    # pure delegation

