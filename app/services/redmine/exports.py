"""
Экспорт трудозатрат Redmine в табличный CSV-формат.
Модуль отвечает за:
- преобразование time entries в плоские записи;
- построение таблицы трудозатрат по дням;
- форматирование значений для CSV;
- добавление итогов по строкам и по всем задачам;
- сохранение итогового файла.
"""

import csv
import os
from typing import Any

import pandas as pd

from app.services.redmine.client import RedmineClient


def build_timelog_records(
    entries: list[dict[str, Any]],
    subjects_map: dict[int, str],
) -> list[dict[str, Any]]:
    """
    Преобразует список time entries в плоские записи для табличного экспорта.
    Для каждой записи формирует имя задачи и сохраняет дату и количество часов.
    """
    records = []
    for entry in entries:
        issue = entry.get('issue', {})
        issue_id = issue.get('id')
        if issue_id:
            subject = subjects_map.get(int(issue_id), 'Без названия')
            task_name = f'Таска #{issue_id}: {subject}'
        else:
            task_name = 'Без привязки к задаче'
        records.append({
            'task': task_name,
            'date': entry['spent_on'],
            'hours': entry['hours'],
        })
    return records


def build_date_columns(start_date_str: str, end_date_str: str) -> list[str]:
    """
    Строит список дат периода в формате YYYY-MM-DD с дневным шагом.
    """
    date_range = pd.date_range(start=start_date_str, end=end_date_str, freq='D')
    return [date.strftime('%Y-%m-%d') for date in date_range]


def build_timelog_dataframe(
    records: list[dict[str, Any]],
    all_dates: list[str],
) -> pd.DataFrame:
    """
    Строит pivot-таблицу трудозатрат по задачам и датам.
    На выходе возвращает DataFrame, где строки — задачи, а колонки — даты периода.
    """
    raw_dataframe = pd.DataFrame(records)
    pivot_dataframe = (
        raw_dataframe
        .pivot_table(index='task', columns='date', values='hours', aggfunc='sum', fill_value=0.0)
        .reindex(columns=all_dates, fill_value=0.0)
        .reset_index()
    )
    return pivot_dataframe


def format_timelog_value(value: Any) -> str:
    """
    Форматирует числовое значение трудозатрат для CSV.
    Нулевые значения преобразуются в `""`, дробная часть записывается через запятую.
    """
    return '""' if value == 0.0 else str(value).replace('.', ',')


def format_timelog_dataframe(dataframe: pd.DataFrame, all_dates: list[str]) -> pd.DataFrame:
    """
    Применяет форматирование значений ко всем дневным колонкам DataFrame.
    """
    formatted_dataframe = dataframe.copy()
    for column in all_dates:
        formatted_dataframe[column] = formatted_dataframe[column].apply(format_timelog_value)
    return formatted_dataframe


def parse_formatted_timelog_value(value: Any) -> float:
    """
    Преобразует форматированное строковое значение трудозатрат обратно в число.
    """
    if value == '""':
        return 0.0
    return float(str(value).replace(',', '.'))


def add_row_totals(dataframe: pd.DataFrame, all_dates: list[str]) -> pd.DataFrame:
    """
    Добавляет в DataFrame колонку с итоговым временем по каждой строке.
    """
    dataframe = dataframe.copy()
    row_totals = []
    for _, row in dataframe.iterrows():
        total = sum(parse_formatted_timelog_value(row[column]) for column in all_dates)
        row_totals.append(str(round(total, 2)).replace('.', ','))
    dataframe['Общее время'] = row_totals
    return dataframe


def build_total_row(dataframe: pd.DataFrame, all_dates: list[str]) -> list[str]:
    """
    Строит итоговую строку с суммами по всем датам и общим итогом.
    """
    total_row = ['Общее время']
    grand_total = 0.0
    for column in all_dates:
        column_sum = sum(parse_formatted_timelog_value(value) for value in dataframe[column])
        grand_total += column_sum
        total_row.append(str(round(column_sum, 2)).replace('.', ',') if column_sum > 0 else '""')
    total_row.append(str(round(grand_total, 2)).replace('.', ','))
    return total_row


def append_totals_row(dataframe: pd.DataFrame, all_dates: list[str]) -> pd.DataFrame:
    """
    Переименовывает колонку задачи и добавляет в конец DataFrame итоговую строку.
    """
    total_row = build_total_row(dataframe, all_dates)
    return pd.concat(
        [
            dataframe.rename(columns={'task': 'Задача'}),
            pd.DataFrame([total_row], columns=['Задача'] + all_dates + ['Общее время']),
        ],
        ignore_index=True,
    )


def save_dataframe_to_csv(dataframe: pd.DataFrame, filename: str) -> str:
    """
    Сохраняет DataFrame в CSV-файл с разделителем `;`.
    Если директория назначения отсутствует, она будет создана.
    """
    output_dir = os.path.dirname(filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    dataframe.to_csv(filename, sep=';', index=False, quoting=csv.QUOTE_ALL)
    print(f'💾 Сохранено: {filename}')
    return filename


def fetch_and_save_timelog(start_date_str: str, end_date_str: str, redmine_filename: str) -> str:
    """
    Загружает time entries из Redmine за период, строит CSV-таблицу и сохраняет её в файл.
    """
    entries = RedmineClient.fetch_time_entries(start_date_str, end_date_str)
    if not entries:
        raise ValueError('Нет трудозатрат за указанный период!')
    issue_ids = {
        int(entry['issue']['id'])
        for entry in entries
        if entry.get('issue', {}).get('id')
    }
    subjects_map = RedmineClient.fetch_issue_subjects(issue_ids)
    records = build_timelog_records(entries, subjects_map)
    all_dates = build_date_columns(start_date_str, end_date_str)
    dataframe = build_timelog_dataframe(records, all_dates)
    dataframe = format_timelog_dataframe(dataframe, all_dates)
    dataframe = add_row_totals(dataframe, all_dates)
    dataframe = append_totals_row(dataframe, all_dates)
    return save_dataframe_to_csv(dataframe, redmine_filename)
