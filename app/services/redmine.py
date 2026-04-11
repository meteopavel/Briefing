import json
import os
import re

import pandas as pd
import requests

from app.config import (
    REDMINE_API_KEY, REDMINE_URL, REDMINE_USER_ID, USER_MAP, ISSUE_STATUS_MAP, ISSUE_PRIORITY_MAP,
    CUSTOM_FIELD_MAP, CUSTOM_FIELDS_HIDE_IF_NEGATIVE,
)


def fetch_time_entries(start_date_str, end_date_str):
    print(f'📥 Запрашиваем time entries из Redmine за {start_date_str} – {end_date_str}...')
    response = requests.get(
        f'{REDMINE_URL}/time_entries.json',
        headers={'X-Redmine-API-Key': REDMINE_API_KEY},
        params={'user_id': REDMINE_USER_ID, 'from': start_date_str, 'to': end_date_str, 'limit': 1000},
        timeout=60,
    )
    response.raise_for_status()
    entries = response.json().get('time_entries', [])
    print(f'✅ Получено записей time entries: {len(entries)}')
    return entries


def fetch_issue_subjects(issue_ids):
    if not issue_ids:
        return {}

    issue_ids_string = ','.join(str(issue_id) for issue_id in sorted(issue_ids))
    print(f'📡 Запрашиваем названия задач ({len(issue_ids)} шт.)...')
    response = requests.get(
        f'{REDMINE_URL}/issues.json',
        headers={'X-Redmine-API-Key': REDMINE_API_KEY},
        params={'issue_id': issue_ids_string, 'status_id': '*', 'limit': 1000},
        timeout=60,
    )
    response.raise_for_status()
    issues = response.json().get('issues', [])
    subjects_map = {int(issue['id']): issue['subject'] for issue in issues}

    missing_issue_ids = set(issue_ids) - set(subjects_map.keys())
    if missing_issue_ids:
        print(f'⚠️ Не найдены названия для задач: {missing_issue_ids}')

    return subjects_map


