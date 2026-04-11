from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


def set_font(run, name='Times New Roman', size=11):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)


def replace_text_with_formatting(doc, placeholder, replacement_text):
    replacement_text = str(replacement_text)

    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            full_text = paragraph.text
            parts = full_text.split(placeholder)
            paragraph.clear()

            for index, part in enumerate(parts):
                if part:
                    run = paragraph.add_run(part)
                    set_font(run)

                if index < len(parts) - 1:
                    run = paragraph.add_run(replacement_text)
                    set_font(run)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if placeholder in paragraph.text:
                        full_text = paragraph.text
                        parts = full_text.split(placeholder)
                        paragraph.clear()

                        for index, part in enumerate(parts):
                            if part:
                                run = paragraph.add_run(part)
                                set_font(run)

                            if index < len(parts) - 1:
                                run = paragraph.add_run(replacement_text)
                                set_font(run)


def add_table_borders(table):
    table_xml = table._tbl
    table_properties = table_xml.tblPr
    table_borders = OxmlElement('w:tblBorders')

    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'auto')
        table_borders.append(border)

    table_properties.append(table_borders)


def add_table_at_placeholder(doc, df, placeholder='{{TABLE}}'):
    target_paragraph = None

    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            target_paragraph = paragraph
            break

    if not target_paragraph:
        raise ValueError(f"Плейсхолдер '{placeholder}' не найден.")

    paragraph_element = target_paragraph._element
    parent = paragraph_element.getparent()
    index = parent.index(paragraph_element)
    parent.remove(paragraph_element)

    table = doc.add_table(rows=1, cols=len(df.columns))

    header_cells = table.rows[0].cells
    for column_index, column_name in enumerate(df.columns):
        cell = header_cells[column_index]
        cell.text = str(column_name)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run = paragraph.runs[0]
        run.bold = True
        set_font(run, size=10)

    for _, row_data in df.iterrows():
        row_cells = table.add_row().cells

        for column_index, value in enumerate(row_data):
            cell = row_cells[column_index]
            cell.text = str(value)

            if column_index == 0:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

            set_font(cell.paragraphs[0].runs[0], size=10)

    column_widths_inch = [0.4, 1.6, 2.9, 1.3]

    for row in table.rows:
        for column_index, width in enumerate(column_widths_inch):
            row.cells[column_index].width = Inches(width)

    table_xml = table._tbl
    table_properties = table_xml.tblPr

    table_grid = table_xml.find(qn('w:tblGrid'))
    if table_grid is not None:
        table_xml.remove(table_grid)

    table_grid = OxmlElement('w:tblGrid')
    for width in column_widths_inch:
        width_dxa = int(width * 1440)
        grid_col = OxmlElement('w:gridCol')
        grid_col.set(qn('w:w'), str(width_dxa))
        table_grid.append(grid_col)

    table_xml.insert(0, table_grid)

    total_width_dxa = sum(int(width * 1440) for width in column_widths_inch)
    table_width = OxmlElement('w:tblW')
    table_width.set(qn('w:type'), 'dxa')
    table_width.set(qn('w:w'), str(total_width_dxa))
    table_properties.append(table_width)

    add_table_borders(table)

    table_element = table._element
    parent.insert(index, table_element)


def make_bold_first_paragraph(doc):
    if not doc.paragraphs:
        return

    first_paragraph = doc.paragraphs[0]
    for run in first_paragraph.runs:
        set_font(run, name='Times New Roman', size=11)
        run.bold = True
