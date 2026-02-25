from PySide6.QtWidgets import QWidget, QHBoxLayout
from view.heart_beat_waveform_page_view import HeartBeatWaveformPage
import viewmodel
import model
from model.ni6216daqmx_model import Ni6216DaqMx

class HeartBeatView(QWidget):

    def __init__(self, viewmodel):
        super().__init__()
        self._viewmodel = viewmodel
        self._init_ui()  # ← UI built first

    # ── UI Setup ──────────────────────────────────────────────────────────
    def _init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Page 0 — Waveform chart + table
        self._heart_beat_waveform_page = HeartBeatWaveformPage(self._viewmodel)

        root_layout.addWidget(self._heart_beat_waveform_page, stretch=1)

    def _initialize_view(self):
        heart_beat_viewmodel = viewmodel.HeartBeatWaveformPageViewModel(self.heart_beat_model)

