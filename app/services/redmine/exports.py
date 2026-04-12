import os

import pandas as pd

from app.services.redmine.client import RedmineClient


def build_timelog_records(entries, subjects_map):
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


def build_date_columns(start_date_str, end_date_str):
    date_range = pd.date_range(start=start_date_str, end=end_date_str, freq='D')
    return [date.strftime('%Y-%m-%d') for date in date_range]


def build_timelog_dataframe(records, all_dates):
    raw_dataframe = pd.DataFrame(records)
    pivot_dataframe = (
        raw_dataframe
        .pivot_table(index='task', columns='date', values='hours', aggfunc='sum', fill_value=0.0)
        .reindex(columns=all_dates, fill_value=0.0)
        .reset_index()
    )
    return pivot_dataframe


def format_timelog_value(value):
    return '""' if value == 0.0 else str(value).replace('.', ',')


def format_timelog_dataframe(dataframe, all_dates):
    formatted_dataframe = dataframe.copy()
    for column in all_dates:
        formatted_dataframe[column] = formatted_dataframe[column].apply(format_timelog_value)
    return formatted_dataframe


def parse_formatted_timelog_value(value):
    if value == '""':
        return 0.0
    return float(str(value).replace(',', '.'))


def add_row_totals(dataframe, all_dates):
    dataframe = dataframe.copy()
    row_totals = []
    for _, row in dataframe.iterrows():
        total = sum(parse_formatted_timelog_value(row[column]) for column in all_dates)
        row_totals.append(str(round(total, 2)).replace('.', ','))
    dataframe['Общее время'] = row_totals
    return dataframe


def build_total_row(dataframe, all_dates):
    total_row = ['Общее время']
    grand_total = 0.0
    for column in all_dates:
        column_sum = sum(parse_formatted_timelog_value(value) for value in dataframe[column])
        grand_total += column_sum
        total_row.append(str(round(column_sum, 2)).replace('.', ',') if column_sum > 0 else '""')
    total_row.append(str(round(grand_total, 2)).replace('.', ','))
    return total_row


def append_totals_row(dataframe, all_dates):
    total_row = build_total_row(dataframe, all_dates)
    return pd.concat(
        [
            dataframe.rename(columns={'task': 'Задача'}),
            pd.DataFrame([total_row], columns=['Задача'] + all_dates + ['Общее время']),
        ],
        ignore_index=True,
    )


def save_dataframe_to_csv(dataframe, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    dataframe.to_csv(filename, sep=';', index=False, quoting=1)
    print(f'💾 Сохранено: {filename}')
    return filename


def fetch_and_save_timelog(start_date_str, end_date_str, redmine_filename):
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
