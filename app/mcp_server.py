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
    return {
        **todo,
        'created_at': todo['created_at'].isoformat() if todo.get('created_at') else None,
        'updated_at': todo['updated_at'].isoformat() if todo.get('updated_at') else None,
    }


@mcp.tool()
def list_projects() -> list[dict]:
    """Список проектов, заведённых в Briefing (slug, title, contour)."""
    return projects_repo.list_projects()


@mcp.tool()
def list_todos(project_slug: str) -> list[dict]:
    """Все задачи проекта с подпунктами (без группировки/сортировки)."""
    project = _project_or_raise(project_slug)
    return [_serialize_todo(t) for t in projects_repo.get_todos(project['id'])]


@mcp.tool()
def create_todo(project_slug: str, section: str, priority: str, title: str, subitems: list[dict] | None = None) -> int:
    """
    Создаёт задачу со следующим свободным номером в указанной секции.
    section: bug|feat|ref|ques. priority: high|medium|low.
    subitems (опционально): [{"kind": "requirement"|"context", "text": "..."}].
    Возвращает id созданной задачи.
    """
    project = _project_or_raise(project_slug)
    if section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    if priority not in projects_repo.PRIORITIES:
        raise ValueError(f'Некорректный приоритет: {priority} (ожидается одна из {projects_repo.PRIORITIES})')
    if not title.strip():
        raise ValueError('Текст задачи не может быть пустым')
    return projects_repo.create_todo(project['id'], section, priority, title, subitems or [])


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
def update_todo_priority(todo_id: int, priority: str) -> None:
    """Меняет приоритет задачи. priority: high|medium|low."""
    if priority not in projects_repo.PRIORITIES:
        raise ValueError(f'Некорректный приоритет: {priority} (ожидается одна из {projects_repo.PRIORITIES})')
    projects_repo.update_priority(todo_id, priority)


@mcp.tool()
def add_todo_subitem(todo_id: int, kind: str, text: str) -> None:
    """Добавляет подпункт к задаче. kind: requirement|context."""
    if kind not in ('requirement', 'context'):
        raise ValueError(f'Некорректный тип подпункта: {kind} (ожидается requirement|context)')
    if not text.strip():
        raise ValueError('Текст подпункта не может быть пустым')
    projects_repo.add_subitem(todo_id, kind, text)


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

    subitems (опционально): полная замена подпунктов списком
    [{"kind": "requirement"|"context", "text": "..."}] в указанном порядке.
    Пустой список [] — удалить все подпункты. None (по умолчанию) — не трогать.
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
        projects_repo.replace_subitems(todo_id, subitems)
    projects_repo.update_todo_meta(todo_id, title, section)


@mcp.tool()
def delete_todo(todo_id: int) -> None:
    """Удаляет задачу вместе с подпунктами (они снимаются каскадом)."""
    projects_repo.delete_todo(todo_id)


def create_asgi_app():
    return mcp.streamable_http_app()
