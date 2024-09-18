from PySide6 import QtWidgets, QtCore


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bot Scraping FRS')
        self.setFixedSize(400, 250)

        with open('styles.qss', 'r') as f:
            self.setStyleSheet(f.read())

        self.url_label = QtWidgets.QLabel('URL')
        self.url_input = QtWidgets.QLineEdit()
        self.url_layout = QtWidgets.QHBoxLayout()
        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_input)

        self.run_button = QtWidgets.QPushButton('Rodar')
        self.run_button.clicked.connect(self.run)

        self.export_to_excel_button = QtWidgets.QPushButton('Exportar para Excel')
        self.export_to_excel_button.clicked.connect(self.export_to_excel)

        self.export_to_pdf_button = QtWidgets.QPushButton('Exportar para PDF')
        self.export_to_pdf_button.clicked.connect(self.export_to_pdf)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.url_layout)
        self.main_layout.addWidget(self.run_button)
        self.main_layout.addWidget(self.export_to_excel_button)
        self.main_layout.addWidget(self.export_to_pdf_button)

    @QtCore.Slot()
    def run(self):
        pass

    @QtCore.Slot()
    def export_to_excel(self):
        pass

    @QtCore.Slot()
    def export_to_pdf(self):
        pass
