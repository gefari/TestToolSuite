from PySide6.QtCore import QObject, Signal
from model.ni6216daqmx_model import Ni6216DaqMx

class NI6216ViewModel(QObject):

    connection_changed = Signal(bool)
    generation_state_changed = Signal(bool)
    status_message = Signal(str)
    waveform_changed = Signal(object, object)  # (ao0: np.ndarray, ao1: np.ndarray)
    sample_rate_changed = Signal(int)

    def __init__(self,
                 daq_model: Ni6216DaqMx,
                 parent=None):
        super().__init__(parent)

        self._daq_model = daq_model

        self._daq_model.connection_changed.connect(self.connection_changed)
        self._daq_model.generation_state_changed.connect(self.generation_state_changed)
        self._daq_model.status_message.connect(self.status_message)
        self._daq_model.waveform_changed.connect(self.waveform_changed)

        self._sample_rate_sps = 1000

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

    def set_static_pressure(self, pressure_mmhg: float):
        self._daq_model.set_static_pressure(pressure_mmhg)

    def set_sample_rate(self, value: int) -> None:
        if value == self._daq_model.get_sample_rate():
            return
        self._daq_model.set_sample_rate(value)

        self._sample_rate_sps = value
        self.sample_rate_changed.emit(value)

    def get_waveforms(self):
        return self._daq_model.get_waveforms()