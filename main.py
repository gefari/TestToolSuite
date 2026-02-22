from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QModelIndex

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QWidget,
    QStackedWidget
    
)

import sys
import model
import view
import viewmodel

import qtawesome as qta

SW_VERSION = "0.0.1"
ABOUT_MSG = f"Testing ToolSuite\n\nVersion {SW_VERSION}\n\nCopyright 2026 Farina Germano\n\nAll rights reserved."

class MainWindow(QMainWindow):
    def __init__(self, theme, settings):
        super().__init__()

        self.setWindowTitle("Testing ToolSuite")
        self.resize(800, 600)
        self.theme = theme
        self.settings = settings

        icon_color = self.theme.default_text_color

        # Create the QStackedWidget to hold the views
        self.stacked_widget = QStackedWidget()
        self.view_lookup = {}

        self.initialize_views()

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(self)

        # List Model
        self.items = [
            model.ItemModel("Heart Beat", "fa5s.sliders-h", "HeartBeat"),
            model.ItemModel("NI DAQMx", "fa5s.sliders-h", "NI_6216_DAQMx")
        ]

        # Create the ViewModel
        list_viewmodel = viewmodel.ItemListViewModel(self.items)

        # Create the LeftPaneView view
        self.left_panel_view = view.LeftPanelView(list_viewmodel)

        # Left Panel: List View
        main_layout.addWidget(self.left_panel_view)

        self.initialize_views()
        main_layout.addWidget(self.stacked_widget)
        central_widget.setLayout(main_layout)

        # Create the MENU BAR
        menu_bar = self.menuBar()

        # MENU BAR - "SETTINGS"
        settings_menu = menu_bar.addMenu("Settings")

        preferences_action = QAction(qta.icon("fa5s.cog", color=icon_color), "Preferences", self)
        preferences_action.triggered.connect(self.show_settings_dialog)

        settings_menu.addAction(preferences_action)

        # MENU BAR - "ABOUT"
        help_menu = menu_bar.addMenu("Help")

        about_action = QAction(qta.icon("fa5s.info-circle", color=icon_color), "About", self)
        about_action.triggered.connect(self.show_about_dialog)

        help_menu.addAction(about_action)

        # TOOLBAR
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)  # Prevent the toolbar from being moved
        self.addToolBar(toolbar)

        # Connect selection change signal to the view model
        self.left_panel_view.selectionModel().currentChanged.connect(self.on_item_selected)

    def initialize_views(self):
        # HEART BEAT VIEW
        self.heart_beat_model = model.HeartBeatModel()
        heart_beat_viewmodel = viewmodel.HeartBeatViewModel(self.heart_beat_model)
        heart_beat_view = view.HeartBeatView(heart_beat_viewmodel) 
        self.view_lookup["HeartBeat"] = heart_beat_view
        self.stacked_widget.addWidget(heart_beat_view)
        # NI VIEW
        ni_6216_view = view.NI6216View() 
        self.view_lookup["NI_6216_DAQMx"] = ni_6216_view
        self.stacked_widget.addWidget(ni_6216_view)

    def on_about_to_quit(self):
        #self.drive_model.stop()
        # Disconnect USB-CAN Peak
        # Disconnect USB NI DAQ
        pass

    # HELP MENU ACTIONS
    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About",
            ABOUT_MSG
        )

    # SETTINGS MENU ACTIONS    
    def show_settings_dialog(self):
        pass

    def on_item_selected(self, current: QModelIndex, previous: QModelIndex):
        index = current.row()
        selected_model = self.left_panel_view.get_selected_model()
        if selected_model:
            view_id = selected_model.view_id
            view_ref = self.view_lookup[view_id]
            if view_ref:
                self.stacked_widget.setCurrentWidget(view_ref)
            self.status_bar.showMessage(f"Selected {selected_model.name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")
    
    settings = model.SettingsModel()

    if settings.theme == "Dark":
        theme = view.themes.DarkTheme(app)
    else:
        theme = view.themes.LightTheme(app)

    window = MainWindow(theme, settings)
    app.aboutToQuit.connect(window.on_about_to_quit)
    
    window.show()
    theme.apply()

    sys.exit(app.exec())