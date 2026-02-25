from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,

)

from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCharts import QChart, QValueAxis, QChartView, QLineSeries
from PySide6.QtCore import Qt, QPointF

from view.interactive_chart_view import InteractiveChartView

import numpy as np
import csv

class HeartBeatLoadWaveformFromFilePage(QWidget):
    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self._viewmodel = viewmodel
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ── Chart ──────────────────────────────────────────────────────────
        self.chart = QChart()
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.legend().setVisible(True)

        # X Axis
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

        # Y Axis
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Pressure (mmHg)")
        self.axis_y.setLabelFormat("%.1f")
        self.axis_y.setGridLineVisible(True)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        # Series — empty until a file is loaded
        self.series = QLineSeries()
        self.series.setName("Loaded Waveform")
        self.chart.addSeries(self.series)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)

        #self.chart_view = QChartView(self.chart)  # plain view, no drag needed
        #self.chart_view.setRenderHint(QPainter.Antialiasing)
        #main_layout.addWidget(self.chart_view)

        # ── InteractiveChartView: pan/zoom/reset built-in ──────────────────
        # No callbacks needed — this page has no draggable reference points
        self.chart_view = InteractiveChartView(self.chart)
        main_layout.addWidget(self.chart_view)

        # --- Load Waveform button ---
        self._load_waveform_button = QPushButton("Load Waveform")
        self._load_waveform_button.setEnabled(True)
        self._load_waveform_button.clicked.connect(self._on_load_waveform_button_clicked)
        main_layout.addWidget(self._load_waveform_button)

        main_layout.addStretch()


    def _on_load_waveform_button_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Waveform File",
            "",  # start dir: last used / home
            "Data Files (*.csv *.txt);;All Files (*)"
        )

        if not path:
            return  # user cancelled — do nothing

        try:
            self._load_waveform_from_file(path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load waveform:\n\n{e}"
            )

    def _populate_chart(self, time_points: np.ndarray, pressure_points: np.ndarray):
        """Clear the series and repaint with new data."""
        self.series.clear()

        # Build the point list in one vectorised pass — no Python loop
        points = [
            QPointF(t, p)
            for t, p in zip(time_points.tolist(), pressure_points.tolist())
        ]

        self.series.replace(points)  # single C++ call, replaces all points at once

        # Rescale axes to fit the loaded data
        self.axis_x.setRange(float(np.min(time_points)), float(np.max(time_points)))
        self.axis_x.setTickAnchor(0.0)
        self.axis_x.setTickInterval(100)
        self.axis_y.setRange(
            float(np.min(pressure_points)) - 5,
            float(np.max(pressure_points)) + 5
        )

    def _load_waveform_from_file(self, path: str):
        """
        Parse a single-column CSV/TXT file: one pressure value (mmHg) per line.
        Lines starting with '#' are treated as comments and skipped.
        Sample index is auto-generated (0, 1, 2, ...).
        """
        pressure_points = []

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for line_num, row in enumerate(reader, start=1):
                if not row or row[0].strip().startswith("#"):
                    continue
                try:
                    p = float(row[0].strip())
                except ValueError:
                    raise ValueError(
                        f"Line {line_num}: cannot parse pressure value → {row[0]!r}"
                    )
                pressure_points.append(p)

        if not pressure_points:
            raise ValueError("File contains no valid data rows.")

        time_points = np.arange(len(pressure_points), dtype=float)  # 0, 1, 2, ...

        self._populate_chart(time_points, np.array(pressure_points))

