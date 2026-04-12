"""
Вспомогательные функции для разбиения данных Chronicle на chunk'и
и построения путей к директориям экспорта.
"""

import os

from typing import TypeVar

T = TypeVar('T')


def split_into_chunks(items: list[T], chunk_size: int) -> list[list[T]]:
    """
    Разбивает список элементов на последовательные chunk'и фиксированного размера.
    Если размер chunk'а меньше или равен нулю, выбрасывает ValueError.
    """
    if chunk_size <= 0:
        raise ValueError('Размер чанка должен быть больше 0')
    return [items[index:index + chunk_size] for index in range(0, len(items), chunk_size)]


def get_chronicle_base_dir(output_root_dir: str, start_date_str: str, end_date_str: str) -> str:
    """
    Строит путь к базовой директории Chronicle-экспорта для заданного периода.
    """
    return os.path.join(output_root_dir, f'chronicle-{start_date_str}_{end_date_str}')