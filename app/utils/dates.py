"""
Утилиты для работы с датами и выбора записей по целевому месяцу.
Модуль содержит функции для:
- валидации дат в формате ДД.ММ.ГГГГ;
- форматирования дат для документов;
- преобразования даты в формат ГГГГ-ММ-ДД;
- выбора строки данных за предыдущий месяц;
- определения диапазона дат по строке трудозатрат.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from app.config import MONTH_NAMES


def is_valid_dd_mm_yyyy(value: Any) -> bool:
    """
    Проверяет, что значение имеет формат ДД.ММ.ГГГГ.
    Проверка включает:
    - строковый тип;
    - наличие трёх компонентов, разделённых точками;
    - числовой состав компонентов;
    - длину компонентов;
    - допустимые диапазоны дня и месяца.
    Функция не проверяет корректность календарной даты полностью,
    например 31.02.2024 будет считаться валидной.
    """
    if not isinstance(value, str):
        return False
    parts = value.split('.')
    if len(parts) != 3:
        return False
    day, month, year = parts
    return (
        day.isdigit() and month.isdigit() and year.isdigit()
        and len(day) == 2 and len(month) == 2 and len(year) == 4
        and 1 <= int(day) <= 31 and 1 <= int(month) <= 12
    )


def format_date(date_str: str, short: bool = False) -> str:
    """
    Форматирует дату из вида ДД.ММ.ГГГГ в текстовый формат для документов.
    Примеры:
    - `01.02.2025` -> `«01» февраля 2025 года`
    - `01.02.2025`, short=True -> `«01» февраля 2025 г.`
    """
    parts = date_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Неверный формат даты: '{date_str}'. Ожидается ДД.ММ.ГГГГ")
    day, month_num, year = parts
    if not (day.isdigit() and month_num.isdigit() and year.isdigit()):
        raise ValueError(f"Дата содержит нечисловые компоненты: '{date_str}'")
    if len(day) != 2 or len(month_num) != 2 or len(year) != 4:
        raise ValueError(f"Неверная длина компонентов даты: '{date_str}'. Требуется ДД.ММ.ГГГГ")
    if month_num not in MONTH_NAMES:
        raise ValueError(f"Неверный номер месяца: '{month_num}' в дате '{date_str}'")
    suffix = 'г.' if short else 'года'
    return f'«{day}» {MONTH_NAMES[month_num]} {year} {suffix}'


def dd_mm_yyyy_to_yyyy_mm_dd(date_str: str) -> str:
    """
    Преобразует дату из формата ДД.ММ.ГГГГ в формат ГГГГ-ММ-ДД.
    """
    day, month, year = date_str.split('.')
    return f'{year}-{month}-{day}'


def get_target_month_row(acts_df: pd.DataFrame, acts_data_file: str) -> pd.Series:
    """
    Возвращает единственную строку данных за предыдущий календарный месяц.
    Если текущий месяц январь, выбирается декабрь предыдущего года.
    Функция печатает диагностическую информацию о текущей дате и целевом периоде.
    Выбрасывает ValueError, если запись не найдена или найдено несколько записей.
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    if current_month == 1:
        target_month = 12
        target_year = current_year - 1
    else:
        target_month = current_month - 1
        target_year = current_year
    print(f"📅 Текущая дата: {now.strftime('%d.%m.%Y')}")
    print(f'🎯 Генерация документов за {target_year} год, месяц №{target_month}')
    mask = (acts_df['year'] == target_year) & (acts_df['month_num'] == target_month)
    matching_rows = acts_df[mask]
    if matching_rows.empty:
        raise ValueError(f'Не найдена запись за {target_year}-{target_month:02d} в {acts_data_file}')
    if len(matching_rows) > 1:
        raise ValueError(f'Найдено несколько записей за {target_year}-{target_month:02d}')
    return matching_rows.iloc[0]


def get_date_range(row_data: pd.Series, date_columns: pd.Index | list[str]) -> tuple[str, str]:
    """
    Определяет диапазон дат оказания услуги по строке трудозатрат.
    Находит первую и последнюю дату среди переданных колонок, в которых
    присутствуют непустые значения. Если таких значений нет, возвращает `('-', '-')`.
    Ожидается, что имена колонок дат находятся в формате ГГГГ-ММ-ДД.
    """
    non_empty_indices = row_data[date_columns].dropna().index
    if len(non_empty_indices) == 0:
        return '-', '-'
    start_date = non_empty_indices[0]
    end_date = non_empty_indices[-1]
    return (
        f'{start_date[8:10]}.{start_date[5:7]}.{start_date[0:4]}',
        f'{end_date[8:10]}.{end_date[5:7]}.{end_date[0:4]}',
    )
