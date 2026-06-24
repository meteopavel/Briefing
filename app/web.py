"""FastAPI web application: маршруты Briefing."""

from pathlib import Path

import hashlib
import re
from datetime import date, timedelta

import requests as req_lib
import textile
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import REDMINE_API_KEY, REDMINE_API_KEY_ADMIN, REDMINE_URL
from app.services.gitlab.client import GitLabClient
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
_NOTEXTILE_RE = re.compile(r'<notextile>(.*?)</notextile>', re.DOTALL)
_QUOTE_BLOCK_RE = re.compile(r'((?:^> ?.*$\n?)+)', re.MULTILINE)


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
    tokens: list[str] = []

    def _store_raw(content: str) -> str:
        tokens.append(content)
        return f'\x01TOK{len(tokens) - 1}\x01'

    # 1. > quote blocks → <blockquote> (render inner via textile)
    def _make_blockquote(m: re.Match) -> str:
        lines = m.group(1).splitlines()
        inner = '\n'.join(ln[2:] if ln.startswith('> ') else ln[1:] if ln.startswith('>') else ln for ln in lines).strip()
        try:
            inner_html = textile.textile(inner)
        except Exception:
            inner_html = inner
        return _store_raw(f'<blockquote class="redmine-quote">{inner_html}</blockquote>')
    text = _QUOTE_BLOCK_RE.sub(_make_blockquote, text)
    # 2. <notextile>...</notextile> → защищаем содержимое, теги выбрасываем
    text = _NOTEXTILE_RE.sub(lambda m: _store_raw(m.group(1)), text)
    # 3. Email-адреса (включая прилегающие _) → токены
    protected = _escape_template_vars(_EMAIL_RE.sub(lambda m: _store_raw(m.group(0)), text))
    try:
        html = textile.textile(protected)
    except Exception:
        html = protected
    for i, tok in enumerate(tokens):
        html = html.replace(f'\x01TOK{i}\x01', tok)
    return _fix_spans(html)



_GROUP_DEFS = [
    ('в_работе',      'В работе',      lambda s: 'работ' in s),
    ('на_ревью',      'На ревью',       lambda s: 'ревью' in s or 'review' in s),
    ('заблокирована', 'Заблокирована',  lambda s: 'заблок' in s or 'block' in s),
]


def _calc_workdays(due_str: str | None) -> int | None:
    if not due_str:
        return None
    try:
        due = date.fromisoformat(due_str)
    except Exception:
        return None
    today = date.today()
    if due >= today:
        count, d = 0, today
        while d <= due:
            if d.weekday() < 5:
                count += 1
            d += timedelta(days=1)
        return count
    else:
        count, d = 0, due + timedelta(days=1)
        while d <= today:
            if d.weekday() < 5:
                count += 1
            d += timedelta(days=1)
        return -count


_MR_URL_RE = re.compile(
    r'(https?://\S+/merge_requests/(\d+))\s*[-–]?\s*(stage|master)?',
    re.IGNORECASE,
)


def _parse_mrs(custom_fields: list) -> list[dict]:
    field_40 = next((f for f in custom_fields if f.get('id') == 40), None)
    if not field_40 or not field_40.get('value'):
        return []
    mrs, seen = [], set()
    for m in _MR_URL_RE.finditer(field_40['value']):
        url, mr_iid, mr_type = m.group(1), int(m.group(2)), (m.group(3) or '').lower()
        if mr_iid not in seen:
            seen.add(mr_iid)
            mrs.append({'url': url, 'mr_iid': mr_iid, 'mr_type': mr_type})
    return mrs


def _enrich(issue: dict, spent_map: dict | None = None) -> dict:
    issue['_desc_html'] = issue.get('_desc_html', '')
    issue['_label']      = _detect_label(issue.get('subject', ''))
    issue['_workdays']   = _calc_workdays(issue.get('due_date'))
    issue['_mrs']        = _parse_mrs(issue.get('custom_fields', []))
    if spent_map is not None:
        rec = spent_map.get(issue.get('id'), {})
        issue['_spent_hours'] = rec.get('hours', 0.0)
        issue['_spent_today'] = rec.get('today', False)
    return issue


def _group_issues(issues: list) -> list:
    buckets = {key: [] for key, _, _ in _GROUP_DEFS}
    buckets['прочее'] = []
    for issue in issues:
        status = (issue.get('status') or {}).get('name', '').lower()
        placed = False
        for key, _, check in _GROUP_DEFS:
            if check(status):
                buckets[key].append(issue)
                placed = True
                break
        if not placed:
            buckets['прочее'].append(issue)
    result = []
    for key, title, _ in _GROUP_DEFS:
        if buckets[key]:
            result.append({'key': key, 'title': title, 'issues': buckets[key]})
    if buckets['прочее']:
        result.append({'key': 'прочее', 'title': 'Прочее', 'issues': buckets['прочее']})
    return result


