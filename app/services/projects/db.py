"""
Подключение к MySQL для вкладки «Проекты».
Без ORM — обычный курсор, в стиле остальных сервисных модулей проекта.
"""

from contextlib import contextmanager

import pymysql
import pymysql.cursors

from app.config import MYSQL_DATABASE, MYSQL_HOST, MYSQL_PASSWORD, MYSQL_PORT, MYSQL_USER


@contextmanager
def get_connection():
    """
    Отдаёт открытое соединение с БД briefing (autocommit включён).
    Закрывает соединение при выходе из контекста в любом случае.
    """
    connection = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()
