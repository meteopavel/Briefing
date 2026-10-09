"""
Фоновый вотчер крит-багов mailganer (feat.30).

Раз в MAX_PING_POLL_SEC секунд опрашивает рабочий Redmine (задачи,
назначенные на владельца): задача, вошедшая в критический приоритет
(«Критичный баг»), пингуется личным сообщением через Max-бота — один пинг
на вход, повтор только после снятия приоритета и возврата. Состояние — в
MySQL (max_ping_state), переживает рестарты и деплои.

Скоуп «только mailganer» выполняется по построению: этот Redmine — трекер
работодателя (email-платформа Mailganer), личные проекты в нём не живут.
"""
from __future__ import annotations

import asyncio

from app.config import MAX_PING_POLL_SEC, MAX_USER_ID, REDMINE_CRITICAL_PRIORITY_IDS, REDMINE_URL
from app.services.maxbot import client as max_client
from app.services.projects.db import get_connection
from app.services.redmine.client import RedmineClient

# Subject в Redmine бывает длинным; режем, чтобы пинг читался на телефоне
_SUBJECT_MAX_LEN = 300


def enabled() -> bool:
    """Вотчер можно запускать: есть токен бота и URL Redmine."""
    return max_client.has_token() and bool(REDMINE_URL)


def _load_state() -> dict[int, bool]:
    """{issue_id: was_critical} по таблице max_ping_state."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT issue_id, was_critical FROM max_ping_state')
            return {row['issue_id']: bool(row['was_critical']) for row in cursor.fetchall()}


def _mark_entered(issue_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO max_ping_state (issue_id, was_critical, pinged_at) '
                'VALUES (%s, 1, NOW()) '
                'ON DUPLICATE KEY UPDATE was_critical = 1, pinged_at = NOW()',
                (issue_id,),
            )


def _mark_left(issue_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE max_ping_state SET was_critical = 0 WHERE issue_id = %s',
                (issue_id,),
            )


def _ping(issue: dict) -> None:
    issue_id = issue['id']
    subject = issue.get('subject', '').strip()
    if len(subject) > _SUBJECT_MAX_LEN:
        subject = subject[:_SUBJECT_MAX_LEN - 1] + '…'
    text = f'🚨 Критичный баг mailganer #{issue_id}\n{subject}\n{REDMINE_URL}/issues/{issue_id}'
    max_client.send_message(text, MAX_USER_ID)
    print(f'✅ maxbot: отправлен пинг по крит-багу #{issue_id}')


def _poll_once() -> None:
    critical = {
        int(issue['id']): issue
        for issue in RedmineClient.fetch_my_issues()
        if int((issue.get('priority') or {}).get('id', 0)) in REDMINE_CRITICAL_PRIORITY_IDS
    }
    state = _load_state()

    # Первый прогон (пустое состояние): засеиваем текущие крит-задачи без
    # пингов — иначе каждый деплой на свежую БД оборачивался бы залпом
    # сообщений по давно открытым багам.
    if not state:
        for issue_id in critical:
            _mark_entered(issue_id)
        print(f'ℹ️ maxbot: первый прогон — {len(critical)} крит-задач засеяно без пингов')
        return

    for issue_id, issue in critical.items():
        if not state.get(issue_id):
            _ping(issue)
            _mark_entered(issue_id)
    for issue_id, was_critical in state.items():
        if was_critical and issue_id not in critical:
            _mark_left(issue_id)


async def run() -> None:
    """Цикл поллинга; запускается lifespan'ом веб-приложения (см. web.py).

    Ошибки отдельных итераций (Redmine недоступен, БД, MAX API) гасятся —
    вотчер живёт вместе с приложением и не должен ронять его.
    """
    while True:
        try:
            await asyncio.to_thread(_poll_once)
        except Exception as exc:
            print(f'⚠️ maxbot watcher: ошибка итерации поллинга: {exc}')
        await asyncio.sleep(MAX_PING_POLL_SEC)
