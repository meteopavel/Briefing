"""
MCP-сервер Briefing: тулы над тудушками проектов (та же БД и тот же
`repository.py`, что у веб-вкладки «Проекты»). Подключается по HTTP —
из Claude Code и из zcode — вместо чтения/записи docs/TODO.md.

Контракт двуязычный и худой (feat.28): чтение — один язык по параметру
lang (по умолчанию 'en', экономия токенов; 'ru'/'both' опционально),
запись — только явными парами title_ru+title_en / text_ru+text_en, обе
версии обязательны — гарантирует сама сигнатура тула. Однострочный текст
с раскладкой split_by_lang — прерогатива веб-форм и import_todo, MCP его
не принимает.
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

LANGS = ('en', 'ru', 'both')


def _project_or_raise(project_slug: str) -> dict:
    project = projects_repo.get_project_by_slug(project_slug)
    if project is None:
        raise ValueError(f'Проект «{project_slug}» не найден')
    return project


def _check_lang(lang: str) -> None:
    if lang not in LANGS:
        raise ValueError(f'Некорректный язык: {lang} (ожидается один из {LANGS})')


def _serialize_todo(todo: dict, lang: str) -> dict:
    """
    Сериализация без дублирования текста: в режимах en/ru — одно поле
    title (+ text у подпунктов) и фактический язык версии в title_lang/
    text_lang (если запрошенной версии нет, берётся вторая — агент видит,
    чего не хватает); в режиме both — только колонки *_ru/*_en, без
    производных полей.
    """
    out = {
        'id': todo['id'],
        'section': todo['section'],
        'number': todo['number'],
        'status': todo['status'],
        'priority': todo['priority'],
        'placement_approved': todo['placement_approved'],
        'closed_note': todo['closed_note'],
        'created_at': todo['created_at'].isoformat() if todo.get('created_at') else None,
        'updated_at': todo['updated_at'].isoformat() if todo.get('updated_at') else None,
    }
    if lang == 'both':
        out['title_ru'] = todo.get('title_ru')
        out['title_en'] = todo.get('title_en')
        out['subitems'] = [
            {'kind': sub['kind'], 'position': sub['position'], 'text_ru': sub.get('text_ru'), 'text_en': sub.get('text_en')}
            for sub in todo.get('subitems', [])
        ]
        return out
    fallback = 'ru' if lang == 'en' else 'en'
    out['title'] = todo.get(f'title_{lang}') or todo.get(f'title_{fallback}')
    out['title_lang'] = lang if todo.get(f'title_{lang}') else (fallback if out['title'] else None)
    subitems = []
    for sub in todo.get('subitems', []):
        text = sub.get(f'text_{lang}') or sub.get(f'text_{fallback}')
        subitems.append({
            'kind': sub['kind'],
            'position': sub['position'],
            'text': text,
            'text_lang': lang if sub.get(f'text_{lang}') else (fallback if text else None),
        })
    out['subitems'] = subitems
    return out


def _validated_pair(title_ru: str, title_en: str) -> tuple[str, str]:
    pair = ((title_ru or '').strip(), (title_en or '').strip())
    if not pair[0] or not pair[1]:
        raise ValueError('Нужны обе языковые версии: title_ru и title_en')
    return pair


def _validated_subitems(subitems: list[dict] | None) -> list[dict] | None:
    """Подпункты записи: у каждого обязаны быть непустые text_ru и text_en."""
    if subitems is None:
        return None
    out = []
    for sub in subitems:
        if sub.get('kind') not in ('requirement', 'context'):
            raise ValueError(f'Некорректный тип подпункта: {sub.get("kind")} (ожидается requirement|context)')
        text_ru = (sub.get('text_ru') or '').strip()
        text_en = (sub.get('text_en') or '').strip()
        if not text_ru or not text_en:
            raise ValueError('Подпункт требует обе языковые версии: text_ru и text_en')
        out.append({'kind': sub['kind'], 'text_ru': text_ru, 'text_en': text_en})
    return out


@mcp.tool()
def list_projects() -> list[dict]:
    """Список проектов, заведённых в Briefing (slug, title, contour, is_hub); хаб первым."""
    return projects_repo.list_projects()


@mcp.tool()
def list_todos(project_slug: str, section: str | None = None, include_closed: bool = True, lang: str = 'en') -> list[dict]:
    """
    Задачи проекта с подпунктами (без группировки/сортировки).

    section (опционально): bug|feat|ref|ques — только эта секция.
    include_closed=False: отбросить done/wontdo (для «что в тудушке?»).
    lang: 'en' (по умолчанию) | 'ru' | 'both' — язык текстов. В режимах
    en/ru каждый текст отдаётся один раз (title/text, фактический язык —
    в title_lang/text_lang); 'both' — колонки *_ru/*_en (для правки).
    Без параметров — все задачи проекта. Для больших проектов фильтруй:
    полный список растёт с историей и может не влезть в лимит ответа тула.
    """
    _check_lang(lang)
    if section is not None and section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    project = _project_or_raise(project_slug)
    todos = projects_repo.get_todos(project['id'])
    if section is not None:
        todos = [t for t in todos if t['section'] == section]
    if not include_closed:
        todos = [t for t in todos if t['status'] not in ('done', 'wontdo')]
    return [_serialize_todo(t, lang) for t in todos]


@mcp.tool()
def get_todo(todo_id: int, lang: str = 'both') -> dict:
    """
    Одна задача с подпунктами по внутреннему id. lang: 'both' (по умолчанию —
    для подготовки правки нужны обе версии) | 'en' | 'ru'.
    """
    _check_lang(lang)
    todo = projects_repo.get_todo(todo_id)
    if todo is None:
        raise ValueError(f'Задача {todo_id} не найдена')
    return _serialize_todo(todo, lang)


@mcp.tool()
def create_todo(project_slug: str, section: str, priority: str, title_ru: str, title_en: str, subitems: list[dict] | None = None) -> int:
    """
    Создаёт задачу со следующим свободным номером в указанной секции.
    section: bug|feat|ref|ques. priority: critical|high|medium|low.
    Обе языковые версии обязательны: title_ru и title_en.
    subitems (опционально): [{"kind": "requirement"|"context", "text_ru": "...", "text_en": "..."}] — у каждого тоже обе версии.
    Возвращает id созданной задачи.
    """
    project = _project_or_raise(project_slug)
    if section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    if priority not in projects_repo.PRIORITIES:
        raise ValueError(f'Некорректный приоритет: {priority} (ожидается одна из {projects_repo.PRIORITIES})')
    title_ru, title_en = _validated_pair(title_ru, title_en)
    return projects_repo.create_todo(project['id'], section, priority, title_ru, title_en, _validated_subitems(subitems) or [])


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
def add_todo_subitem(todo_id: int, kind: str, text_ru: str, text_en: str) -> None:
    """
    Добавляет подпункт к задаче. kind: requirement|context; обе языковые
    версии (text_ru и text_en) обязательны.
    """
    if kind not in ('requirement', 'context'):
        raise ValueError(f'Некорректный тип подпункта: {kind} (ожидается requirement|context)')
    text_ru = (text_ru or '').strip()
    text_en = (text_en or '').strip()
    if not text_ru or not text_en:
        raise ValueError('Подпункт требует обе языковые версии: text_ru и text_en')
    projects_repo.add_subitem(todo_id, kind, text_ru, text_en)


@mcp.tool()
def edit_todo(
    todo_id: int,
    title_ru: str,
    title_en: str,
    section: str,
    subitems: list[dict] | None = None,
) -> None:
    """
    Меняет заголовок задачи и (опционально) секцию. section: bug|feat|ref|ques.
    При смене секции номер перевыпускается (bug.3 → feat.5), т.к. номер привязан
    к секции. Статус и приоритет сохраняются.

    Обе языковые версии заголовка обязательны: title_ru и title_en. Перед
    правкой прочитай текущие версии через get_todo(todo_id, lang='both'),
    чтобы не переписывать их вслепую.

    subitems (опционально): полная замена подпунктов списком
    [{"kind": ..., "text_ru": "...", "text_en": "..."}] в указанном порядке
    (обе версии у каждого). Пустой список [] — удалить все подпункты.
    None (по умолчанию) — не трогать.
    """
    if section not in projects_repo.SECTIONS:
        raise ValueError(f'Некорректная секция: {section} (ожидается одна из {projects_repo.SECTIONS})')
    title_ru, title_en = _validated_pair(title_ru, title_en)
    if projects_repo.get_todo(todo_id) is None:
        raise ValueError(f'Задача {todo_id} не найдена')
    projects_repo.edit_todo(todo_id, title_ru, title_en, section, _validated_subitems(subitems))


@mcp.tool()
def delete_todo(todo_id: int) -> None:
    """Удаляет задачу вместе с подпунктами (они снимаются каскадом)."""
    projects_repo.delete_todo(todo_id)


def create_asgi_app():
    return mcp.streamable_http_app()
