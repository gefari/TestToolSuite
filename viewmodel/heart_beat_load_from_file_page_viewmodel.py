from PySide6.QtCore import QObject, Signal, Property
class HeartBeatLoadWaveformFromFilePageViewModel(QObject):
    def __init__(self, model):
        super().__init__()
        self._heart_beat_from_file_model = model


    def new_file_loaded(self):
        raise NotImplementedError("New file loaded not supported.")