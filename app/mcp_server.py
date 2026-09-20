"""
MCP-сервер Briefing: тулы над тудушками проектов (та же БД и тот же
`repository.py`, что у веб-вкладки «Проекты»). Подключается по HTTP —
из Claude Code и из zcode — вместо чтения/записи docs/TODO.md.
"""

from mcp.server.fastmcp import FastMCP

from app.services.projects import repository as projects_repo

mcp = FastMCP('briefing')
# FastAPI уже режет префикс при app.mount('/mcp', ...) — без этого получилось
# бы двойное /mcp/mcp, потому что streamable_http_app() по умолчанию сам
# ожидает путь /mcp внутри себя.
mcp.settings.streamable_http_path = '/'
# Stateless: сервер не ведёт сессий в памяти. Каждый tools/call изолирован —
# без session-id, без state между вызовами. Тулы здесь чистые БД-операции,
# межзапросное состояние не нужно, а так session store жил в ОП процесса и
# протухал при каждом `systemctl restart` во время деплоя (No valid session ID).
mcp.settings.stateless_http = True


def _project_or_raise(project_slug: str) -> dict:
    project = projects_repo.get_project_by_slug(project_slug)
    if project is None:
        raise ValueError(f'Проект «{project_slug}» не найден')
    return project


def _serialize_todo(todo: dict) -> dict:
    out = dict(todo)
    # Однострочный контракт MCP: title = ru-версия, иначе en; title_alt —
    # вторая версия (None, если её ещё не заполнили). Аналогично для подпунктов.
    out['title'] = todo.get('title_ru') or todo.get('title_en')
    out['title_alt'] = todo.get('title_en') if todo.get('title_ru') else todo.get('title_ru')
    for sub in out.get('subitems', []):
        sub['text'] = sub.get('text_ru') or sub.get('text_en')
        sub['text_alt'] = sub.get('text_en') if sub.get('text_ru') else sub.get('text_ru')
    out['created_at'] = todo['created_at'].isoformat() if todo.get('created_at') else None
    out['updated_at'] = todo['updated_at'].isoformat() if todo.get('updated_at') else None
    return out


def _split_subitems(subitems: list[dict]) -> list[dict]:
    """Подпункты с однострочным text → пары text_ru/text_en по языку текста."""
    out = []
    for sub in subitems or []:
        text_ru, text_en = projects_repo.split_by_lang(sub.get('text') or '')
        out.append({'kind': sub['kind'], 'text_ru': text_ru, 'text_en': text_en})
    return out


@mcp.tool()
def list_projects() -> list[dict]:
    """Список проектов, заведённых в Briefing (slug, title, contour, is_hub); хаб первым."""
    return projects_repo.list_projects()


@mcp.tool()
def list_todos(project_slug: str, section: str | None = None, include_closed: bool = True) -> list[dict]:
    """
    Задачи проекта с подпунктами (без группировки/сортировки).

    section (опционально): bug|feat|ref|ques — только эта секция.
    include_closed=False: отбросить done/wontdo (для «что в тудушке?»).
    Без параметров — все задачи проекта. Для больших проектов фильтруй:
    полный список растёт с историей и может не влезть в лимит ответа тула.
    """
    if section is not None and section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    project = _project_or_raise(project_slug)
    todos = projects_repo.get_todos(project['id'])
    if section is not None:
        todos = [t for t in todos if t['section'] == section]
    if not include_closed:
        todos = [t for t in todos if t['status'] not in ('done', 'wontdo')]
    return [_serialize_todo(t) for t in todos]


@mcp.tool()
def create_todo(project_slug: str, section: str, priority: str, title: str, subitems: list[dict] | None = None) -> int:
    """
    Создаёт задачу со следующим свободным номером в указанной секции.
    section: bug|feat|ref|ques. priority: critical|high|medium|low.
    subitems (опционально): [{"kind": "requirement"|"context", "text": "..."}].
    Текст пишется в колонку своего языка (кириллица → ru, иначе → en);
    вторую версию можно заполнить позже через веб (форма правки, поля RU/EN).
    Возвращает id созданной задачи.
    """
    project = _project_or_raise(project_slug)
    if section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    if priority not in projects_repo.PRIORITIES:
        raise ValueError(f'Некорректный приоритет: {priority} (ожидается одна из {projects_repo.PRIORITIES})')
    if not title.strip():
        raise ValueError('Текст задачи не может быть пустым')
    title_ru, title_en = projects_repo.split_by_lang(title)
    return projects_repo.create_todo(project['id'], section, priority, title_ru, title_en, _split_subitems(subitems))


