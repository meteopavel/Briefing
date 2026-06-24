"""
Конфигурация приложения и загрузка значений из переменных окружения.
Модуль отвечает за:
- загрузку .env-файла;
- чтение и преобразование JSON-значений из переменных окружения;
- хранение путей к входным, шаблонным и выходным файлам;
- хранение справочников и констант, используемых в приложении.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def load_json_env(name: str, default: Any) -> Any:
    """
    Загружает значение переменной окружения как JSON.
    Если переменная не задана или пуста, возвращает default.
    Если значение не является корректным JSON, выбрасывает ValueError.
    """
    value = os.getenv(name)
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f'Некорректный JSON в переменной окружения {name}: {error}') from error


def load_int_key_dict_env(name: str, default: dict[Any, Any]) -> dict[int, Any]:
    """
    Загружает JSON-словарь из переменной окружения и приводит его ключи к int.
    """
    raw_data = load_json_env(name, default)
    return {int(key): value for key, value in raw_data.items()}


def load_set_dict_env(name: str, default: dict[Any, Any]) -> dict[Any, set[Any]]:
    """
    Загружает JSON-словарь из переменной окружения и приводит его значения к set.
    """
    raw_data = load_json_env(name, default)
    return {key: set(value) for key, value in raw_data.items()}


LOCAL_SECURE_DIR = '.local_secure'
LOCAL_RUNTIME_DIR = '.local_runtime'

ACTS_DATA_FILE = os.path.join(LOCAL_SECURE_DIR, 'salary_data.xlsx')

TEMPLATES_DIR = os.path.join(LOCAL_SECURE_DIR, 'templates')
ACT_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, 'template_act.docx')
REPORT_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, 'template_report.docx')

OUTPUT_DIR = os.path.join(LOCAL_RUNTIME_DIR, 'output')
TIMELOGS_DIR = os.path.join(LOCAL_RUNTIME_DIR, 'timelogs')

REDMINE_URL = os.getenv('REDMINE_URL', '').rstrip('/')
REDMINE_API_KEY = os.getenv('REDMINE_API_KEY')
REDMINE_API_KEY_ADMIN = os.getenv('REDMINE_API_KEY_ADMIN') or os.getenv('REDMINE_API_KEY')
REDMINE_USER_ID = os.getenv('REDMINE_USER_ID')

GITLAB_URL = os.getenv('GITLAB_URL', '').rstrip('/')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', '')
GITLAB_PROJECT_PATH = os.getenv('GITLAB_PROJECT_PATH', 'mg/mailganer')
GITLAB_AUTHOR_ID = int(os.getenv('GITLAB_AUTHOR_ID', '68'))

DOCUMENT_OWNER = os.getenv('DOCUMENT_OWNER', 'Contractor')

USER_MAP = load_int_key_dict_env('USER_MAP', {})
ISSUE_STATUS_MAP = load_int_key_dict_env('ISSUE_STATUS_MAP', {})
ISSUE_PRIORITY_MAP = load_int_key_dict_env('ISSUE_PRIORITY_MAP', {})
CUSTOM_FIELD_MAP = load_int_key_dict_env('CUSTOM_FIELD_MAP', {})
CUSTOM_FIELDS_HIDE_IF_NEGATIVE = load_set_dict_env('CUSTOM_FIELDS_HIDE_IF_NEGATIVE', {})
USER_REFERENCE_CUSTOM_FIELD_IDS = {16, 17, 18, 19}

MONTH_NAMES = {
    '01': 'января', '02': 'февраля', '03': 'марта', '04': 'апреля', '05': 'мая', '06': 'июня',
    '07': 'июля', '08': 'августа', '09': 'сентября', '10': 'октября', '11': 'ноября', '12': 'декабря'
}
REPORT_TABLE_COLUMN_WIDTHS_INCH = [0.4, 1.6, 2.9, 1.3]

