from PySide6.QtCore import QObject, Signal, Property
import csv

class HeartBeatLoadWaveformFromFilePageViewModel(QObject):
    waveform_loaded = Signal(list, list)
    load_error = Signal(str)

    def __init__(self, model):
        super().__init__()
        self._heart_beat_from_file_model = model
        # ViewModel listens to model (the model emits waveform_changed)
        self._heart_beat_from_file_model.waveform_changed.connect(self._on_waveform_changed)

    ''' Public called by "view" when a new abp waveform is selected. '''
    def new_file_loaded(self, path: str):
        try:
            pressure_points = self._parse_csv(path)  # returns a plain list
            ''' 
            1. set_waveform() in the model is the single entry point for writing data 
            2. fills the model arrays
            3. triggers waveform_changed
            '''
            self._heart_beat_from_file_model.set_waveform(pressure_points)

        except Exception as e:
            self.load_error.emit(str(e))

    ''' 
    Triggered by Signal emitted from model layer.
    Forward message and argument to view layer 
    '''
    def _on_waveform_changed(self):
        self.waveform_loaded.emit(
            self._heart_beat_from_file_model.time_points,
            self._heart_beat_from_file_model.pressure_points)

    @staticmethod
    def _parse_csv(path: str) -> list:
        pressure_points = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for line_num, row in enumerate(reader, start=1):
                if not row or row[0].strip().startswith("#"):
                    continue
                try:
                    pressure_points.append(float(row[0].strip()))
                except ValueError:
                    raise ValueError(
                        f"Line {line_num}: cannot parse pressure value → {row[0]!r}"
                    )
        if not pressure_points:
            raise ValueError("File contains no valid data rows.")
        return pressure_points

