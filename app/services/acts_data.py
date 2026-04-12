"""
Загрузка и подготовка данных по актам из Excel-файла.
Модуль отвечает за чтение таблицы актов и преобразование относительных
имён файлов Redmine в полные пути внутри каталога таймлогов.
"""

import os

import pandas as pd

from app.config import ACTS_DATA_FILE, TIMELOGS_DIR


def load_acts_data() -> pd.DataFrame:
    """
    Загружает данные по актам из Excel-файла.
    Возвращает DataFrame с приведёнными типами колонок и полными путями
    к CSV-файлам Redmine в колонке `redmine_file`.
    """
    dataframe = pd.read_excel(
        ACTS_DATA_FILE,
        dtype={
            'year': int,
            'month': str,
            'redmine_file': str,
            'total_amount': int,
            'act_num': int,
            'start_date': str,
            'end_date': str,
        },
    )
    dataframe['redmine_file'] = dataframe['redmine_file'].map(
        lambda value: os.path.join(TIMELOGS_DIR, value)
    )
    return dataframe
