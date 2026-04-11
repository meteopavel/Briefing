import os

import pandas as pd
from docx import Document

from app.config import ACT_TEMPLATE_FILE, OUTPUT_DIR, REPORT_TEMPLATE_FILE
from app.utils.dates import format_date, is_valid_dd_mm_yyyy
from app.utils.docx_utils import (
    add_table_at_placeholder,
    make_bold_first_paragraph,
    replace_text_with_formatting,
)
from app.utils.money import amount_to_words_rubles


def generate_act(row, output_dir=OUTPUT_DIR):
    act_num = int(row['act_num'])
    month_name = row['month']
    total_amount = int(row['total_amount'])
    start_date_str = row['start_date'].strip()
    end_date_str = row['end_date'].strip()

    if not (is_valid_dd_mm_yyyy(start_date_str) and is_valid_dd_mm_yyyy(end_date_str)):
        raise ValueError(f'Неверный формат дат в строке акта №{act_num}')

    document = Document(ACT_TEMPLATE_FILE)
    total_words = amount_to_words_rubles(total_amount)

    replace_text_with_formatting(document, '{{ACT_NUM}}', act_num)
    replace_text_with_formatting(document, '{{START_DATE}}', format_date(start_date_str))
    replace_text_with_formatting(document, '{{END_DATE}}', format_date(end_date_str))
    replace_text_with_formatting(document, '{{TOTAL_AMOUNT}}', total_amount)
    replace_text_with_formatting(document, '{{TOTAL_WORDS}}', total_words)

    make_bold_first_paragraph(document)

    filename = f'Найденов Акт №{act_num} {month_name}.docx'
    path = os.path.join(output_dir, filename)
    document.save(path)

    print(f'✅ Акт сохранён: {filename}')
    return path


def generate_report(row, output_dir=OUTPUT_DIR, debug_print=False):
    report_num = int(row['act_num'])
    month_name = row['month']
    total_amount = int(row['total_amount'])
    redmine_file = row['redmine_file']
    start_date_str = row['start_date'].strip()
    end_date_str = row['end_date'].strip()

    if not os.path.exists(redmine_file):
        raise FileNotFoundError(f'Файл трудозатрат не найден: {redmine_file}')

    dataframe = pd.read_csv(redmine_file, sep=';', na_values=['-', ' ', '""'])
    dataframe['Общее время'] = dataframe['Общее время'].str.replace(',', '.', regex=True)
    dataframe['Общее время'] = pd.to_numeric(dataframe['Общее время'], errors='coerce')
    total_hours = dataframe['Общее время'].iloc[-1]

    dataframe['Расчет Вознаграждения'] = (dataframe['Общее время'] / total_hours) * total_amount
    dataframe['Расчет Вознаграждения'] = dataframe['Расчет Вознаграждения'].apply(
        lambda value: max(round(value / 50) * 50, 50)
    )

    current_total = dataframe['Расчет Вознаграждения'].iloc[:-1].sum()
    difference = total_amount - current_total

    if difference != 0:
        max_index = dataframe['Расчет Вознаграждения'].iloc[:-1].idxmax()
        dataframe.at[max_index, 'Расчет Вознаграждения'] += difference

    dates = dataframe.columns[1:-2]

    def get_date_range(row_data):
        non_zero_indices = row_data.iloc[1:-2].dropna().index
        if len(non_zero_indices) == 0:
            return '-', '-'

        start_date = dates[dates.get_loc(non_zero_indices[0])]
        end_date = dates[dates.get_loc(non_zero_indices[-1])]

        return (
            f'{start_date[8:10]}.{start_date[5:7]}.{start_date[0:4]}',
            f'{end_date[8:10]}.{end_date[5:7]}.{end_date[0:4]}',
        )

    dataframe[['Дата начала', 'Дата окончания']] = dataframe.apply(
        get_date_range,
        axis=1,
        result_type='expand',
    )

    result_dataframe = pd.DataFrame(
        {
            '№': range(1, len(dataframe)),
            'Дата начала и окончания оказания услуги': dataframe.apply(
                lambda row_data: f"{row_data['Дата начала']} - {row_data['Дата окончания']}",
                axis=1,
            ).iloc[:-1],
            'Наименование услуги': dataframe['Задача'].iloc[:-1],
            'Расчет Вознаграждения': dataframe['Расчет Вознаграждения'].iloc[:-1],
        }
    )

    if debug_print:
        print('\n=== ТАБЛИЦА РАСЧЁТА ===')
        print(result_dataframe.to_string(index=False))
        print('========================\n')

    document = Document(REPORT_TEMPLATE_FILE)
    total_words = amount_to_words_rubles(total_amount)

    replace_text_with_formatting(document, '{{REPORT_NUM}}', report_num)
    replace_text_with_formatting(document, '{{START_DATE}}', format_date(start_date_str))
    replace_text_with_formatting(document, '{{END_DATE}}', format_date(end_date_str))
    replace_text_with_formatting(document, '{{END_DATE_SHORT}}', format_date(end_date_str, short=True))
    replace_text_with_formatting(document, '{{TOTAL_AMOUNT}}', total_amount)
    replace_text_with_formatting(document, '{{TOTAL_WORDS}}', total_words)

    add_table_at_placeholder(document, result_dataframe)
    make_bold_first_paragraph(document)

    filename = f'Найденов Отчёт №{report_num} {month_name}.docx'
    path = os.path.join(output_dir, filename)
    document.save(path)

    print(f'✅ Отчёт сохранён: {filename}')
    return path
