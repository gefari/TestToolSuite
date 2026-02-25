from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget
)

from PySide6.QtCore import Qt
import qtawesome as qta

class InnerPanel(QWidget):
    BUTTON_SIZE = 36

    def __init__(self, parent=None):
        super().__init__(parent)

        self._active_index: int | None = None
        self._buttons: list[QPushButton] = []

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Icon strip ──────────────
        self._strip = QWidget()
        self._strip.setFixedWidth(self.BUTTON_SIZE + 8)
        self._strip.setStyleSheet("background-color: #111111;")

        strip_layout = QVBoxLayout(self._strip)
        strip_layout.setContentsMargins(4, 8, 4, 4)
        strip_layout.setSpacing(6)
        strip_layout.setAlignment(Qt.AlignTop)

        self._strip_layout = strip_layout

        # ── Stacked content ────────────────────────────────────────────────
        self._stack = QStackedWidget()

        outer.addWidget(self._strip)
        outer.addWidget(self._stack)

    # ── Public API ─────────────────────────────────────────────────────────
    def add_page(self, icon_name: str, tooltip: str, widget: QWidget) -> int:
        """
        Register a page. Returns its index.
        First page added is shown immediately (like main.py default selection).
        """
        index = len(self._buttons)

        btn = QPushButton()
        btn.setIcon(qta.icon(icon_name, color="#aaaaaa"))
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        btn.setStyleSheet(self._btn_style())
        btn.clicked.connect(lambda _checked, i=index: self._on_btn_clicked(i))

        self._strip_layout.addWidget(btn)
        self._buttons.append(btn)
        self._stack.addWidget(widget)

    def current_index(self) -> int | None:
        return self._active_index

    # ── Private ────────────────────────────────────────────────────────────
    def _on_btn_clicked(self, index: int):
        self._select(index)

    def _select(self, index: int):
        self._active_index = index
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)

    @staticmethod
    def _btn_style() -> str:
        return """
            QPushButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #FFD93D;
            }
            QPushButton:checked {
                background-color: #003300;
                border-color: #00CC00;
            }
        """

