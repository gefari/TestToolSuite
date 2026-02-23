from PySide6.QtWidgets import QListView, QAbstractItemView


class LeftPanelView(QListView):
    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self._viewmodel = viewmodel
        self.setFixedWidth(200)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setModel(self._viewmodel.list_model)

        if self.model().rowCount() > 0:
            self.setCurrentIndex(self.model().index(0, 0))

    def get_selected_model(self):
        current_index = self.currentIndex()
        if current_index.isValid() and self._viewmodel:
            return self._viewmodel.get_item_model(current_index.row())
        return None
