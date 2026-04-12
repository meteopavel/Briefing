"""
Утилиты для записи файлов.
Модуль содержит функции для:
- записи данных в JSON-файл;
- записи текста в обычный текстовый файл.
"""

import json
import os

from typing import Any


def write_json_file(filename: str, payload: Any) -> None:
    """
    Записывает переданные данные в JSON-файл.
    Если директория для файла не существует, она будет создана.
    JSON сохраняется в UTF-8 с отступами и без ASCII-экранирования.
    """
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def write_text_file(filename: str, content: str) -> None:
    """
    Записывает текст в файл.
    Если директория для файла не существует, она будет создана.
    Файл сохраняется в кодировке UTF-8.
    """
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)