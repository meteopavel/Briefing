"""
CRUD для тудушек проектов (секции bug/feat/ref/ques, статусы, приоритеты,
подпункты). Формат данных — тот же, что у скилла `todo`.
"""

from app.services.projects.db import get_connection

SECTIONS = ['bug', 'feat', 'ref', 'ques']
SECTION_TITLES = {
    'bug': 'Баги',
    'feat': 'Идеи / Фичи',
    'ref': 'Рефакторинг / Техдолг',
    'ques': 'Вопросы / Исследовать',
}
STATUSES = ['open', 'in_progress', 'done', 'wontdo']
PRIORITIES = ['high', 'medium', 'low']

# Единый источник правды для UI: лейбл + SVG-иконка статуса/приоритета.
STATUS_META = {
    'open':        {'label': 'Открыта',  'icon': 'i-status-open',     'icon_class': 'icon-status-open'},
    'in_progress': {'label': 'В работе', 'icon': 'i-status-progress', 'icon_class': 'icon-status-progress'},
    'done':        {'label': 'Готово',   'icon': 'i-status-done',     'icon_class': 'icon-status-done'},
    'wontdo':      {'label': 'Отклонено', 'icon': 'i-status-wontdo',  'icon_class': 'icon-status-wontdo'},
}
PRIORITY_META = {
    'high':   {'label': 'Высокий', 'icon': 'i-prio', 'icon_class': 'icon-prio-high'},
    'medium': {'label': 'Средний', 'icon': 'i-prio', 'icon_class': 'icon-prio-medium'},
    'low':    {'label': 'Низкий',  'icon': 'i-prio', 'icon_class': 'icon-prio-low'},
}


def list_projects() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, slug, title, local_path, contour FROM projects ORDER BY title')
            return cursor.fetchall()


def get_project_by_slug(slug: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, slug, title, local_path, contour FROM projects WHERE slug = %s', (slug,))
            return cursor.fetchone()


def get_todos(project_id: int) -> list[dict]:
    """
    Возвращает все задачи проекта с подпунктами, без группировки/сортировки
    (этим занимается вызывающий код — см. `app/web.py:_group_todos`).
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id, section, number, status, priority, placement_approved, title, closed_note, created_at, updated_at '
                'FROM todos WHERE project_id = %s',
                (project_id,),
            )
            todos = cursor.fetchall()
            if not todos:
                return []
            todo_ids = [todo['id'] for todo in todos]
            cursor.execute(
                'SELECT todo_id, kind, text, position FROM todo_subitems '
                f'WHERE todo_id IN ({",".join(["%s"] * len(todo_ids))}) ORDER BY position',
                todo_ids,
            )
            subitems_by_todo: dict[int, list[dict]] = {}
            for row in cursor.fetchall():
                subitems_by_todo.setdefault(row['todo_id'], []).append(row)
            for todo in todos:
                todo['subitems'] = subitems_by_todo.get(todo['id'], [])
            return todos


def _next_number(cursor, project_id: int, section: str) -> int:
    cursor.execute(
        'SELECT COALESCE(MAX(number), 0) AS max_number FROM todos WHERE project_id = %s AND section = %s',
        (project_id, section),
    )
    return cursor.fetchone()['max_number'] + 1


def import_todo(
    project_id: int,
    section: str,
    number: int,
    status: str,
    priority: str,
    title: str,
    closed_note: str | None,
    subitems: list[dict],
) -> int:
    """
    Вставляет задачу с явно заданным номером (для миграции из docs/TODO.md,
    где нумерация уже существует и должна сохраниться 1:1). В отличие от
    `create_todo`, номер не назначается автоматически.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO todos (project_id, section, number, status, priority, title, closed_note) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (project_id, section, number, status, priority, title, closed_note),
            )
            todo_id = cursor.lastrowid
            for position, subitem in enumerate(subitems):
                cursor.execute(
                    'INSERT INTO todo_subitems (todo_id, kind, text, position) VALUES (%s, %s, %s, %s)',
                    (todo_id, subitem['kind'], subitem['text'], position),
                )
            return todo_id


