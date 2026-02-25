from PySide6.QtCharts import QChartView
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QMouseEvent, QWheelEvent

ZOOM_FACTOR      = 1.15   # per wheel notch
PAN_BUTTON       = Qt.MiddleButton
PAN_MOD_BUTTON   = Qt.LeftButton
PAN_MODIFIER     = Qt.ControlModifier


class InteractiveChartView(QChartView):

    def __init__(self, chart, on_point_moved_callback=None,
                 on_point_clicked_callback=None, parent=None):
        super().__init__(chart, parent)
        self.setRenderHint(QPainter.Antialiasing)

        self._on_point_moved   = on_point_moved_callback
        self._on_point_clicked = on_point_clicked_callback

        self._dragging_index   = None
        self._ref_points       = []
        self._drag_threshold   = 12.0

        # Pan state
        self._panning          = False
        self._pan_last_pos     = QPointF()

    # ── Public ─────────────────────────────────────────────────────────────

    def set_reference_points(self, points: list[QPointF]):
        self._ref_points = points

    # ── Wheel → Zoom ───────────────────────────────────────────────────────

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta == 0:
            return

        factor = ZOOM_FACTOR if delta > 0 else 1.0 / ZOOM_FACTOR

        # Zoom centered on the cursor position
        cursor_scene = self.mapToScene(event.position().toPoint())
        cursor_chart = self.chart().mapFromScene(cursor_scene)

        self.chart().zoom(factor)

        # Compensate pan so zoom is anchored to cursor, not chart centre
        new_cursor_scene = self.chart().mapToScene(cursor_chart)
        delta_scene = cursor_scene - new_cursor_scene
        self.chart().scroll(-delta_scene.x(), delta_scene.y())

        event.accept()

    # ── Mouse Press ────────────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        # ── Pan: middle button OR Ctrl + left ─────────────────────────────
        if (event.button() == PAN_BUTTON or
                (event.button() == PAN_MOD_BUTTON and
                 event.modifiers() & PAN_MODIFIER)):
            self._panning      = True
            self._pan_last_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        # ── Reference point drag: plain left click ─────────────────────────
        if event.button() == Qt.LeftButton:
            index = self._nearest_point_index(event.position())
            if index is not None:
                self._dragging_index = index
                self.setCursor(Qt.ClosedHandCursor)
                if self._on_point_clicked:
                    self._on_point_clicked(index)
                event.accept()
                return

        super().mousePressEvent(event)

    # ── Mouse Move ─────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event: QMouseEvent):
        # ── Active pan ─────────────────────────────────────────────────────
        if self._panning:
            delta = event.position() - self._pan_last_pos
            self._pan_last_pos = event.position()
            # chart().scroll() takes pixel deltas; Y is inverted (chart Y grows up)
            self.chart().scroll(-delta.x(), delta.y())
            event.accept()
            return

        # ── Active point drag ──────────────────────────────────────────────
        if self._dragging_index is not None:
            value = self._pixel_to_chart_value(event.position())
            if self._on_point_moved:
                self._on_point_moved(self._dragging_index, value)
            event.accept()
            return

        # ── Hover cursor hint ──────────────────────────────────────────────
        idx = self._nearest_point_index(event.position())
        if event.modifiers() & PAN_MODIFIER:
            self.setCursor(Qt.OpenHandCursor)
        elif idx is not None:
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    # ── Mouse Release ──────────────────────────────────────────────────────

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._panning and (
                event.button() == PAN_BUTTON or
                event.button() == PAN_MOD_BUTTON):
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            self._dragging_index = None
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    # ── Double Click → Reset zoom ──────────────────────────────────────────

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.chart().zoomReset()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    # ── Private helpers ────────────────────────────────────────────────────

    def _pixel_to_chart_value(self, pos) -> QPointF:
        scene_pos = self.mapToScene(pos.toPoint())
        chart_pos = self.chart().mapFromScene(scene_pos)
        return self.chart().mapToValue(chart_pos)

    def _nearest_point_index(self, pos) -> int | None:
        for i, pt in enumerate(self._ref_points):
            scene_pt = self.chart().mapToPosition(pt)
            view_pt  = self.mapFromScene(scene_pt)
            dx = view_pt.x() - pos.x()
            dy = view_pt.y() - pos.y()
            if (dx * dx + dy * dy) ** 0.5 <= self._drag_threshold:
                return i
        return None
