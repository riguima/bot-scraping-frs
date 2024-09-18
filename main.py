import sys
from PySide6 import QtWidgets
from bot_scraping_frs.main_window import MainWindow
from qt_material import apply_stylesheet


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    apply_stylesheet(app, 'dark_blue.xml')
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
