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
# Захватываем опциональные _ вокруг адреса — они ломают textile-курсив
_EMAIL_RE = re.compile(r'_?[a-zA-Z0-9._+%-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+_?')
# Настоящие HTML-теги, которые трогать нельзя
_REAL_TAGS = {
    'a', 'b', 'i', 'u', 's', 'p', 'br', 'hr', 'em', 'strong', 'code', 'pre',
    'span', 'div', 'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tfoot',
    'tr', 'th', 'td', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'img', 'blockquote', 'del', 'ins', 'sub', 'sup', 'tt',
}
_ANGLE_RE = re.compile(r'</?([a-zA-Z][a-zA-Z0-9_-]*)(?:\s[^>]*)?>|<([a-zA-Z][a-zA-Z0-9_-]*)>')


def _fix_spans(html: str) -> str:
    return _SPAN_RE.sub(lambda m: f'<span style="{m.group(1)}">{m.group(2)}</span>', html)


def _escape_template_vars(text: str) -> str:
    """Экранирует <placeholder> которые не являются HTML-тегами."""
    def _replace(m: re.Match) -> str:
        full = m.group(0)
        tag_name = (m.group(1) or m.group(2) or '').lower()
        if tag_name in _REAL_TAGS:
            return full
        return full.replace('<', '&lt;').replace('>', '&gt;')
    return _ANGLE_RE.sub(_replace, text)


def _render(text: str | None) -> str:
    if not text:
        return ''
    # Сохраняем email-токены (включая прилегающие _) → placeholders
    tokens: list[str] = []

    def _store(m: re.Match) -> str:
        tokens.append(m.group(0))
        return f'\x01TOK{len(tokens) - 1}\x01'

    protected = _escape_template_vars(_EMAIL_RE.sub(_store, text))
    try:
        html = textile.textile(protected)
    except Exception:
        html = protected
    for i, tok in enumerate(tokens):
        html = html.replace(f'\x01TOK{i}\x01', tok)
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
