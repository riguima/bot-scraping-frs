import asyncio
from io import BytesIO

import pandas as pd
from httpx import get
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from PySide6 import QtCore, QtWidgets
from sqlalchemy import select

from bot_scraping_frs.browser import get_all_pages_data
from bot_scraping_frs.database import Session
from bot_scraping_frs.models import Product
from bot_scraping_frs.utils import convert_value


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bot Scraping FRS')
        self.setFixedSize(400, 250)

        with open('styles.qss', 'r') as f:
            self.setStyleSheet(f.read())

        self.message_box = QtWidgets.QMessageBox()

        self.url_label = QtWidgets.QLabel('URL')
        self.url_input = QtWidgets.QLineEdit()
        self.url_layout = QtWidgets.QHBoxLayout()
        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_input)

        self.run_button = QtWidgets.QPushButton('Rodar')
        self.run_button.clicked.connect(self.run)

        self.export_to_excel_button = QtWidgets.QPushButton(
            'Exportar para Excel'
        )
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
        if not self.url_input.text():
            self.message_box.setText('Preencha a URL')
            self.message_box.show()
        self.message_box.setText('Aguarde...')
        self.message_box.exec()
        with Session() as session:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(
                get_all_pages_data(self.url_input.text())
            )
            loop.close()
            for item in data:
                query = select(Product).where(Product.url == item['url'])
                item_model = session.scalars(query).first()
                if item_model:
                    item_model.foto = item['foto']
                    item_model.codigo = item['codigo']
                    item_model.descricao = item['descricao']
                    item_model.valor = convert_value(item['valor'])
                else:
                    item_model = Product(
                        url=item['url'],
                        foto=item['foto'],
                        codigo=item['codigo'],
                        descricao=item['descricao'],
                        valor=convert_value(item['valor']),
                    )
                    session.add(item_model)
            session.commit()
            self.message_box.setText('Finalizado!')
            self.message_box.show()

    @QtCore.Slot()
    def export_to_excel(self):
        file_path = QtWidgets.QFileDialog.getSaveFileName()[0]
        if '.xlsx' not in file_path:
            file_path = file_path + '.xlsx'
        with Session() as session:
            items = []
            for item in session.scalars(select(Product)).all():
                items.append(
                    {
                        'url': item.url,
                        'foto': item.foto,
                        'codigo': item.codigo,
                        'descricao': item.descricao,
                        'valor': item.valor,
                    }
                )
            df = pd.DataFrame(items)
            df.to_excel(file_path, index=False)
            wb = load_workbook(file_path)
            ws = wb.active
            self.set_width_to_content(ws, 'B')
            self.set_width_to_content(ws, 'C')
            self.set_width_to_content(ws, 'D')
            ws.column_dimensions['A'].width = 18
            for cell in ws['A:A']:
                if cell.row > 10:
                    continue
                if cell.value and 'http' in cell.value:
                    print(cell.row)
                    ws.row_dimensions[cell.row].height = 100
                    response = get(cell.value, timeout=1000)
                    image_content = BytesIO(response.content)
                    image = Image(image_content)
                    image.width = 130
                    image.height = 130
                    cell.value = ''
                    ws.add_image(image, f'A{cell.row}')
            wb.save(file_path)
        self.message_box.setText('Finalizado!')
        self.message_box.show()

    @QtCore.Slot()
    def export_to_pdf(self):
        pass

    def set_width_to_content(self, ws, column):
        max_length = 0
        for cell in ws[f'{column}:{column}']:
            if max_length < len(str(cell.value)):
                max_length = len(str(cell.value))
        ws.column_dimensions[column].width = max_length + 2