_LABEL_Q_RE  = re.compile(r'\[Q', re.IGNORECASE)
_LABEL_AI_RE = re.compile(r'\[ai\]',    re.IGNORECASE)


def _detect_label(subject: str) -> str:
    if _LABEL_Q_RE.search(subject):
        return 'q'
    if _LABEL_AI_RE.search(subject):
        return 'ai'
    return ''


_PRIORITY_ORDER = {
    'критичный баг': 0,
    'недельный фокус': 1,
    'высокий': 2, 'high': 2,
    'нормальный': 3, 'normal': 3,
    'низкий': 4, 'low': 4,
}


def _issue_sort_key(issue: dict) -> tuple:
    label         = issue.get('_label', '')
    status_name   = (issue.get('status') or {}).get('name', '').lower()
    priority_name = (issue.get('priority') or {}).get('name', '').lower()
    due           = issue.get('due_date') or ''
    in_progress   = 'работ' in status_name
    on_review     = 'ревью' in status_name or 'review' in status_name
    prio          = _PRIORITY_ORDER.get(priority_name, 3)
    if label == 'q':
        group = 0 if due else 1
    elif in_progress and due:
        group = 2
    elif in_progress:
        group = 3
    elif on_review:
        group = 4
    else:
        group = 5
    return (group, prio, due if due else 'z')


@app.get('/')
def index(request: Request):
    try:
        issues = RedmineClient.fetch_my_issues()
        review_issues = RedmineClient.fetch_on_review_issues()
        daily_summary = RedmineClient.fetch_daily_summary(days=3)
        my_issue_ids = {i['id'] for i in issues}
        for issue in issues:
            issue['_desc_html'] = _render(issue.get('description'))
            _enrich(issue)
        for issue in review_issues:
            if issue['id'] not in my_issue_ids:
                issue['_desc_html'] = _render(issue.get('description'))
                _enrich(issue)
        issues.sort(key=_issue_sort_key)
        groups = _group_issues(issues)
        error = None
    except Exception as e:
        issues = []; groups = []; daily_summary = []; review_issues = []
        error = str(e)
    return templates.TemplateResponse(
        request=request,
        name='tasks.html',
        context={'title': 'Briefing', 'active_tab': 'tasks', 'issues': issues, 'groups': groups, 'review_issues': review_issues, 'error': error, 'redmine_url': REDMINE_URL, 'issues_count': len(issues), 'daily_summary': daily_summary},
    )


@app.get('/api/spent')
def api_spent():
    try:
        spent_map = RedmineClient.fetch_my_spent_hours()
        by_issue = {
            str(iid): {'hours': round(rec['hours'], 2), 'today': rec['today']}
            for iid, rec in spent_map.items()
            if rec['hours'] > 0
        }
        return {'by_issue': by_issue}
    except Exception as e:
        return {'error': str(e), 'by_issue': {}, 'daily': []}


@app.get('/api/mrs')
def api_mrs(issue_ids: str = ''):
    if not issue_ids:
        return {}
    ids = [int(x) for x in issue_ids.split(',') if x.strip().isdigit()]
    result = {}
    try:
        for issue_id in ids:
            mrs = GitLabClient.get_mrs_for_issue(issue_id)
            if mrs:
                result[str(issue_id)] = mrs
    except Exception:
        pass
    return result


@app.get('/issue/{issue_id}')
def issue_by_id(request: Request, issue_id: int):
    try:
        r = req_lib.get(
            f'{REDMINE_URL}/issues/{issue_id}.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            timeout=30,
        )
        r.raise_for_status()
        issue = r.json()['issue']
        issue['_desc_html'] = _render(issue.get('description'))
        _enrich(issue)
        issues = [issue]
        groups = None
        error = None
    except Exception as e:
        issues = []; groups = None
        error = str(e)
    return templates.TemplateResponse(
        request=request,
        name='tasks.html',
        context={'title': f'#{issue_id}', 'active_tab': 'tasks', 'issues': issues, 'groups': groups, 'error': error, 'redmine_url': REDMINE_URL, 'issues_count': None},
    )


@app.get('/api/issues/{issue_id}/journals')
def issue_journals(issue_id: int):
    try:
        r = req_lib.get(
            f'{REDMINE_URL}/issues/{issue_id}.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY_ADMIN},
            params={'include': 'journals'},
            timeout=60,
        )
        r.raise_for_status()
        issue = r.json()['issue']
        journals = []
        for note_idx, j in enumerate(issue.get('journals', []), start=1):
            notes = j.get('notes', '').strip()
            details = j.get('details', [])
            attachments = [
                {'id': d['name'], 'filename': d['new_value']}
                for d in details
                if d.get('property') == 'attachment' and d.get('new_value')
            ]
            attr_changes = _build_attr_changes(details)
            if notes or attachments or attr_changes:
                if notes:
                    j['notes_html'] = _render(notes)
                j['attachments'] = attachments
                j['attr_changes'] = attr_changes
                j['_note_index'] = note_idx
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


