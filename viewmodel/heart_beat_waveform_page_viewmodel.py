from PySide6.QtCore import QObject, Signal, Property

# This class represents the bridge between the model and the view for the HeartBeat Functionalities
class HeartBeatWaveformPageViewModel(QObject):
    waveform_data_changed = Signal()
    reference_waveform_data_changed = Signal()

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._model.waveform_data_changed.connect(self.waveform_data_changed)
        self._model.waveform_data_changed.connect(self.reference_waveform_data_changed)

    @Property(object, notify=waveform_data_changed)
    def abp_waveform(self):
        return self._model.get_waveform_points()

    @abp_waveform.setter
    def abp_waveform(self, value):
        raise NotImplementedError("Direct waveform assignment is not yet supported.") 

    @Property(object, notify=reference_waveform_data_changed)
    def reference_abp_waveform(self):
        return self._model.get_waveform_reference_points()
    
    def update_reference_point(self, key: str, new_time_pct: float, new_pressure: float):
        new_time_pct = max(0.0, min(1.0, new_time_pct))
        new_pressure = max(0.0, new_pressure)   # pressure cannot be negative
        self._model.update_reference_point(key, new_time_pct, new_pressure)
    
    @Property(list, notify=waveform_data_changed)
    def reference_point_keys(self):
        return self._model.get_reference_point_keys()

    def load_default_settings(self):
        self._model.load_default_settings()