def create_todo(project_id: int, section: str, priority: str, title: str, subitems: list[dict]) -> int:
    """
    Создаёт задачу со следующим свободным номером в секции.
    `subitems` — список {'kind': 'requirement'|'context', 'text': str}.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            number = _next_number(cursor, project_id, section)
            cursor.execute(
                'INSERT INTO todos (project_id, section, number, status, priority, placement_approved, title) '
                "VALUES (%s, %s, %s, 'open', %s, 0, %s)",
                (project_id, section, number, priority, title),
            )
            todo_id = cursor.lastrowid
            for position, subitem in enumerate(subitems):
                cursor.execute(
                    'INSERT INTO todo_subitems (todo_id, kind, text, position) VALUES (%s, %s, %s, %s)',
                    (todo_id, subitem['kind'], subitem['text'], position),
                )
            return todo_id


def update_status(todo_id: int, status: str, closed_note: str | None = None) -> None:
    """
    Меняет статус. При переходе в done/wontdo заметка обязательна —
    вызывающий код (роут) должен это проверить до вызова.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'UPDATE todos SET status = %s, closed_note = %s WHERE id = %s',
                (status, closed_note, todo_id),
            )


def update_priority(todo_id: int, priority: str, reset_approved: bool = False) -> None:
    """
    Меняет приоритет. reset_approved=True (ручное изменение через веб) дополнительно
    сбрасывает placement_approved — т.к. размещение (секция+приоритет) изменилось,
    его надо заново утвердить. MCP-вызовы идут с reset_approved=False (агент сам
    выставляет флаг после ревью через update_placement_approved).
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            if reset_approved:
                cursor.execute('UPDATE todos SET priority = %s, placement_approved = 0 WHERE id = %s', (priority, todo_id))
            else:
                cursor.execute('UPDATE todos SET priority = %s WHERE id = %s', (priority, todo_id))


def add_subitem(todo_id: int, kind: str, text: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT COALESCE(MAX(position), -1) AS max_position FROM todo_subitems WHERE todo_id = %s',
                (todo_id,),
            )
            next_position = cursor.fetchone()['max_position'] + 1
            cursor.execute(
                'INSERT INTO todo_subitems (todo_id, kind, text, position) VALUES (%s, %s, %s, %s)',
                (todo_id, kind, text, next_position),
            )


def edit_todo(todo_id: int, title: str, section: str, subitems: list[dict] | None = None, reset_approved: bool = False) -> None:
    """
    Атомарно меняет заголовок/секцию и (опционально) подпункты задачи в одной
    транзакции. Соединение по умолчанию в autocommit, поэтому оборачиваем
    явные begin()/commit() с rollback() при ошибке — иначе replace+update
    прошли бы в раздельных авто-коммитах и при сбое второго шага подпункты
    оказались бы перезаписаны при старом заголовке/секции (рассинхрон).

    title — новый заголовок; section — bug|feat|ref|ques (при смене номер
    перевыпускается как следующий свободный в новой секции, UNIQUE-констрейнт
    project_id+section+number не даёт сохранить старый);
    subitems — None (не трогать) либо полная замена списком
    {'kind': 'requirement'|'context', 'text': str}; пустой список — удалить все.
    reset_approved — сбросить placement_approved при смене секции (ручное
    изменение через веб; MCP не передаёт — агент сам управляет флагом). Сброс
    применяется только когда секция реально меняется; при правке только title
    флаг не трогается.
    Валидация значений — на вызывающей стороне (роут/MCP).
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                conn.begin()
                if subitems is not None:
                    cursor.execute('DELETE FROM todo_subitems WHERE todo_id = %s', (todo_id,))
                    for position, subitem in enumerate(subitems):
                        cursor.execute(
                            'INSERT INTO todo_subitems (todo_id, kind, text, position) VALUES (%s, %s, %s, %s)',
                            (todo_id, subitem['kind'], subitem['text'], position),
                        )
                cursor.execute('SELECT project_id, section FROM todos WHERE id = %s', (todo_id,))
                current = cursor.fetchone()
                if current is None:
                    conn.rollback()
                    return
                if section == current['section']:
                    cursor.execute('UPDATE todos SET title = %s WHERE id = %s', (title, todo_id))
                else:
                    next_number = _next_number(cursor, current['project_id'], section)
                    if reset_approved:
                        cursor.execute(
                            'UPDATE todos SET title = %s, section = %s, number = %s, placement_approved = 0 WHERE id = %s',
                            (title, section, next_number, todo_id),
                        )
                    else:
                        cursor.execute(
                            'UPDATE todos SET title = %s, section = %s, number = %s WHERE id = %s',
                            (title, section, next_number, todo_id),
                        )
                conn.commit()
            except Exception:
                conn.rollback()
                raise


def update_placement_approved(todo_id: int, approved: bool) -> None:
    """Ставит/снимает флаг «размещение (секция+приоритет) утверждено»."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE todos SET placement_approved = %s WHERE id = %s', (1 if approved else 0, todo_id))


def delete_todo(todo_id: int) -> None:
    """Удаляет задачу. Подпункты снимаются каскадом (FK ON DELETE CASCADE)."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM todos WHERE id = %s', (todo_id,))
