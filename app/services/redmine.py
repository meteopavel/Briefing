import os

import pandas as pd
import requests

from app.config import REDMINE_API_KEY, REDMINE_URL, REDMINE_USER_ID


def fetch_and_save_timelog(start_date_str, end_date_str, redmine_filename):
    print(f'📥 Запрашиваем данные из Redmine за {start_date_str} – {end_date_str}...')

    response = requests.get(
        f'{REDMINE_URL}/time_entries.json',
        headers={'X-Redmine-API-Key': REDMINE_API_KEY},
        params={
            'user_id': REDMINE_USER_ID,
            'from': start_date_str,
            'to': end_date_str,
            'limit': 1000,
        },
        timeout=60,
    )
    response.raise_for_status()
    entries = response.json()['time_entries']
    print(f'✅ Получено записей: {len(entries)}')

    if not entries:
        raise ValueError('Нет трудозатрат за указанный период!')

    issue_ids = {int(entry['issue']['id']) for entry in entries if entry.get('issue', {}).get('id')}
    subjects_map = {}

    if issue_ids:
        issue_ids_string = ','.join(str(issue_id) for issue_id in issue_ids)
        print(f'📡 Запрашиваем названия задач ({len(issue_ids)} шт.)...')

        issues_response = requests.get(
            f'{REDMINE_URL}/issues.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            params={
                'issue_id': issue_ids_string,
                'status_id': '*',
                'limit': 1000,
            },
            timeout=60,
        )
        issues_response.raise_for_status()
        issues = issues_response.json()['issues']

        subjects_map = {int(issue['id']): issue['subject'] for issue in issues}
        missing_issue_ids = issue_ids - set(subjects_map.keys())
        if missing_issue_ids:
            print(f'⚠️ Не найдены названия для задач: {missing_issue_ids}')

    records = []
    for entry in entries:
        issue = entry.get('issue', {})
        issue_id = issue.get('id')
        subject = subjects_map.get(int(issue_id), 'Без названия') if issue_id else 'Без задачи'
        task_name = f'Таска #{issue_id}: {subject}' if issue_id else 'Без привязки к задаче'

        records.append(
            {
                'task': task_name,
                'date': entry['spent_on'],
                'hours': entry['hours'],
            }
        )

    raw_dataframe = pd.DataFrame(records)

    date_range = pd.date_range(start=start_date_str, end=end_date_str, freq='D')
    all_dates = [date.strftime('%Y-%m-%d') for date in date_range]

    pivot_dataframe = (
        raw_dataframe.pivot_table(
            index='task',
            columns='date',
            values='hours',
            aggfunc='sum',
            fill_value=0.0,
        )
        .reindex(columns=all_dates, fill_value=0.0)
        .reset_index()
    )

    def format_cell(value):
        return '""' if value == 0.0 else str(value).replace('.', ',')

    for column in all_dates:
        pivot_dataframe[column] = pivot_dataframe[column].apply(format_cell)

    row_totals = []
    for _, row in pivot_dataframe.iterrows():
        total = sum(float(str(value).replace(',', '.')) if value != '""' else 0 for value in row[1:])
        row_totals.append(str(round(total, 2)).replace('.', ','))

    pivot_dataframe['Общее время'] = row_totals

    total_row = ['Общее время']
    grand_total = 0.0

    for column in all_dates:
        column_sum = sum(
            float(str(value).replace(',', '.')) if value != '""' else 0
            for value in pivot_dataframe[column]
        )
        grand_total += column_sum
        total_row.append(str(round(column_sum, 2)).replace('.', ',') if column_sum > 0 else '""')

    total_row.append(str(round(grand_total, 2)).replace('.', ','))

    final_dataframe = pd.concat(
        [
            pivot_dataframe.rename(columns={'task': 'Задача'}),
            pd.DataFrame([total_row], columns=['Задача'] + all_dates + ['Общее время']),
        ],
        ignore_index=True,
    )

    os.makedirs(os.path.dirname(redmine_filename), exist_ok=True)
    final_dataframe.to_csv(redmine_filename, sep=';', index=False, quoting=1)
    print(f'💾 Сохранено: {redmine_filename}')

    return redmine_filename
