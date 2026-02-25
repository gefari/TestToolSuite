from PySide6.QtCore import QObject, Signal
class AbpWaveformFileModel(QObject):
    def __init__(self):
        super().__init__()

        self._abp_waveform_time_points = []
        self._abp_waveform_pressure_points = []