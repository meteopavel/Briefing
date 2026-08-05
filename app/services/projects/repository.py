"""
CRUD для тудушек проектов (секции bug/feat/refactor/q, статусы, приоритеты,
подпункты). Формат данных — тот же, что использует скилл `todo` (zcode).
"""

from app.services.projects.db import get_connection

SECTIONS = ['bug', 'feat', 'refactor', 'q']
SECTION_TITLES = {
    'bug': 'Баги',
    'feat': 'Идеи / Фичи',
    'refactor': 'Рефакторинг / Техдолг',
    'q': 'Вопросы / Исследовать',
}
STATUSES = ['open', 'in_progress', 'done', 'wontdo']
PRIORITIES = ['high', 'medium', 'low']


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
                'SELECT id, section, number, status, priority, title, closed_note, created_at, updated_at '
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
                'INSERT INTO todos (project_id, section, number, status, priority, title) '
                "VALUES (%s, %s, %s, 'open', %s, %s)",
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


def update_priority(todo_id: int, priority: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
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


def replace_subitems(todo_id: int, subitems: list[dict]) -> None:
    """
    Полная замена подпунктов задачи: удаляет старые, вставляет переданный
    список (position = порядок в списке). Удобно для single-user UI, где форма
    ✎ присылает актуальный снимок подпунктов одним батчем. Пустой список —
    удалить все подпункты.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM todo_subitems WHERE todo_id = %s', (todo_id,))
            for position, subitem in enumerate(subitems):
                cursor.execute(
                    'INSERT INTO todo_subitems (todo_id, kind, text, position) VALUES (%s, %s, %s, %s)',
                    (todo_id, subitem['kind'], subitem['text'], position),
                )


def update_todo_meta(todo_id: int, title: str, section: str) -> None:
    """
    Меняет заголовок задачи и (опционально) секцию. При смене секции номер
    перевыпускается как следующий свободный в новой секции (UNIQUE-констрейнт
    project_id+section+number не даёт сохранить старый). Подпункты не трогает.
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT project_id, section FROM todos WHERE id = %s', (todo_id,))
            current = cursor.fetchone()
            if current is None:
                return
            if section == current['section']:
                cursor.execute('UPDATE todos SET title = %s WHERE id = %s', (title, todo_id))
            else:
                next_number = _next_number(cursor, current['project_id'], section)
                cursor.execute(
                    'UPDATE todos SET title = %s, section = %s, number = %s WHERE id = %s',
                    (title, section, next_number, todo_id),
                )


def delete_todo(todo_id: int) -> None:
    """Удаляет задачу. Подпункты снимаются каскадом (FK ON DELETE CASCADE)."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM todos WHERE id = %s', (todo_id,))
