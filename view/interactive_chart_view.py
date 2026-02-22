from PySide6.QtCharts import QChartView
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QMouseEvent


class InteractiveChartView(QChartView):

    def __init__(self, chart, on_point_moved_callback, on_point_clicked_callback=None, parent=None):
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self._on_point_moved    = on_point_moved_callback
        self._on_point_clicked = on_point_clicked_callback
        self._dragging_index    = None      # index of point being dragged
        self._ref_points        = []        # list of QPointF in chart value coords
        self._drag_threshold    = 12.0      # pixels — hit area radius per dot

    # ── Public ────────────────────────────────────────────────────────────

    def set_reference_points(self, points: list[QPointF]):
        """Update the list of draggable reference points (chart value coords)."""
        self._ref_points = points

    # ── Mouse Events ──────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos   = event.position()
            index = self._nearest_point_index(pos)
            if index is not None:
                self._dragging_index = index
                self.setCursor(Qt.ClosedHandCursor)
                # ── Notify view of click ──────────────────────────────
                if self._on_point_clicked:
                    self._on_point_clicked(index)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging_index is not None:
            value = self._pixel_to_chart_value(event.position())
            self._on_point_moved(self._dragging_index, value)
        else:
            # Change cursor to pointer when hovering over a ref point
            idx = self._nearest_point_index(event.position())
            self.setCursor(Qt.OpenHandCursor if idx is not None else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging_index = None
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    # ── Private Helpers ───────────────────────────────────────────────────

    def _pixel_to_chart_value(self, pos) -> QPointF:
        """Convert a pixel position (view coords) to chart value coords."""
        scene_pos = self.mapToScene(pos.toPoint())
        chart_pos = self.chart().mapFromScene(scene_pos)
        return self.chart().mapToValue(chart_pos)

    def _nearest_point_index(self, pos) -> int | None:
        """Return index of the ref point within drag threshold, or None."""
        for i, pt in enumerate(self._ref_points):
            # Map chart value → scene → view pixels
            scene_pt = self.chart().mapToPosition(pt)
            view_pt  = self.mapFromScene(scene_pt)
            dx = view_pt.x() - pos.x()
            dy = view_pt.y() - pos.y()
            if (dx * dx + dy * dy) ** 0.5 <= self._drag_threshold:
                return i
        return None

