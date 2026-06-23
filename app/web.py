"""FastAPI web application: маршруты Briefing."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / 'web_static'
TEMPLATES_DIR = PROJECT_ROOT / 'templates'

app = FastAPI(title='Briefing')

app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')

templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get('/')
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'title': 'Briefing', 'active_tab': 'tasks'},
    )


@app.get('/health')
def health():
    return {'status': 'ok'}
