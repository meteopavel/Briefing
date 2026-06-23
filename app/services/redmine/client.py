"""
HTTP-клиент для получения данных из Redmine API.
Модуль содержит методы для загрузки:
- time entries за период;
- названий задач по списку id;
- полной задачи;
- полной задачи вместе с journals.
"""
from __future__ import annotations

from typing import Any

import requests

from app.config import REDMINE_API_KEY, REDMINE_USER_ID, REDMINE_URL


class RedmineClient:
    """
    Клиент для чтения данных из Redmine через REST API.
    """

    @staticmethod
    def fetch_time_entries(start_date_str: str, end_date_str: str) -> list[dict[str, Any]]:
        """
        Загружает time entries текущего пользователя Redmine за указанный период.
        """
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


    @staticmethod
    def fetch_issue_subjects(issue_ids: set[int] | list[int]) -> dict[int, str]:
        """
        Загружает названия задач по набору или списку идентификаторов.
        """
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


    @staticmethod
    def fetch_issue_with_journals(issue_id: int) -> dict[str, Any]:
        """
        Загружает полные данные задачи вместе с journals.
        """
        print(f'📄 Запрашиваем расширенный контекст задачи #{issue_id}...')
        response = requests.get(
            f'{REDMINE_URL}/issues/{issue_id}.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            params={'include': 'journals'},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()['issue']


    @staticmethod
    def fetch_issue(issue_id: int) -> dict[str, Any]:
        """
        Загружает полные данные одной задачи без journals.
        """
        response = requests.get(
            f'{REDMINE_URL}/issues/{issue_id}.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()['issue']

    @staticmethod
    def fetch_my_issues(status_id: str = 'open') -> list[dict[str, Any]]:
        """Загружает задачи, назначенные на текущего пользователя."""
        response = requests.get(
            f'{REDMINE_URL}/issues.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            params={
                'assigned_to_id': REDMINE_USER_ID,
                'status_id': status_id,
                'include': 'spent_time',
                'limit': 100,
                'sort': 'priority:desc,updated_on:desc',
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get('issues', [])
