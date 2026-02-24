from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtWidgets import QAbstractItemView
from PySide6.QtCharts import QChart, QLineSeries, QValueAxis, QScatterSeries
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QTimer

from view.interactive_chart_view import InteractiveChartView
import numpy as np

class HeartBeatView(QWidget):

    def __init__(self, viewmodel):
        super().__init__()
        self._viewmodel = viewmodel
        self.initUI()  # ← UI built first
        self._viewmodel.waveform_data_changed.connect(self.update_waveform_data)
        self.update_waveform_data() # ← manual first paint with already-generated data

    # ── UI Setup ──────────────────────────────────────────────────────────
    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Chart
        self.chart = QChart()
        self.chart.setTheme(QChart.ChartThemeDark)
        self.chart.legend().setVisible(True)

        # ABP curve
        self.series = QLineSeries()
        self.series.setName("ABP Waveform")
        self.chart.addSeries(self.series)

        # Reference points
        self.ref_points_series = QScatterSeries()
        self.ref_points_series.setName("Reference Points")
        self.ref_points_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
        self.ref_points_series.setMarkerSize(10.0)
        self.ref_points_series.setColor(QColor("#FFD93D"))
        self.chart.addSeries(self.ref_points_series)

        # ── X Axis — dashed grid every 50 samples ────────────────────────
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Samples")
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTickType(QValueAxis.TicksDynamic)
        self.axis_x.setTickInterval(50)
        self.axis_x.setTickAnchor(0.0)
        self.axis_x.setGridLineVisible(True)

        # ── Y Axis ────────────────────────────────────────────────────────
        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("Pressure (mmHg)")
        self.axis_y.setLabelFormat("%.1f")
        self.axis_y.setGridLineVisible(True)

        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

        # Dashed pen for X grid lines (vertical, every 50 samples)
        dash_pen = QPen(QColor("#555555"))
        dash_pen.setStyle(Qt.DashLine)
        dash_pen.setWidth(1)
        self.axis_x.setGridLinePen(dash_pen)

        for s in [self.series, self.ref_points_series]:
            s.attachAxis(self.axis_x)
            s.attachAxis(self.axis_y)

        # Interactive chart view
        self.chart_view = InteractiveChartView(
            self.chart,
            on_point_moved_callback=self._on_reference_point_moved,
            on_point_clicked_callback=self._on_reference_point_clicked
        )
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        
        main_layout.addWidget(self.chart_view)

        # ── Controls bar ──────────────────────────────────────────────────────
        controls_layout = QHBoxLayout()
        self.btn_load_defaults = QPushButton("↺  Load Defaults")
        self.btn_load_defaults.setToolTip("Reload reference points from the XML settings file")
        self.btn_load_defaults.setFixedHeight(32)
        self.btn_load_defaults.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #00FF00;
                border: 1px solid #00CC00;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #003300;
                border-color: #FFD93D;
                color: #FFD93D;
            }
            QPushButton:pressed {
                background-color: #004400;
            }
        """)

        self.btn_load_defaults.clicked.connect(self._on_load_defaults_clicked)

        controls_layout.addStretch()          # pushes button to the right
        controls_layout.addWidget(self.btn_load_defaults)

        # Reference points legend table
        self.ref_table = QTableWidget()
        self.ref_table.setRowCount(2)
        self.ref_table.setColumnCount(0)          # populated dynamically
        self.ref_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ref_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ref_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.SelectedClicked)
        self.ref_table.setSelectionMode(QTableWidget.SingleSelection)
        self.ref_table.setMaximumHeight(100)      # only 2 data rows now, less height needed
        self.ref_table.setAlternatingRowColors(True)
        self.ref_table.setStyleSheet("""
            QTableWidget {
                background-color: #000000;
                color: #00FF00;
                gridline-color: #1a1a1a;
                font-size: 12px;
            }
            QTableWidget::item {
                background-color: #000000;
                color: #00FF00;
                padding: 4px;
            }
            QTableWidget::item:alternate {
                background-color: #0a0a0a;
            }
            QTableWidget::item:selected {
                background-color: #004400;
                color: #00FF00;
                border: 1px solid #FFD93D;
            }
            QHeaderView::section {
                background-color: #111111;
                color: #00CC00;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #1a1a1a;
            }
            QHeaderView::section:checked {
                background-color: #003300;
                color: #FFD93D;
            }
            QTableCornerButton::section {
                background-color: #111111;
                border: 1px solid #1a1a1a;
            }
        """)

        self.ref_table.setSelectionBehavior(QTableWidget.SelectColumns)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.ref_table)
        self.ref_table.cellChanged.connect(self._on_table_cell_changed)

    # ── Waveform Update ───────────────────────────────────────────────────
    def update_waveform_data(self):
        self.series.clear()
        self.ref_points_series.clear()

        waveform        = self._viewmodel.abp_waveform
        time_points     = waveform['abp_waveform_time_points']
        pressure_points = waveform['abp_waveform_pressure_points']

        if len(time_points) == 0:
            return

        # ABP curve
        for t, p in zip(time_points, pressure_points):
            self.series.append(float(t), float(p))

        # Reference scatter dots
        ref           = self._viewmodel.reference_abp_waveform
        ref_times     = ref['abp_ref_waveform_time_points']
        ref_pressures = ref['abp_ref_waveform_pressure_points']
        keys          = self._viewmodel.reference_point_keys

        for t, p in zip(ref_times, ref_pressures):
            self.ref_points_series.append(float(t), float(p))

        self.chart_view.set_reference_points(
            [QPointF(float(t), float(p)) for t, p in zip(ref_times, ref_pressures)]
        )

        # Axes — reaffirm tick settings after range change
        #self.axis_x.setRange(float(min(time_points)), float(max(time_points)))
        self.axis_x.setRange(float(np.min(time_points)), float(np.max(time_points)))
        self.axis_x.setTickAnchor(0.0)
        self.axis_x.setTickInterval(50)
        #self.axis_y.setRange(float(min(pressure_points)) - 5,
        #                     float(max(pressure_points)) + 5)
        self.axis_y.setRange(float(np.min(pressure_points)) - 5, float(np.max(pressure_points)) + 5)

        # ── Refresh legend table ──────────────────────────────────────────────
        self._update_ref_table(keys, ref_times, ref_pressures)


    def _update_ref_table(self, keys, ref_times, ref_pressures):
        self.ref_table.blockSignals(True)

        # One column per reference point
        self.ref_table.setRowCount(2)                    # Row 0: Time, Row 1: Pressure
        self.ref_table.setColumnCount(len(keys))
        self.ref_table.setHorizontalHeaderLabels(list(keys))
        self.ref_table.setVerticalHeaderLabels(["Time (samples)", "Pressure (mmHg)"])
        self.ref_table.verticalHeader().setVisible(True)
        self.ref_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ref_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for col, (t, p) in enumerate(zip(ref_times, ref_pressures)):
            time_item = QTableWidgetItem(f"{int(t)}")
            pres_item = QTableWidgetItem(f"{float(p):.1f}")

            for item in (time_item, pres_item):
                item.setTextAlignment(Qt.AlignCenter)

            self.ref_table.setItem(0, col, time_item)    # row 0 → time
            self.ref_table.setItem(1, col, pres_item)    # row 1 → pressure

        self.ref_table.blockSignals(False)


    def _on_table_cell_changed(self, row: int, col: int):
        # row 0 = Time (samples), row 1 = Pressure (mmHg)
        # col  = feature index

        keys          = self._viewmodel.reference_point_keys
        ref           = self._viewmodel.reference_abp_waveform
        ref_times     = ref['abp_ref_waveform_time_points']
        ref_pressures = ref['abp_ref_waveform_pressure_points']
        n_samples     = len(self._viewmodel.abp_waveform['abp_waveform_time_points'])

        if col >= len(keys):
            return

        key = keys[col]

        try:
            if row == 0:
                # User edited Time (samples) → convert to percentage
                new_sample   = float(self.ref_table.item(row, col).text())
                new_time_pct = max(0.0, min(1.0, new_sample / (n_samples - 1)))
                self._viewmodel.update_reference_point(key, new_time_pct, float(ref_pressures[col]))

            elif row == 1:
                # User edited Pressure (mmHg)
                new_pressure = max(0.0, min(300.0, float(self.ref_table.item(row, col).text())))
                self._viewmodel.update_reference_point(key, float(ref_times[col]) / (n_samples - 1), new_pressure)

        except (ValueError, TypeError):
            self._update_ref_table(keys, ref_times, ref_pressures)


    def _on_reference_point_moved(self, index: int, new_value: QPointF):
        """
        Called by the View when the user drags a reference point.
        
        :param index: Index of the reference point in the model.
        :param new_value: The new position of the reference point in chart value coordinates.
        :return: None
        """
        keys = self._viewmodel.reference_point_keys

        if index >= len(keys):
            return

        key       = keys[index]
        n_samples = len(self._viewmodel.abp_waveform['abp_waveform_time_points'])

        new_time_pct = max(0.0, min(1.0, new_value.x() / (n_samples - 1)))
        new_pressure = max(0.0, min(300.0, new_value.y()))

        self._viewmodel.update_reference_point(key, new_time_pct, new_pressure)

    def _on_reference_point_clicked(self, index: int):
        if index >= self.ref_table.columnCount():
            return
        self.ref_table.blockSignals(True)
        self.ref_table.clearSelection()
        self.ref_table.selectColumn(index)
        self.ref_table.scrollTo(self.ref_table.model().index(0, index))
        self.ref_table.blockSignals(False)

    def _on_load_defaults_clicked(self):
        self._viewmodel.load_default_settings()
        # waveform_data_changed fires automatically → update_waveform_data() redraws everything
