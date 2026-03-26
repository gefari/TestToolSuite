from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox,
    QDoubleSpinBox, QLabel
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCharts import QChart, QValueAxis, QLineSeries
from PySide6.QtCore import Qt, QPointF
from view.interactive_chart_view import InteractiveChartView
import numpy as np

class HeartBeatLoadWaveformFromFilePage(QWidget):
    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._viewmodel.waveform_loaded.connect(self._on_waveform_loaded)
        self._viewmodel.load_error.connect(self._on_load_error)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ── Chart ──────────────────────────────────────────────────────────
        self.chart = QChart()
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.legend().setVisible(True)

        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Samples")
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTickType(QValueAxis.TicksDynamic)
        self.axis_x.setTickInterval(100)
        self.axis_x.setTickAnchor(0.0)
        self.axis_x.setGridLineVisible(True)
        dash_pen = QPen(QColor("#555555"))
        dash_pen.setStyle(Qt.DashLine)
        dash_pen.setWidth(1)
        self.axis_x.setGridLinePen(dash_pen)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Pressure (mmHg)")
        self.axis_y.setLabelFormat("%.1f")
        self.axis_y.setGridLineVisible(True)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        self.series = QLineSeries()
        self.series.setName("Loaded Waveform")
        self.chart.addSeries(self.series)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        self.chart_view = InteractiveChartView(self.chart)
        main_layout.addWidget(self.chart_view)

        # ── Controls row ───────────────────────────────────────────────────
        controls_layout = QHBoxLayout()

        self._load_waveform_button = QPushButton("Load Waveform")
        self._load_waveform_button.clicked.connect(self._on_load_waveform_button_clicked)
        controls_layout.addWidget(self._load_waveform_button)

        controls_layout.addStretch()

        # ── Scale spin box ─────────────────────────────────────────────────
        controls_layout.addWidget(QLabel("Scale (mmHg):"))
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.01, 100.0)
        self._scale_spin.setSingleStep(0.1)
        self._scale_spin.setDecimals(3)
        self._scale_spin.setValue(0.1)
        self._scale_spin.setFixedWidth(90)
        self._scale_spin.valueChanged.connect(self._viewmodel.set_scale)
        self._scale_spin.editingFinished.connect(
            lambda: self._viewmodel.set_scale(self._scale_spin.value())
        )
        self._viewmodel.set_scale(self._scale_spin.value())
        controls_layout.addWidget(self._scale_spin)

        main_layout.addLayout(controls_layout)
        main_layout.addStretch()

    def _on_waveform_loaded(self, time, pressure, filename: str):
        self._populate_chart(time, pressure, filename)

    @staticmethod
    def _on_load_error(msg):
        print(msg)

    def _on_load_waveform_button_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Waveform File", "",
            "Data Files (*.csv *.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            self._viewmodel.new_file_loaded(path)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load waveform:\n\n{e}")

    def _populate_chart(self,
                        time_points: np.ndarray,
                        pressure_points: np.ndarray,
                        filename: str = "Loaded Waveform"):
        self.series.clear()
        self.series.setName(filename)

        points = [QPointF(t, p) for t, p in zip(time_points, pressure_points)]
        self.series.replace(points)

        self.axis_x.setRange(float(np.min(time_points)), float(np.max(time_points)))
        self.axis_x.setTickAnchor(0.0)
        self.axis_x.setTickInterval(100)
        self.axis_y.setRange(
            float(np.min(pressure_points)) - 5,
            float(np.max(pressure_points)) + 5
        )