def fetch_issue_with_journals(issue_id):
    print(f'📄 Запрашиваем расширенный контекст задачи #{issue_id}...')
    response = requests.get(
        f'{REDMINE_URL}/issues/{issue_id}.json',
        headers={'X-Redmine-API-Key': REDMINE_API_KEY},
        params={'include': 'journals'},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()['issue']


def fetch_issue(issue_id):
    response = requests.get(
        f'{REDMINE_URL}/issues/{issue_id}.json',
        headers={'X-Redmine-API-Key': REDMINE_API_KEY},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()['issue']


def fetch_and_save_timelog(start_date_str, end_date_str, redmine_filename):
    entries = fetch_time_entries(start_date_str, end_date_str)
    if not entries:
        raise ValueError('Нет трудозатрат за указанный период!')

    issue_ids = {int(entry['issue']['id']) for entry in entries if entry.get('issue', {}).get('id')}
    subjects_map = fetch_issue_subjects(issue_ids)

    records = []
    for entry in entries:
        issue = entry.get('issue', {})
        issue_id = issue.get('id')
        subject = subjects_map.get(int(issue_id), 'Без названия') if issue_id else 'Без задачи'
        task_name = f'Таска #{issue_id}: {subject}' if issue_id else 'Без привязки к задаче'
        records.append({'task': task_name, 'date': entry['spent_on'], 'hours': entry['hours']})

    raw_dataframe = pd.DataFrame(records)
    date_range = pd.date_range(start=start_date_str, end=end_date_str, freq='D')
    all_dates = [date.strftime('%Y-%m-%d') for date in date_range]

    pivot_dataframe = (
        raw_dataframe.pivot_table(index='task', columns='date', values='hours', aggfunc='sum', fill_value=0.0)
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
        column_sum = sum(float(str(value).replace(',', '.')) if value != '""' else 0 for value in pivot_dataframe[column])
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


def compact_value(value):
    if value in (None, '', [], {}):
        return None
    return value


def compact_dict(data):
    return {key: value for key, value in data.items() if value not in (None, '', [], {})}


def normalize_text(value):
    if value in (None, ''):
        return None
    value = str(value)
    value = value.replace('\r\n', '\n').replace('\r', '\n')
    value = '\n'.join(line.rstrip() for line in value.split('\n'))
    value = re.sub(r'\n{3,}', '\n\n', value)
    value = value.strip()
    return value or None


def resolve_user_name(value):
    if value in (None, ''):
        return None
    try:
        user_id = int(value)
    except (TypeError, ValueError):
        return value
    return USER_MAP.get(user_id, str(user_id))


def resolve_status_name(value):
    if value in (None, ''):
        return None
    try:
        status_id = int(value)
    except (TypeError, ValueError):
        return value
    return ISSUE_STATUS_MAP.get(status_id, str(status_id))


def resolve_priority_name(value):
    if value in (None, ''):
        return None
    try:
        priority_id = int(value)
    except (TypeError, ValueError):
        return value
    return ISSUE_PRIORITY_MAP.get(priority_id, str(priority_id))


def resolve_custom_field_value(field_id, value):
    if value in (None, ''):
        return None
    if field_id in (16, 17, 18, 19):
        return resolve_user_name(value)
    if isinstance(value, str):
        return normalize_text(value)
    return value


def should_keep_custom_field(field_name, field_value):
    if field_value in (None, '', [], {}):
        return False
    negative_values = CUSTOM_FIELDS_HIDE_IF_NEGATIVE.get(field_name)
    if negative_values and str(field_value) in negative_values:
        return False
    return True


def safe_fetch_issue_brief(issue_id):
    try:
        issue_data = fetch_issue(issue_id)
    except Exception:
        return {'id': issue_id}

    priority = issue_data.get('priority') or {}
    priority_name = priority.get('name')
    if not priority_name and priority.get('id') is not None:
        priority_name = resolve_priority_name(priority.get('id'))

    return compact_dict({'id': issue_data.get('id', issue_id), 'subject': normalize_text(issue_data.get('subject')), 'priority': priority_name})


def extract_related_issue_ids(issue_data):
    related_ids = set()
    current_issue_id = issue_data.get('id')

    for relation in issue_data.get('relations', []) or []:
        issue_to_id = relation.get('issue_to_id')
        issue_from_id = relation.get('issue_from_id')
        if issue_to_id and issue_to_id != current_issue_id:
            related_ids.add(int(issue_to_id))
        if issue_from_id and issue_from_id != current_issue_id:
            related_ids.add(int(issue_from_id))

    for journal in issue_data.get('journals', []) or []:
        for detail in journal.get('details', []) or []:
            if detail.get('property') == 'relation':
                for value_key in ('old_value', 'new_value'):
                    value = detail.get(value_key)
                    if value in (None, ''):
                        continue
                    try:
                        related_id = int(value)
                    except (TypeError, ValueError):
                        continue
                    if related_id != current_issue_id:
                        related_ids.add(related_id)

    return sorted(related_ids)


def build_related_issues(issue_data):
    related_ids = extract_related_issue_ids(issue_data)
    return [safe_fetch_issue_brief(related_issue_id) for related_issue_id in related_ids]


def normalize_journal_details(details):
    normalized = []
    for detail in details or []:
        property_name = detail.get('property')
        name = detail.get('name')
        old_value = detail.get('old_value')
        new_value = detail.get('new_value')

        if property_name == 'cf':
            try:
                field_id = int(name)
            except (TypeError, ValueError):
                field_id = None

            field_name = CUSTOM_FIELD_MAP.get(field_id, f'cf_{name}')
            old_resolved = resolve_custom_field_value(field_id, old_value)
            new_resolved = resolve_custom_field_value(field_id, new_value)
            if not should_keep_custom_field(field_name, new_resolved):
                continue

            item = compact_dict({'field': field_name, 'from': old_resolved, 'to': new_resolved})
            if item:
                normalized.append(item)
            continue

        if property_name == 'attr' and name == 'status_id':
            item = compact_dict({'field': 'status', 'from': resolve_status_name(old_value), 'to': resolve_status_name(new_value)})
            if item:
                normalized.append(item)
            continue

        if property_name == 'attr' and name == 'assigned_to_id':
            item = compact_dict({'field': 'assigned_to', 'from': resolve_user_name(old_value), 'to': resolve_user_name(new_value)})
            if item:
                normalized.append(item)
            continue

        if property_name == 'attr' and name == 'done_ratio':
            continue
        if property_name == 'relation':
            continue

        item = compact_dict({
            'field': name,
            'from': normalize_text(old_value) if isinstance(old_value, str) else old_value,
            'to': normalize_text(new_value) if isinstance(new_value, str) else new_value,
        })
        if item:
            normalized.append(item)

    return normalized


def normalize_time_entry(entry, include_project=False):
    return compact_dict({
        'spent_on': entry.get('spent_on'),
        'hours': entry.get('hours'),
        'comments': normalize_text(entry.get('comments')),
        'activity': (entry.get('activity') or {}).get('name'),
        'project': (entry.get('project') or {}).get('name') if include_project else None,
    })


def normalize_custom_fields(custom_fields):
    result = {}
    for field in custom_fields or []:
        field_id = field.get('id')
        field_name = CUSTOM_FIELD_MAP.get(field_id, field.get('name'))
        field_value = resolve_custom_field_value(field_id, field.get('value'))
        if not should_keep_custom_field(field_name, field_value):
            continue
        result[field_name] = field_value
    return result


def normalize_journals(journals):
    result = []
    for journal in journals or []:
        notes = normalize_text(journal.get('notes'))
        changes = normalize_journal_details(journal.get('details', []))
        item = compact_dict({
            'created_on': journal.get('created_on'),
            'user': (journal.get('user') or {}).get('name'),
            'notes': notes,
            'changes': changes if changes else None,
        })
        if not notes and not changes:
            continue
        if item:
            result.append(item)
    return result


def build_issue_context(issue_data, time_entries_in_period):
    spent_hours_in_period = round(sum(entry['hours'] for entry in time_entries_in_period), 2)
    return compact_dict({
        'id': issue_data.get('id'),
        'subject': normalize_text(issue_data.get('subject')),
        'description': normalize_text(issue_data.get('description')),
        'project': (issue_data.get('project') or {}).get('name'),
        'tracker': (issue_data.get('tracker') or {}).get('name'),
        'status': (issue_data.get('status') or {}).get('name'),
        'priority': (issue_data.get('priority') or {}).get('name'),
        'author': (issue_data.get('author') or {}).get('name'),
        'assigned_to': (issue_data.get('assigned_to') or {}).get('name'),
        'created_on': issue_data.get('created_on'),
        'updated_on': issue_data.get('updated_on'),
        'done_ratio': issue_data.get('done_ratio'),
        'related_issues': build_related_issues(issue_data),
        'custom_fields': normalize_custom_fields(issue_data.get('custom_fields', [])),
        'spent_hours_total': issue_data.get('spent_hours'),
        'spent_hours_in_period': spent_hours_in_period,
        'time_entries': time_entries_in_period if time_entries_in_period else None,
        'journals': normalize_journals(issue_data.get('journals', [])),
    })


def export_issue_contexts_for_period(start_date_str, end_date_str, output_filename, issue_id=None):
    entries = fetch_time_entries(start_date_str, end_date_str)
    if not entries:
        raise ValueError('Нет трудозатрат за указанный период!')

    issue_entries_map = {}
    entries_without_issue = []

    for entry in entries:
        issue = entry.get('issue')
        if not issue or not issue.get('id'):
            normalized_entry = normalize_time_entry(entry, include_project=True)
            if normalized_entry:
                entries_without_issue.append(normalized_entry)
            continue

        current_issue_id = int(issue['id'])
        if issue_id is not None and current_issue_id != issue_id:
            continue
        issue_entries_map.setdefault(current_issue_id, []).append(normalize_time_entry(entry))

    if issue_id is not None and not issue_entries_map:
        raise ValueError(f'За период {start_date_str} – {end_date_str} не найдено трудозатрат по задаче #{issue_id}')

    issue_contexts = []
    issue_ids = sorted(issue_entries_map.keys())
    print(f'🧩 Собираем контекст по задачам: {len(issue_ids)} шт.')

    for current_issue_id in issue_ids:
        issue_data = fetch_issue_with_journals(current_issue_id)
        time_entries_in_period = issue_entries_map[current_issue_id]
        issue_contexts.append(build_issue_context(issue_data, time_entries_in_period))

    base_payload = {'period': {'from': start_date_str, 'to': end_date_str}}

    if len(issue_contexts) == 1:
        payload = compact_dict({
            **base_payload,
            'issue': issue_contexts[0],
            'entries_without_issue': entries_without_issue if entries_without_issue else None,
        })
    else:
        payload = compact_dict({
            **base_payload,
            'issues_count': len(issue_contexts),
            'issues': issue_contexts,
            'entries_without_issue': entries_without_issue if entries_without_issue else None,
        })

    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    print(f'💾 Контекст задач сохранён: {output_filename}')
    return output_filename