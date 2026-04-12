"""
Сборка нормализованного контекста задач Redmine для последующего экспорта.
Модуль отвечает за:
- получение brief-информации по связанным задачам;
- извлечение связанных issue id из relations и journals;
- сборку контекста одной задачи;
- формирование итогового payload по периоду или по одной задаче.
"""
from __future__ import annotations

from typing import Any

from app.services.redmine.client import RedmineClient
from app.services.redmine.normalizers import (
    resolve_priority_name, remove_empty_values, normalize_text, normalize_journals,
    normalize_custom_fields, normalize_time_entry
)


def safe_fetch_issue_brief(issue_id: int) -> dict[str, Any]:
    """
    Безопасно загружает краткую информацию по задаче.
    Если задача недоступна или запрос завершается ошибкой, возвращает
    минимальный объект только с идентификатором задачи.
    """
    try:
        issue_data = RedmineClient.fetch_issue(issue_id)
    except KeyError:
        return {'id': issue_id}
    priority = issue_data.get('priority') or {}
    priority_name = priority.get('name')
    if not priority_name and priority.get('id') is not None:
        priority_name = resolve_priority_name(priority.get('id'))
    return remove_empty_values({
        'id': issue_data.get('id', issue_id),
        'subject': normalize_text(issue_data.get('subject')),
        'priority': priority_name,
    })


def extract_related_issue_ids(issue_data: dict[str, Any]) -> list[int]:
    """
    Извлекает идентификаторы связанных задач из relations и journals задачи.
    В результат не включается id текущей задачи. Возвращает отсортированный
    список уникальных идентификаторов.
    """
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


def build_related_issues(issue_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Строит список кратких описаний связанных задач для переданной задачи.
    """
    related_ids = extract_related_issue_ids(issue_data)
    return [safe_fetch_issue_brief(related_issue_id) for related_issue_id in related_ids]


def build_issue_context(
    issue_data: dict[str, Any],
    time_entries_in_period: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Собирает нормализованный контекст одной задачи Redmine.
    В итоговый контекст включаются основные поля задачи, связанные задачи,
    custom fields, journals и трудозатраты за выбранный период.
    """
    spent_hours_in_period = round(sum(float(entry.get('hours', 0)) for entry in time_entries_in_period), 2,)
    return remove_empty_values({
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


def build_issue_context_payload(
    start_date_str: str,
    end_date_str: str,
    issue_id: int | None = None,
) -> dict[str, Any]:
    """
    Формирует итоговый payload контекста задач за период.
    Загружает time entries за указанный диапазон дат, группирует их по задачам,
    подгружает расширенный контекст задач с journals и возвращает итоговую
    структуру либо для одной задачи, либо для набора задач.
    """
    entries = RedmineClient.fetch_time_entries(start_date_str, end_date_str)
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
        normalized_entry = normalize_time_entry(entry)
        if normalized_entry:
            issue_entries_map.setdefault(current_issue_id, []).append(normalized_entry)
    if issue_id is not None and not issue_entries_map:
        raise ValueError(f'За период {start_date_str} – {end_date_str} не найдено трудозатрат по задаче #{issue_id}')
    issue_contexts = []
    issue_ids = sorted(issue_entries_map.keys())
    print(f'🧩 Собираем контекст по задачам: {len(issue_ids)} шт.')
    for current_issue_id in issue_ids:
        issue_data = RedmineClient.fetch_issue_with_journals(current_issue_id)
        time_entries_in_period = issue_entries_map[current_issue_id]
        issue_contexts.append(build_issue_context(issue_data, time_entries_in_period))
    base_payload = {'period': {'from': start_date_str, 'to': end_date_str}}
    if len(issue_contexts) == 1:
        return remove_empty_values({
            **base_payload,
            'issue': issue_contexts[0],
            'entries_without_issue': entries_without_issue if entries_without_issue else None,
        })
    return remove_empty_values({
        **base_payload,
        'issues_count': len(issue_contexts),
        'issues': issue_contexts,
        'entries_without_issue': entries_without_issue if entries_without_issue else None,
    })