@mcp.tool()
def update_todo_status(todo_id: int, status: str, closed_note: str | None = None) -> None:
    """
    Меняет статус задачи. status: open|in_progress|done|wontdo.
    При переходе в done/wontdo closed_note обязателен (что сделано / что решили).
    """
    if status not in projects_repo.STATUSES:
        raise ValueError(f'Некорректный статус: {status} (ожидается одна из {projects_repo.STATUSES})')
    if status in ('done', 'wontdo') and not (closed_note or '').strip():
        raise ValueError('Для закрытия задачи нужна заметка — что сделано / что решили')
    projects_repo.update_status(todo_id, status, closed_note)


@mcp.tool()
def update_todo_priority(todo_id: int, priority: str):
    """Меняет приоритет задачи. priority: critical|high|medium|low."""
    if priority not in projects_repo.PRIORITIES:
        raise ValueError(f'Некорректный приоритет: {priority} (ожидается одна из {projects_repo.PRIORITIES})')
    projects_repo.update_priority(todo_id, priority)


@mcp.tool()
def set_todo_placement_approved(todo_id: int, approved: bool) -> None:
    """
    Ставит/снимает флаг «размещение (секция + приоритет) утверждено».
    Агент выставляет approved=True после ревью размещения (когда согласовал
    секцию и приоритет задачи); при ручном изменении секции/приоритета через
    веб флаг снимается автоматически на бэке, а через MCP — нет (агент сам
    управляет им этим тулом).
    """
    if not isinstance(approved, bool):
        raise ValueError(f'approved должен быть bool, получен {type(approved).__name__}')
    projects_repo.update_placement_approved(todo_id, approved)


@mcp.tool()
def add_todo_subitem(todo_id: int, kind: str, text: str) -> None:
    """Добавляет подпункт к задаче. kind: requirement|context."""
    if kind not in ('requirement', 'context'):
        raise ValueError(f'Некорректный тип подпункта: {kind} (ожидается requirement|context)')
    if not text.strip():
        raise ValueError('Текст подпункта не может быть пустым')
    text_ru, text_en = projects_repo.split_by_lang(text)
    projects_repo.add_subitem(todo_id, kind, text_ru, text_en)


@mcp.tool()
def edit_todo(
    todo_id: int,
    title: str,
    section: str,
    subitems: list[dict] | None = None,
) -> None:
    """
    Меняет заголовок задачи и (опционально) секцию. section: bug|feat|ref|ques.
    При смене секции номер перевыпускается (bug.3 → feat.5), т.к. номер привязан
    к секции. Статус и приоритет сохраняются.

    Однострочный title перезаписывает только колонку своего языка (кириллица →
    ru, иначе → en); вторая языковая версия не трогается.

    subitems (опционально): полная замена подпунктов списком
    [{"kind": "requirement"|"context", "text": "..."}] в указанном порядке.
    Каждый text пишется в колонку своего языка. Пустой список [] — удалить все
    подпункты. None (по умолчанию) — не трогать.
    """
    if section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    if not title.strip():
        raise ValueError('Текст задачи не может быть пустым')
    if subitems is not None:
        for sub in subitems:
            if sub.get('kind') not in ('requirement', 'context'):
                raise ValueError(f'Некорректный тип подпункта: {sub.get("kind")} (ожидается requirement|context)')
            if not (sub.get('text') or '').strip():
                raise ValueError('Текст подпункта не может быть пустым')
    current = projects_repo.get_todo(todo_id)
    if current is None:
        raise ValueError(f'Задача {todo_id} не найдена')
    title_ru, title_en = projects_repo.split_by_lang(title)
    # склейка: однострочный title обновляет только свою колонку,
    # вторая языковая версия сохраняется
    projects_repo.edit_todo(
        todo_id,
        title_ru or current['title_ru'],
        title_en or current['title_en'],
        section,
        _split_subitems(subitems),
    )


@mcp.tool()
def delete_todo(todo_id: int) -> None:
    """Удаляет задачу вместе с подпунктами (они снимаются каскадом)."""
    projects_repo.delete_todo(todo_id)


def create_asgi_app():
    return mcp.streamable_http_app()
