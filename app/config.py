import json
import os

from dotenv import load_dotenv

load_dotenv()


def load_json_env(name, default):
    value = os.getenv(name)
    if not value:
        return default

    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f'Некорректный JSON в переменной окружения {name}: {error}') from error


def load_int_key_dict_env(name, default):
    raw_data = load_json_env(name, default)
    return {int(key): value for key, value in raw_data.items()}


def load_set_dict_env(name, default):
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
REDMINE_USER_ID = os.getenv('REDMINE_USER_ID')

USER_MAP = load_int_key_dict_env('USER_MAP', {})
ISSUE_STATUS_MAP = load_int_key_dict_env('ISSUE_STATUS_MAP', {})
ISSUE_PRIORITY_MAP = load_int_key_dict_env('ISSUE_PRIORITY_MAP', {})
CUSTOM_FIELD_MAP = load_int_key_dict_env('CUSTOM_FIELD_MAP', {})
CUSTOM_FIELDS_HIDE_IF_NEGATIVE = load_set_dict_env('CUSTOM_FIELDS_HIDE_IF_NEGATIVE', {})
