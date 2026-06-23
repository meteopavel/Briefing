"""FastAPI web application: маршруты Briefing."""

from pathlib import Path

import re

import requests as req_lib
import textile
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import REDMINE_API_KEY, REDMINE_URL
from app.services.redmine.client import RedmineClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / 'web_static'
TEMPLATES_DIR = PROJECT_ROOT / 'templates'

app = FastAPI(title='Briefing')

app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

templates = Jinja2Templates(directory=TEMPLATES_DIR)


_SPAN_RE = re.compile(r'%\{([^}]+)\}([^%]*)%')
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._+%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


def _fix_spans(html: str) -> str:
    return _SPAN_RE.sub(lambda m: f'<span style="{m.group(1)}">{m.group(2)}</span>', html)


def _protect_emails(text: str) -> str:
    """Оборачивает email-адреса в <notextile>, чтобы @ не интерпретировался как код."""
    return _EMAIL_RE.sub(lambda m: f'<notextile>{m.group(0)}</notextile>', text)


def _render(text: str | None) -> str:
    if not text:
        return ''
    try:
        html = textile.textile(_protect_emails(text))
    except Exception:
        html = text
    return _fix_spans(html)


@app.get('/')
def index(request: Request):
    try:
        issues = RedmineClient.fetch_my_issues()
        for issue in issues:
            issue['_desc_html'] = _render(issue.get('description'))
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
        journals = []
        for j in issue.get('journals', []):
            notes = j.get('notes', '').strip()
            attachments = [
                {'id': d['name'], 'filename': d['new_value']}
                for d in j.get('details', [])
                if d.get('property') == 'attachment' and d.get('new_value')
            ]
            if notes or attachments:
                if notes:
                    j['notes_html'] = _render(notes)
                j['attachments'] = attachments
                journals.append(j)
        return {'journals': journals}
    except Exception as e:
        return {'error': str(e), 'journals': []}


@app.get('/api/attachment/thumbnail/{attachment_id}')
def attachment_thumbnail(attachment_id: int):
    try:
        r = req_lib.get(
            f'{REDMINE_URL}/attachments/thumbnail/{attachment_id}',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            timeout=10,
        )
        if r.status_code == 200 and r.content:
            ct = r.headers.get('content-type', 'image/png')
            return Response(content=r.content, media_type=ct)
    except Exception:
        pass
    return Response(status_code=404)


@app.get('/api/avatar/{user_id}')
def avatar(user_id: int):
    try:
        r = req_lib.get(
            f'{REDMINE_URL}/users/{user_id}/avatar',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            timeout=5,
            allow_redirects=True,
        )
        if r.status_code == 200:
            ct = r.headers.get('content-type', 'image/png')
            return Response(content=r.content, media_type=ct)
    except Exception:
        pass
    return Response(status_code=404)


@app.get('/health')
def health():
    return {'status': 'ok'}