@app.get('/api/attachment/download/{attachment_id}')
def attachment_download(attachment_id: int, filename: str = ''):
    try:
        path = f'/attachments/download/{attachment_id}/{filename}' if filename else f'/attachments/download/{attachment_id}'
        r = req_lib.get(
            f'{REDMINE_URL}{path}',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            timeout=30,
            allow_redirects=True,
        )
        if r.status_code == 200 and r.content:
            ct = r.headers.get('content-type', 'image/png')
            return Response(content=r.content, media_type=ct)
    except Exception:
        pass
    return Response(status_code=404)


_avatar_cache: dict[int, bytes] = {}
_redmine_meta: dict = {}  # statuses, priorities, users cache

_ATTR_LABELS: dict[str, str] = {
    'status_id': 'Статус',
    'assigned_to_id': 'Назначена',
    'priority_id': 'Приоритет',
    'done_ratio': 'Готовность',
    'fixed_version_id': 'Версия',
    'tracker_id': 'Трекер',
    'subject': 'Тема',
    'description': 'Описание',
    'estimated_hours': 'Оценка (ч)',
    'start_date': 'Дата начала',
    'due_date': 'Дедлайн',
    'is_private': 'Приватная',
}


def _get_redmine_meta() -> dict:
    if _redmine_meta:
        return _redmine_meta
    try:
        statuses = {
            str(s['id']): s['name']
            for s in req_lib.get(
                f'{REDMINE_URL}/issue_statuses.json',
                headers={'X-Redmine-API-Key': REDMINE_API_KEY},
                timeout=5,
            ).json().get('issue_statuses', [])
        }
        priorities = {
            str(p['id']): p['name']
            for p in req_lib.get(
                f'{REDMINE_URL}/enumerations/issue_priorities.json',
                headers={'X-Redmine-API-Key': REDMINE_API_KEY},
                timeout=5,
            ).json().get('issue_priorities', [])
        }
        _redmine_meta.update({'statuses': statuses, 'priorities': priorities, 'users': {}})
    except Exception:
        pass
    return _redmine_meta


def _resolve_attr(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    meta = _get_redmine_meta()
    if name == 'status_id':
        return meta.get('statuses', {}).get(value, value)
    if name == 'priority_id':
        return meta.get('priorities', {}).get(value, value)
    if name in ('assigned_to_id',):
        users: dict = meta.get('users', {})
        if value in users:
            return users[value]
        try:
            u = req_lib.get(
                f'{REDMINE_URL}/users/{value}.json',
                headers={'X-Redmine-API-Key': REDMINE_API_KEY},
                timeout=5,
            ).json().get('user', {})
            name_str = f"{u.get('firstname', '')} {u.get('lastname', '')}".strip()
            users[value] = name_str
            return name_str
        except Exception:
            return value
    if name == 'done_ratio':
        return f'{value}%'
    return value


def _build_attr_changes(details: list[dict]) -> list[dict]:
    changes = []
    for d in details:
        if d.get('property') != 'attr':
            continue
        field = d.get('name', '')
        label = _ATTR_LABELS.get(field, field)
        old = _resolve_attr(field, d.get('old_value'))
        new = _resolve_attr(field, d.get('new_value'))
        changes.append({'label': label, 'old': old, 'new': new})
    return changes


@app.get('/api/avatar/{user_id}')
def avatar(user_id: int):
    if user_id in _avatar_cache:
        return Response(content=_avatar_cache[user_id], media_type='image/jpeg')
    try:
        u = req_lib.get(
            f'{REDMINE_URL}/users/{user_id}.json',
            headers={'X-Redmine-API-Key': REDMINE_API_KEY},
            timeout=5,
        ).json().get('user', {})
        email = (u.get('mail') or u.get('login') or '').strip().lower()
        if not email:
            return Response(status_code=404)
        email_hash = hashlib.md5(email.encode()).hexdigest()
        gravatar_url = f'https://www.gravatar.com/avatar/{email_hash}?size=48&rating=PG&default=monsterid'
        r = req_lib.get(gravatar_url, timeout=5)
        if r.status_code == 200:
            _avatar_cache[user_id] = r.content
            return Response(content=r.content, media_type=r.headers.get('content-type', 'image/jpeg'))
    except Exception:
        pass
    return Response(status_code=404)


@app.get('/health')
def health():
    return {'status': 'ok'}
