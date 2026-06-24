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

import time

import requests

from app.config import REDMINE_API_KEY, REDMINE_USER_ID, REDMINE_URL


_spent_cache: dict = {}
_SPENT_CACHE_TTL = 300  # 5 минут


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

                'limit': 100,
                'sort': 'priority:desc,updated_on:desc',
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get('issues', [])

    @staticmethod
    def _fetch_and_cache() -> None:
        """Загружает все записи времени и сохраняет в кэш."""
        from datetime import date
        today_str = date.today().isoformat()
        by_issue: dict[int, dict] = {}
        by_day: dict[str, dict] = {}
        offset = 0
        limit = 100
        while True:
            response = requests.get(
                f'{REDMINE_URL}/time_entries.json',
                headers={'X-Redmine-API-Key': REDMINE_API_KEY},
                params={'user_id': REDMINE_USER_ID, 'limit': limit, 'offset': offset},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            for entry in data.get('time_entries', []):
                issue = entry.get('issue', {})
                iid = issue.get('id')
                hours = entry.get('hours', 0.0)
                spent_on = entry.get('spent_on', '')
                if iid:
                    rec = by_issue.setdefault(iid, {'hours': 0.0, 'today': False})
                    rec['hours'] += hours
                    if spent_on == today_str:
                        rec['today'] = True
                if spent_on:
                    day = by_day.setdefault(spent_on, {'total': 0.0, 'entries': []})
                    day['total'] += hours
                    if iid:
                        day['entries'].append({'issue_id': iid, 'hours': hours,
                                               'subject': issue.get('subject', '')})
            offset += limit
            if offset >= data.get('total_count', 0):
                break
        _spent_cache['by_issue'] = by_issue
        _spent_cache['by_day'] = by_day
        _spent_cache['ts'] = time.monotonic()

    @staticmethod
    def _ensure_cache() -> None:
        if not _spent_cache.get('by_issue') or                 time.monotonic() - _spent_cache.get('ts', 0) >= _SPENT_CACHE_TTL:
            RedmineClient._fetch_and_cache()

    @staticmethod
    def fetch_my_spent_hours() -> dict[int, dict]:
        """Возвращает {issue_id: {hours: float, today: bool}}."""
        try:
            RedmineClient._ensure_cache()
            return _spent_cache.get('by_issue', {})
        except Exception:
            return {}

    @staticmethod
    def fetch_daily_summary(days: int = 3) -> list[dict]:
        """Возвращает список {date, total, entries} за последние N дней (включая дни без записей)."""
        from datetime import date, timedelta
        try:
            RedmineClient._ensure_cache()
            by_day = _spent_cache.get('by_day', {})
        except Exception:
            by_day = {}
        today = date.today()
        result = []
        for i in range(days):
            d = today - timedelta(days=i)
            ds = d.isoformat()
            day_data = by_day.get(ds, {'total': 0.0, 'entries': []})
            result.append({'date': ds, 'total': day_data['total'], 'entries': day_data['entries']})
        return result
