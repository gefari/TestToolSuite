from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QLabel, QSpinBox
)
from PySide6.QtCharts import QChart, QLineSeries, QValueAxis, QScatterSeries
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF

from view.interactive_chart_view import InteractiveChartView
import numpy as np


class HeartBeatWaveformPage(QWidget):
    """
    The chart + reference table page.
    Extracted from HeartBeatView so it lives as one page
    inside HeartBeatView's InnerLeftPanel stack.
    """

    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self._heartbeat_viewmodel = viewmodel
        self._init_ui()

        self._heartbeat_viewmodel.waveform_data_changed.connect(self.update_waveform_data)
        self._heartbeat_viewmodel.sample_rate_changed.connect(self._on_sample_rate_changed)

        self.update_waveform_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # --- BPM row ---
        bpm_layout = QHBoxLayout()
        bpm_label = QLabel("Heart Rate:")
        bpm_layout.addWidget(bpm_label)

        self._bpm_spinbox = QSpinBox()
        self._bpm_spinbox.setRange(30, 240)  # clinically safe range
        self._bpm_spinbox.setValue(60)  # default 60 BPM
        self._bpm_spinbox.setSuffix(" BPM")
        self._bpm_spinbox.setEnabled(True)
        self._bpm_spinbox.valueChanged.connect(self._on_bpm_changed)
        bpm_layout.addWidget(self._bpm_spinbox)
        bpm_layout.addStretch()
        main_layout.addLayout(bpm_layout)

        # ── Chart ──────────────────────────────────────────────────────────
        self.chart = QChart()
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.legend().setVisible(True)

        self.series = QLineSeries()
        self.series.setName("ABP Waveform")
        self.chart.addSeries(self.series)

        self.ref_points_series = QScatterSeries()
        self.ref_points_series.setName("Reference Points")
        self.ref_points_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        self.ref_points_series.setMarkerSize(10.0)
        self.ref_points_series.setColor(QColor("#FFD93D"))
        self.chart.addSeries(self.ref_points_series)

        # X Axis Bottom
        self.axis_x_sample = QValueAxis()
        self.axis_x_sample.setTitleText("Samples")
        self.axis_x_sample.setLabelFormat("%d")
        self.axis_x_sample.setTickType(QValueAxis.TicksDynamic)
        self.axis_x_sample.setTickInterval(50)
        self.axis_x_sample.setTickAnchor(0.0)
        self.axis_x_sample.setGridLineVisible(True)
        dash_pen = QPen(QColor("#555555"))
        dash_pen.setStyle(Qt.DashLine)
        dash_pen.setWidth(1)
        self.axis_x_sample.setGridLinePen(dash_pen)

        # X Axis Top (time in seconds)
        self.axis_x_time = QValueAxis()
        self.axis_x_time.setTitleText("Time (s)")
        self.axis_x_time.setLabelFormat("%.2f")
        self.axis_x_time.setTickType(QValueAxis.TicksDynamic)
        self.axis_x_time.setTickInterval(0.05)  # updated dynamically
        self.axis_x_time.setTickAnchor(0.0)
        self.axis_x_time.setGridLineVisible(False)  # avoid double grid
        dash_pen_top = QPen(QColor("#555555"))
        dash_pen_top.setStyle(Qt.DashLine)
        dash_pen_top.setWidth(1)
        self.axis_x_time.setGridLinePen(dash_pen_top)

        # Y Axis
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Pressure (mmHg)")
        self.axis_y.setLabelFormat("%.1f")
        self.axis_y.setGridLineVisible(True)

        # Add x-axis, y-axis yo chart
        self.chart.addAxis(self.axis_x_sample, Qt.AlignBottom)
        self.chart.addAxis(self.axis_x_time, Qt.AlignTop) # labels only
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        for s in [self.series, self.ref_points_series]:
            s.attachAxis(self.axis_x_sample)
            #s.attachAxis(self.axis_x_time)
            s.attachAxis(self.axis_y)

        self.chart_view = InteractiveChartView(
            self.chart,
            on_point_moved_callback=self._on_reference_point_moved,
            on_point_clicked_callback=self._on_reference_point_clicked
        )
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self.chart_view)

        # ── Controls bar ───────────────────────────────────────────────────
        controls_layout = QHBoxLayout()
        self.btn_load_defaults = QPushButton("↺  Load Defaults")
        self.btn_load_defaults.setToolTip("Reload reference points from the XML settings file")
        self.btn_load_defaults.setFixedHeight(32)
        self.btn_load_defaults.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a; color: #00FF00;
                border: 1px solid #00CC00; border-radius: 4px;
                padding: 4px 12px; font-size: 12px;
            }
            QPushButton:hover {
                background-color: #003300;
                border-color: #FFD93D; color: #FFD93D;
            }
            QPushButton:pressed { background-color: #004400; }
        """)
        self.btn_load_defaults.clicked.connect(self._on_load_defaults_clicked)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_load_defaults)

        # ── Reference table ────────────────────────────────────────────────
        self.ref_table = QTableWidget()
        self.ref_table.setRowCount(2)
        self.ref_table.setColumnCount(0)
        self.ref_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ref_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ref_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked |
            QAbstractItemView.EditTrigger.SelectedClicked
        )
        self.ref_table.setSelectionMode(QTableWidget.SingleSelection)
        self.ref_table.setSelectionBehavior(QTableWidget.SelectColumns)
        self.ref_table.setMaximumHeight(100)
        self.ref_table.setAlternatingRowColors(True)
        self.ref_table.setStyleSheet("""
            QTableWidget { background-color:#000; color:#00FF00;
                           gridline-color:#1a1a1a; font-size:12px; }
            QTableWidget::item { background-color:#000; color:#00FF00; padding:4px; }
            QTableWidget::item:alternate { background-color:#0a0a0a; }
            QTableWidget::item:selected { background-color:#004400;
                           color:#00FF00; border:1px solid #FFD93D; }
            QHeaderView::section { background-color:#111; color:#00CC00;
                           font-weight:bold; padding:4px; border:1px solid #1a1a1a; }
            QHeaderView::section:checked { background-color:#003300; color:#FFD93D; }
            QTableCornerButton::section { background-color:#111; border:1px solid #1a1a1a; }
        """)
        self.ref_table.cellChanged.connect(self._on_table_cell_changed)

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.ref_table)

    # ── All waveform/table methods (unchanged from HeartBeatView) ──────────

    def update_waveform_data(self):
        self.series.clear()
        self.ref_points_series.clear()
        waveform        = self._heartbeat_viewmodel.abp_waveform
        time_points     = waveform['abp_waveform_time_points']
        pressure_points = waveform['abp_waveform_pressure_points']
        if len(time_points) == 0:
            return
        for t, p in zip(time_points, pressure_points):
            self.series.append(float(t), float(p))
        ref           = self._heartbeat_viewmodel.reference_abp_waveform
        ref_times     = ref['abp_ref_waveform_time_points']
        ref_pressures = ref['abp_ref_waveform_pressure_points']
        keys          = self._heartbeat_viewmodel.reference_point_keys
        for t, p in zip(ref_times, ref_pressures):
            self.ref_points_series.append(float(t), float(p))
        self.chart_view.set_reference_points(
            [QPointF(float(t), float(p)) for t, p in zip(ref_times, ref_pressures)]
        )

        x_min = float(np.min(time_points))
        x_max = float(np.max(time_points))

        # Bottom axis: samples
        self.axis_x_sample.setRange(x_min, x_max)
        self.axis_x_sample.setTickAnchor(0.0)
        self.axis_x_sample.setTickInterval(50)

        # Top axis: time in seconds — derived from BPM only
        bpm = self._heartbeat_viewmodel.get_bpm()
        beat_duration_s = 60.0 / bpm  # e.g. 1.0 s at 60 BPM
        n_samples = len(time_points)

        self.axis_x_time.setRange(0.0, beat_duration_s)
        self.axis_x_time.setTickAnchor(0.0)
        self.axis_x_time.setTickInterval(beat_duration_s / (n_samples / 50))  # ~same density as sample ticks

        self.axis_y.setRange(float(np.min(pressure_points)) - 5, float(np.max(pressure_points)) + 5)
        self._update_ref_table(keys, ref_times, ref_pressures)

    def _update_ref_table(self, keys, ref_times, ref_pressures):
        self.ref_table.blockSignals(True)
        self.ref_table.setRowCount(2)
        self.ref_table.setColumnCount(len(keys))
        self.ref_table.setHorizontalHeaderLabels(list(keys))
        self.ref_table.setVerticalHeaderLabels(["Time (samples)", "Pressure (mmHg)"])
        self.ref_table.verticalHeader().setVisible(True)
        self.ref_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ref_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for col, (t, p) in enumerate(zip(ref_times, ref_pressures)):
            t_item = QTableWidgetItem(f"{int(t)}")
            p_item = QTableWidgetItem(f"{float(p):.1f}")
            for item in (t_item, p_item):
                item.setTextAlignment(Qt.AlignCenter)
            self.ref_table.setItem(0, col, t_item)
            self.ref_table.setItem(1, col, p_item)
        self.ref_table.blockSignals(False)

    def _on_table_cell_changed(self, row: int, col: int):
        keys          = self._heartbeat_viewmodel.reference_point_keys
        ref           = self._heartbeat_viewmodel.reference_abp_waveform
        ref_times     = ref['abp_ref_waveform_time_points']
        ref_pressures = ref['abp_ref_waveform_pressure_points']
        n_samples     = len(self._heartbeat_viewmodel.abp_waveform['abp_waveform_time_points'])
        if col >= len(keys) or n_samples <= 1:
            return
        key = keys[col]
        try:
            if row == 0:
                new_sample   = float(self.ref_table.item(row, col).text())
                new_time_pct = max(0.0, min(1.0, new_sample / (n_samples - 1)))
                self._heartbeat_viewmodel.update_reference_point(key, new_time_pct,
                                                                 float(ref_pressures[col]))
            elif row == 1:
                new_pressure = max(0.0, min(300.0,
                                   float(self.ref_table.item(row, col).text())))
                self._heartbeat_viewmodel.update_reference_point(
                    key, float(ref_times[col]) / (n_samples - 1), new_pressure)
        except (ValueError, TypeError):
            self._update_ref_table(keys, ref_times, ref_pressures)

    def _on_reference_point_moved(self, index: int, new_value: QPointF):
        keys = self._heartbeat_viewmodel.reference_point_keys
        if index >= len(keys):
            return
        n_samples    = len(self._heartbeat_viewmodel.abp_waveform['abp_waveform_time_points'])
        new_time_pct = max(0.0, min(1.0, new_value.x() / (n_samples - 1)))
        new_pressure = max(0.0, min(300.0, new_value.y()))
        self._heartbeat_viewmodel.update_reference_point(keys[index], new_time_pct, new_pressure)

    def _on_reference_point_clicked(self, index: int):
        if index >= self.ref_table.columnCount():
            return
        self.ref_table.blockSignals(True)
        self.ref_table.clearSelection()
        self.ref_table.selectColumn(index)
        self.ref_table.scrollTo(self.ref_table.model().index(0, index))
        self.ref_table.blockSignals(False)

    def _on_load_defaults_clicked(self):
        self._heartbeat_viewmodel.load_default_settings()

    def _on_bpm_changed(self, value: int):
        self._heartbeat_viewmodel.set_bpm(value)

    def _on_sample_rate_changed(self, new_rate: int):
        pass  # Time axis depends on BPM only; waveform_data_changed handles the redraw
