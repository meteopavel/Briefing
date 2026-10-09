"""Ручной пинг через Max-бота: python -m app.services.maxbot "текст".

Для крит-багов mailganer, обнаруженных вне Redmine (например, в сессии
авто-ревью MR), и для проверки канала.
"""
import sys

from app.config import MAX_USER_ID
from app.services.maxbot.client import send_message


def main() -> None:
    text = ' '.join(sys.argv[1:]).strip()
    if not text:
        raise SystemExit('Использование: python -m app.services.maxbot "текст сообщения"')
    send_message(text, MAX_USER_ID)
    print('✅ Отправлено')


if __name__ == '__main__':
    main()
