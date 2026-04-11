import os

from dotenv import load_dotenv

load_dotenv()

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