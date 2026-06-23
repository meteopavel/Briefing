"""FastAPI web application: маршруты Briefing."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import REDMINE_URL
from app.services.redmine.client import RedmineClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / 'web_static'
TEMPLATES_DIR = PROJECT_ROOT / 'templates'

app = FastAPI(title='Briefing')

app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get('/')
def index(request: Request):
    try:
        issues = RedmineClient.fetch_my_issues()
        error = None
    except Exception as e:
        issues = []
        error = str(e)
    return templates.TemplateResponse(
        request=request,
        name='tasks.html',
        context={'title': 'Briefing', 'active_tab': 'tasks', 'issues': issues, 'error': error, 'redmine_url': REDMINE_URL},
    )


@app.get('/api/issues/{issue_id}/journals')
def issue_journals(issue_id: int):
    try:
        issue = RedmineClient.fetch_issue_with_journals(issue_id)
        journals = [
            j for j in issue.get('journals', [])
            if j.get('notes', '').strip()
        ]
        return {'journals': journals}
    except Exception as e:
        return {'error': str(e), 'journals': []}


@app.get('/health')
def health():
    return {'status': 'ok'}
