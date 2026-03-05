from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QSpinBox
from viewmodel.ni_6216_viewmodel import NI6216ViewModel

import qtawesome as qta

class NI6216View(QWidget):

    def __init__(self, viewmodel: NI6216ViewModel, parent=None):
        super().__init__(parent)
        self._viewmodel = viewmodel

        main_layout = QVBoxLayout()

        # --- Connection status row ---
        status_layout = QHBoxLayout()
        self._status_icon = QLabel()
        self._status_label = QLabel("Disconnected")
        status_layout.addWidget(self._status_icon)
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)

        # Spins box to change DaqMx Sample rate
        min_sample_rate_layout = QHBoxLayout()
        min_sample_rate_label = QLabel("Minimum Sample Rate:")
        min_sample_rate_layout.addWidget(min_sample_rate_label)

        self._min_sample_rate_spinbox = QSpinBox()
        self._min_sample_rate_spinbox.setRange(1000, 50000)  # clinically safe range
        self._min_sample_rate_spinbox.setValue(10000)  # default 1000 SPS
        self._min_sample_rate_spinbox.setEnabled(False)
        self._min_sample_rate_spinbox.valueChanged.connect(self._on_min_sample_rate_changed)
        min_sample_rate_layout.addWidget(self._min_sample_rate_spinbox)
        min_sample_rate_layout.addStretch()
        main_layout.addLayout(min_sample_rate_layout)

        # --- Start/Stop button ---
        self._gen_button = QPushButton("Start Generation")
        self._gen_button.setCheckable(True)
        self._gen_button.setEnabled(False)  # disabled until device is connected
        self._gen_button.toggled.connect(self._on_start_stop_toggled)
        main_layout.addWidget(self._gen_button)

        # --- Static pressure row ---
        zero_layout = QHBoxLayout()
        # --- ZERO button ---
        self._static_pressure_button = QPushButton("Set Pressure")
        self._static_pressure_button.setEnabled(False)  # disabled until device is connected
        self._static_pressure_button.clicked.connect(self._on_set_static_pressure_button_clicked)

        zero_layout.addWidget(self._static_pressure_button)

        self._static_pressure_spinbox = QSpinBox()
        self._static_pressure_spinbox.setRange(0, 300)
        self._static_pressure_spinbox.setValue(0)
        self._static_pressure_spinbox.setSuffix(" mmHg")
        self._static_pressure_spinbox.setEnabled(False)  # disabled until device is connected

        zero_layout.addWidget(self._static_pressure_spinbox)

        main_layout.addLayout(zero_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

        # Connect ViewModel signals
        self._viewmodel.connection_changed.connect(self._on_connection_changed)
        self._viewmodel.generation_state_changed.connect(self._on_generation_state_changed)
        # Set initial state
        self._on_connection_changed(self._viewmodel.is_connected)

    def _on_start_stop_toggled(self, checked: bool):
        if checked:
            self._viewmodel.start_generation()
        else:
            self._viewmodel.stop_generation()

    def _on_set_static_pressure_button_clicked(self):
        self._viewmodel.set_static_pressure(self._static_pressure_spinbox.value())

    def _on_min_sample_rate_changed(self):
        self._viewmodel.set_min_sample_rate(self._min_sample_rate_spinbox.value())

    def _on_connection_changed(self, connected: bool):
        self._gen_button.blockSignals(True)  # prevent re-triggering toggled
        try:
            if connected:
                self._status_icon.setPixmap(
                    qta.icon("fa5s.circle", color="green").pixmap(16, 16)
                )
                self._status_label.setText("NI-6216 Connected")
            else:
                self._status_icon.setPixmap(
                    qta.icon("fa5s.circle", color="red").pixmap(16, 16)
                )
                self._status_label.setText("NI-6216 Disconnected")

                # Stop generation and reset button if device is unplugged mid-run
                if self._gen_button.isChecked():
                    #self._gen_button.blockSignals(True)  # prevent re-triggering toggled
                    self._gen_button.setChecked(False)
                    #self._gen_button.blockSignals(False)

            self._gen_button.setEnabled(connected)
            self._static_pressure_button.setEnabled(connected)
            self._static_pressure_spinbox.setEnabled(connected)
            self._min_sample_rate_spinbox.setEnabled(connected)

        finally:
            self._gen_button.blockSignals(False)
    def _on_generation_state_changed(self, running: bool):
        self._gen_button.blockSignals(True)
        try:
            self._gen_button.setChecked(running)
            self._gen_button.setText("Stop Generation" if running else "Start Generation")
            self._static_pressure_button.setEnabled(not running and self._viewmodel.is_connected)
            self._static_pressure_spinbox.setEnabled(not running and self._viewmodel.is_connected)
            self._min_sample_rate_spinbox.setEnabled(not running and self._viewmodel.is_connected)
        finally:
            self._gen_button.blockSignals(False)

