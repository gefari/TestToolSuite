from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox, QCheckBox
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen

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
        min_sample_rate_label = QLabel("Sample Rate (sps):")
        min_sample_rate_layout.addWidget(min_sample_rate_label)

        self._min_sample_rate_spinbox = QSpinBox()
        self._min_sample_rate_spinbox.setRange(1000, 50000)  # clinically safe range
        self._min_sample_rate_spinbox.setValue(1000)  # default 1000 SPS
        self._min_sample_rate_spinbox.setEnabled(True)
        self._min_sample_rate_spinbox.valueChanged.connect(self._on_sample_rate_changed)
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

        # --- Chart setup (replaces the final addStretch) ---
        self._chart = QChart()
        self._chart.setTitle("AO Waveforms")
        self._chart.legend().setVisible(True)

        self._series_ao0 = QLineSeries()
        self._series_ao0.setName("AO0 – ABP Waveform")
        pen0 = QPen(QColor("#1E90FF"))
        pen0.setWidth(2)
        self._series_ao0.setPen(pen0)

        self._series_ao1 = QLineSeries()
        self._series_ao1.setName("AO1 – Reference")
        pen1 = QPen(QColor("#FF8C00"))
        pen1.setWidth(2)
        self._series_ao1.setPen(pen1)

        self._chart.addSeries(self._series_ao0)
        self._chart.addSeries(self._series_ao1)

        axis_x = QValueAxis()
        axis_x.setTitleText("Sample Index")
        axis_x.setLabelFormat("%d")

        axis_y = QValueAxis()
        axis_y.setTitleText("Voltage (V)")
        axis_y.setRange(-10.0, 10.0)

        self._chart.addAxis(axis_x, Qt.AlignBottom)
        self._chart.addAxis(axis_y, Qt.AlignLeft)
        self._series_ao0.attachAxis(axis_x)
        self._series_ao0.attachAxis(axis_y)
        self._series_ao1.attachAxis(axis_x)
        self._series_ao1.attachAxis(axis_y)

        chart_view = QChartView(self._chart)
        chart_view.setMinimumHeight(250)

        main_layout.addWidget(chart_view)

        # --- Y-axis range controls ---
        y_range_layout = QHBoxLayout()

        y_range_layout.addWidget(QLabel("Y Min (V):"))
        self._ymin_spinbox = QDoubleSpinBox()
        self._ymin_spinbox.setRange(-100.0, 100.0)
        self._ymin_spinbox.setValue(-10.0)
        self._ymin_spinbox.setSingleStep(0.5)
        self._ymin_spinbox.setSuffix(" V")
        self._ymin_spinbox.valueChanged.connect(self._on_y_range_changed)
        y_range_layout.addWidget(self._ymin_spinbox)

        y_range_layout.addWidget(QLabel("Y Max (V):"))
        self._ymax_spinbox = QDoubleSpinBox()
        self._ymax_spinbox.setRange(-100.0, 100.0)
        self._ymax_spinbox.setValue(10.0)
        self._ymax_spinbox.setSingleStep(0.5)
        self._ymax_spinbox.setSuffix(" V")
        self._ymax_spinbox.valueChanged.connect(self._on_y_range_changed)
        y_range_layout.addWidget(self._ymax_spinbox)

        y_range_layout.addStretch()
        main_layout.addLayout(y_range_layout)

        # --- Series visibility controls ---
        series_layout = QHBoxLayout()

        self._ao0_checkbox = QCheckBox("AO0 – ABP Waveform")
        self._ao0_checkbox.setChecked(True)
        self._ao0_checkbox.toggled.connect(self._on_ao0_visibility_changed)
        series_layout.addWidget(self._ao0_checkbox)

        self._ao1_checkbox = QCheckBox("AO1 – Reference")
        self._ao1_checkbox.setChecked(True)
        self._ao1_checkbox.toggled.connect(self._on_ao1_visibility_changed)
        series_layout.addWidget(self._ao1_checkbox)

        series_layout.addStretch()
        main_layout.addLayout(series_layout)

        self.setLayout(main_layout)

        # Populate immediately from ViewModel initial state
        ao0_init, ao1_init = self._viewmodel.get_waveforms()
        if ao0_init is not None:
            self._populate_chart(ao0_init, ao1_init)

        # Connect ViewModel signals
        self._viewmodel.connection_changed.connect(self._on_connection_changed)
        self._viewmodel.generation_state_changed.connect(self._on_generation_state_changed)
        self._viewmodel.waveform_changed.connect(self._on_waveform_changed)

        # Set initial state
        self._on_connection_changed(self._viewmodel.is_connected)
        self._viewmodel.set_sample_rate(self._min_sample_rate_spinbox.value())

    def _on_start_stop_toggled(self, checked: bool):
        if checked:
            self._viewmodel.start_generation()
        else:
            self._viewmodel.stop_generation()

    def _on_set_static_pressure_button_clicked(self):
        self._viewmodel.set_static_pressure(self._static_pressure_spinbox.value())

    ''' When DAQ Sample Rate change from UI '''
    def _on_sample_rate_changed(self):
        self._viewmodel.set_sample_rate(self._min_sample_rate_spinbox.value())

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
                    self._gen_button.setChecked(False)

            self._gen_button.setEnabled(connected)
            self._static_pressure_button.setEnabled(connected)
            self._static_pressure_spinbox.setEnabled(connected)
            #self._min_sample_rate_spinbox.setEnabled(connected)

        finally:
            self._gen_button.blockSignals(False)
    def _on_generation_state_changed(self, running: bool):
        self._gen_button.blockSignals(True)
        try:
            self._gen_button.setChecked(running)
            self._gen_button.setText("Stop Generation" if running else "Start Generation")
            self._static_pressure_button.setEnabled(not running and self._viewmodel.is_connected)
            self._static_pressure_spinbox.setEnabled(not running and self._viewmodel.is_connected)
            #self._min_sample_rate_spinbox.setEnabled(not running and self._viewmodel.is_connected)
        finally:
            self._gen_button.blockSignals(False)

    def _populate_chart(self, ao0, ao1):
        step = max(1, len(ao0) // 1000)  # downsample to ≤1000 pts for performance
        self._series_ao0.replace([
            QPointF(i, float(v)) for i, v in enumerate(ao0[::step])
        ])
        self._series_ao1.replace([
            QPointF(i, float(v)) for i, v in enumerate(ao1[::step])
        ])
        self._chart.axes(Qt.Horizontal)[0].setRange(0, len(ao0[::step]) - 1)

    def _on_waveform_changed(self, ao0, ao1):
        self._populate_chart(ao0, ao1)

    def _on_y_range_changed(self):
        y_min = self._ymin_spinbox.value()
        y_max = self._ymax_spinbox.value()
        if y_min >= y_max:
            return  # guard: ignore invalid range
        self._chart.axes(Qt.Vertical)[0].setRange(y_min, y_max)

    def _on_ao0_visibility_changed(self, visible: bool):
        self._series_ao0.setVisible(visible)

    def _on_ao1_visibility_changed(self, visible: bool):
        self._series_ao1.setVisible(visible)