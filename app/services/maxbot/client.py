"""Минимальный клиент MAX Bot API для Briefing (только stdlib).

Порт клиента из Gym_helper (core/max_client.py), тот же бот, что в
django_edu_multisite и Gym_helper — нового бота feat.30 не создаёт.
Отправка личных сообщений (user_id); сертификат platform-api2.max.ru
выпущен НУЦ Минцифры — корня нет в публичных trust store, поэтому
догружаем certs/russian_trusted_ca.pem поверх доступного набора CA.
"""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

MAX_API_BASE_URL = 'https://platform-api2.max.ru'

_CERTS_DIR = Path(__file__).resolve().parent / 'certs'
RUSSIAN_TRUSTED_CA = _CERTS_DIR / 'russian_trusted_ca.pem'

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.load_verify_locations(cafile=str(RUSSIAN_TRUSTED_CA))

# Где искать MAX_BOT_TOKEN, если его нет в окружении: .env Briefing (его
# подгружает app.config при работе приложения, сюда — для автономного CLI),
# затем .env соседнего проекта, где бот живёт (локально на маке).
_ROOT = Path(__file__).resolve().parents[3]
_TOKEN_CANDIDATES = [
    _ROOT / '.env',
    _ROOT.parent / 'Django_EDU_Multisite' / '.env',
]


def _token_from_file(path: Path) -> str:
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line.startswith('MAX_BOT_TOKEN='):
            return line.split('=', 1)[1].strip().strip('"\'')
    return ''


def has_token() -> bool:
    """Есть ли токен — без исключений (решает, запускать ли вотчер)."""
    if os.environ.get('MAX_BOT_TOKEN'):
        return True
    return any(p.exists() and _token_from_file(p) for p in _TOKEN_CANDIDATES)


def load_token() -> str:
    token = os.environ.get('MAX_BOT_TOKEN', '')
    if token:
        return token
    for candidate in _TOKEN_CANDIDATES:
        if candidate.exists():
            token = _token_from_file(candidate)
            if token:
                return token
    raise RuntimeError('MAX_BOT_TOKEN не найден: нет в окружении и ни в одном .env')


def send_message(text: str, user_id: str) -> None:
    """Отправляет личное сообщение пользователю MAX от имени бота."""
    url = f'{MAX_API_BASE_URL}/messages?user_id={user_id}'
    request = urllib.request.Request(
        url,
        data=json.dumps({'text': text}).encode('utf-8'),
        method='POST',
        headers={'Authorization': load_token(), 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=15, context=_SSL_CONTEXT) as response:
            if response.status >= 300:
                raise RuntimeError(f'MAX API вернул статус {response.status}')
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'MAX API вернул ошибку {exc.code}: {body}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Не удалось связаться с MAX API: {exc.reason}') from exc
