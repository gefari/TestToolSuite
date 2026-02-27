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

        # --- Start/Stop button ---
        self._gen_button = QPushButton("Start Generation")
        self._gen_button.setCheckable(True)
        self._gen_button.setEnabled(False)  # disabled until device is disconnected
        self._gen_button.toggled.connect(self._on_start_stop_toggled)
        main_layout.addWidget(self._gen_button)

        # --- Zero / Fixed pressure row ---
        zero_layout = QHBoxLayout()
        # --- ZERO button ---
        self._static_pressure_button = QPushButton("Set Pressure")
        self._static_pressure_button.setEnabled(False)  # disabled until device is disconnected
        self._static_pressure_button.clicked.connect(self._on_zero_button_clicked)

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

    def _on_zero_button_clicked(self):
        self._viewmodel.set_static_pressure(self._static_pressure_spinbox.value())

    def _on_connection_changed(self, connected: bool):
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
                self._gen_button.blockSignals(True)  # prevent re-triggering toggled
                self._gen_button.setChecked(False)
                #self._static_pressure_button.setChecked(False)
                self._gen_button.blockSignals(False)

        self._gen_button.setEnabled(connected)
        self._static_pressure_button.setEnabled(connected)
        self._static_pressure_spinbox.setEnabled(connected)

    def _on_generation_state_changed(self, running: bool):
        # Keep button label in sync if state is changed externally
        self._gen_button.blockSignals(True)
        self._gen_button.setChecked(running)
        self._gen_button.setText("Stop Generation" if running else "Start Generation")
        #self._static_pressure_button.setChecked(running)

        self._static_pressure_button.setEnabled(not running and self._viewmodel.is_connected)
        self._static_pressure_spinbox.setEnabled(not running and self._viewmodel.is_connected)

        self._gen_button.blockSignals(False)



    

