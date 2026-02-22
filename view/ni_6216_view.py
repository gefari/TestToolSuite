from PySide6.QtWidgets import QWidget, QVBoxLayout

class NI6216View(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)