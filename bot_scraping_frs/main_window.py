import asyncio
from io import BytesIO

import pandas as pd
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Cm
from httpx import get
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, PatternFill
from PySide6 import QtCore, QtWidgets
from sqlalchemy import select

from bot_scraping_frs.browser import get_all_pages_data
from bot_scraping_frs.database import Session
from bot_scraping_frs.models import Product
from bot_scraping_frs.utils import convert_value, format_number


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Bot Scraping FRS')
        self.setFixedSize(400, 250)

        with open('styles.qss', 'r') as f:
            self.setStyleSheet(f.read())

        self.message_box = QtWidgets.QMessageBox()

        with Session() as session:
            products = session.scalars(select(Product)).all()
            self.products_label = QtWidgets.QLabel(
                f'Produtos: {len(products)}',
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )
            self.products_label.setStyleSheet('font-weight: bold')

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
        self.main_layout.addWidget(self.products_label)
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
            self.update_products_label()
            self.url_input.setText('')
            self.message_box.setText('Finalizado!')
            self.message_box.show()

    def update_products_label(self):
        with Session() as session:
            products = session.scalars(select(Product)).all()
            self.products_label.setText(f'Produtos: {len(products)}')

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
                        'Foto': item.foto,
                        'Código': item.codigo,
                        'Descrição': item.descricao,
                        'Valor': format_number(item.valor),
                    }
                )
            df = pd.DataFrame(items)
            df.to_excel(file_path, index=False)
            wb = load_workbook(file_path)
            ws = wb.active
            self.set_width_to_content(ws, 'B')
            self.set_width_to_content(ws, 'C')
            self.set_width_to_content(ws, 'D')
            self.set_alignment(ws, 'B')
            self.set_alignment(ws, 'C')
            self.set_alignment(ws, 'D')
            ws.column_dimensions['A'].width = 18
            fill = PatternFill(
                fill_type='solid', start_color='000000', end_color='000000'
            )
            for column in ws['A1:D1']:
                for cell in column:
                    cell.fill = fill
            for cell in ws['A:A']:
                if cell.row > 10:
                    continue
                if cell.value and 'http' in cell.value:
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
        file_path = QtWidgets.QFileDialog.getSaveFileName()[0]
        if '.pdf' not in file_path:
            file_path = file_path + '.pdf'
        with Session() as session:
            products = session.scalars(select(Product)).all()
            document = Document()
            section = document.sections[0]
            section.top_margin = Cm(1)
            section.bottom_margin = Cm(1)
            section.left_margin = Cm(1)
            section.right_margin = Cm(1)
            table = document.add_table(rows=len(products) + 1, cols=4)
            table.cell(0, 0).text = 'Foto'
            table.cell(0, 1).text = 'Código'
            table.cell(0, 2).text = 'Descrição'
            table.cell(0, 3).text = 'Valor'
            table.cell(0, 0)._tc.get_or_add_tcPr().append(
                parse_xml(r'<w:shd {} w:fill="000000"/>'.format(nsdecls('w')))
            )
            table.cell(0, 1)._tc.get_or_add_tcPr().append(
                parse_xml(r'<w:shd {} w:fill="000000"/>'.format(nsdecls('w')))
            )
            table.cell(0, 2)._tc.get_or_add_tcPr().append(
                parse_xml(r'<w:shd {} w:fill="000000"/>'.format(nsdecls('w')))
            )
            table.cell(0, 3)._tc.get_or_add_tcPr().append(
                parse_xml(r'<w:shd {} w:fill="000000"/>'.format(nsdecls('w')))
            )
            self.make_rows_bold(table.rows[0])
            self.align_rows(table)
            for e, product in enumerate(products[:5]):
                response = get(product.foto, timeout=1000)
                image_content = BytesIO(response.content)
                paragraph = table.cell(e + 1, 0).paragraphs[0]
                run = paragraph.add_run()
                run.add_picture(image_content, width=Cm(4))
                table.cell(e + 1, 1).text = product.codigo
                table.cell(e + 1, 2).text = product.descricao
                table.cell(e + 1, 3).text = format_number(product.valor)
            document.save(file_path)
        self.message_box.setText('Finalizado!')
        self.message_box.show()

    def set_width_to_content(self, ws, column):
        max_length = 0
        for cell in ws[f'{column}:{column}']:
            if max_length < len(str(cell.value)):
                max_length = len(str(cell.value))
        ws.column_dimensions[column].width = max_length + 2

    def set_alignment(self, ws, column):
        alignment = Alignment(horizontal='center', vertical='center')
        for cell in ws[f'{column}:{column}']:
            cell.alignment = alignment

    def make_rows_bold(self, *rows):
        for row in rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True

    def align_rows(self, table):
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    paragraph.alignment = WD_ALIGN_VERTICAL.CENTER
