from PySide6.QtCore import QObject, Signal
import numpy as np

class AbpWaveformFileModel(QObject):
    waveform_changed = Signal()

    def __init__(self):
        super().__init__()
        self._abp_waveform_time_points = []
        self._abp_waveform_pressure_points = []

    @property
    def time_points(self) -> list:
        return self._abp_waveform_time_points

    @property
    def pressure_points(self) -> list:
        return self._abp_waveform_pressure_points

    '''
    The key point is that set_waveform() in the model 
    is the single entry point for writing data — 
    it always keeps _abp_waveform_time_points and _abp_waveform_pressure_points in sync 
    and emits waveform_changed so any other subscriber 
    (e.g. a future status bar or export button) 
    can react automatically.
    '''
    def set_waveform(self, pressure_points: list):
        self._abp_waveform_pressure_points = pressure_points
        self._abp_waveform_time_points = list(range(len(pressure_points)))  # 0, 1, 2, ...
        self.waveform_changed.emit()

    def clear(self):
        self._abp_waveform_pressure_points = []
        self._abp_waveform_time_points = []
        self.waveform_changed.emit()
