"""
Разовый парсер формата тудушки скилла `todo` (docs/TODO.md) → структурированные
задачи для импорта в MySQL. Формат описан в ~/.agents/skills/todo/SKILL.md.
"""

import re

STATUS_MAP = {'📋': 'open', '🚧': 'in_progress', '✅': 'done', '❌': 'wontdo'}
PRIORITY_MAP = {'🔴': 'high', '🟡': 'medium', '⚪': 'low'}
SECTION_HEADER_MAP = {
    'Баги': 'bug',
    'Идеи / Фичи': 'feat',
    'Рефакторинг / Техдолг': 'refactor',
    'Вопросы / Исследовать': 'q',
}

_SECTION_RE = re.compile(r'^## (.+)$')
_TODO_RE = re.compile(r'^- ([📋🚧✅❌]) ([🔴🟡⚪]) (bug|feat|refactor|q)\.(\d+) (.*)$')
_SUBITEM_RE = re.compile(r'^  - (.*)$')
_NOTE_LINE_RE = re.compile(r'^  — (.*)$')
_INLINE_NOTE_RE = re.compile(r'\s—\s((?:fixed|done|решили):.*)$')


def _classify_subitem(text: str) -> str:
    return 'context' if text.lower().startswith('контекст:') else 'requirement'


def parse(markdown: str) -> list[dict]:
    """
    Возвращает список задач в порядке появления в файле, каждая:
    {section, number, status, priority, title, closed_note, subitems: [{kind, text}]}.
    """
    lines = markdown.splitlines()
    todos: list[dict] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('```'):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue

        if _SECTION_RE.match(line):
            i += 1
            continue

        todo_match = _TODO_RE.match(line)
        if not todo_match:
            i += 1
            continue

        status_emoji, priority_emoji, section, number, rest = todo_match.groups()
        status = STATUS_MAP[status_emoji]
        priority = PRIORITY_MAP[priority_emoji]
        title = rest
        closed_note = None

        subitems: list[dict] = []
        i += 1
        while i < len(lines):
            sub_match = _SUBITEM_RE.match(lines[i])
            note_match = _NOTE_LINE_RE.match(lines[i])
            if sub_match:
                text = sub_match.group(1)
                subitems.append({'kind': _classify_subitem(text), 'text': text})
                i += 1
                continue
            if note_match:
                closed_note = note_match.group(1)
                i += 1
                continue
            break

        if closed_note is None and status in ('done', 'wontdo'):
            inline_match = _INLINE_NOTE_RE.search(title)
            if inline_match:
                closed_note = inline_match.group(1)
                title = title[:inline_match.start()].rstrip()

        todos.append({
            'section': section,
            'number': int(number),
            'status': status,
            'priority': priority,
            'title': title,
            'closed_note': closed_note,
            'subitems': subitems,
        })

    return todos
