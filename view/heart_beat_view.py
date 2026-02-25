from PySide6.QtWidgets import QWidget, QHBoxLayout
from view.heart_beat_waveform_page_view import HeartBeatWaveformPage
import viewmodel
from view.inner_panel import InnerPanel
from view.heart_beat_load_from_file_page_view import HeartBeatLoadWaveformFromFilePage


class HeartBeatView(QWidget):

    def __init__(self, waveform_page_viewmodel, load_from_file_page_viewmodel):
        super().__init__()
        self._heart_beat_waveform_page_viewmodel = waveform_page_viewmodel
        self._heart_beat_load_from_file_page_viewmodel = load_from_file_page_viewmodel
        self._init_ui()  # ← UI built first

    # ── UI Setup ──────────────────────────────────────────────────────────
    def _init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._inner_panel = InnerPanel()
        # Page 1 — Waveform chart + table
        self._heart_beat_waveform_page = HeartBeatWaveformPage(self._heart_beat_waveform_page_viewmodel)
        self._inner_panel.add_page(
            "fa5s.heartbeat",
            "Waveform",
            self._heart_beat_waveform_page
        )
        # Page 2 — Load Waveform from file
        self._heart_beat_load_from_file_page = HeartBeatLoadWaveformFromFilePage(
            self._heart_beat_load_from_file_page_viewmodel)
        self._inner_panel.add_page(
            "fa5s.file",
            "Load from file",
            self._heart_beat_load_from_file_page
        )
        # Page 3 — Fixed Values
        self._inner_panel.add_page(
            "fa5s.flag",
            "Calibration Values",
            QWidget()
        )


        root_layout.addWidget(self._inner_panel, stretch=1)

    def _initialize_view(self):
        heart_beat_viewmodel = viewmodel.HeartBeatWaveformPageViewModel(self.heart_beat_model)

