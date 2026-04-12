import re

from app.config import USER_MAP, ISSUE_STATUS_MAP, ISSUE_PRIORITY_MAP, CUSTOM_FIELDS_HIDE_IF_NEGATIVE, CUSTOM_FIELD_MAP


def compact_dict(data):
    return {key: value for key, value in data.items() if value not in (None, '', [], {})}


def normalize_text(value):
    if value in (None, ''):
        return None
    value = str(value)
    value = value.replace('\r\n', '\n').replace('\r', '\n')
    value = '\n'.join(line.rstrip() for line in value.split('\n'))
    value = re.sub(r'\n{3,}', '\n\n', value)
    value = value.strip()
    return value or None


def resolve_user_name(value):
    if value in (None, ''):
        return None
    try:
        user_id = int(value)
    except (TypeError, ValueError):
        return value
    return USER_MAP.get(user_id, str(user_id))


def resolve_status_name(value):
    if value in (None, ''):
        return None
    try:
        status_id = int(value)
    except (TypeError, ValueError):
        return value
    return ISSUE_STATUS_MAP.get(status_id, str(status_id))


def resolve_priority_name(value):
    if value in (None, ''):
        return None
    try:
        priority_id = int(value)
    except (TypeError, ValueError):
        return value
    return ISSUE_PRIORITY_MAP.get(priority_id, str(priority_id))


def resolve_custom_field_value(field_id, value):
    if value in (None, ''):
        return None
    if field_id in (16, 17, 18, 19):
        return resolve_user_name(value)
    if isinstance(value, str):
        return normalize_text(value)
    return value


def should_keep_custom_field(field_name, field_value):
    if field_value in (None, '', [], {}):
        return False
    negative_values = CUSTOM_FIELDS_HIDE_IF_NEGATIVE.get(field_name)
    if negative_values and str(field_value) in negative_values:
        return False
    return True


def normalize_journal_details(details):
    normalized = []
    for detail in details or []:
        property_name = detail.get('property')
        name = detail.get('name')
        old_value = detail.get('old_value')
        new_value = detail.get('new_value')
        if property_name == 'cf':
            try:
                field_id = int(name)
            except (TypeError, ValueError):
                field_id = None
            field_name = CUSTOM_FIELD_MAP.get(field_id, f'cf_{name}')
            old_resolved = resolve_custom_field_value(field_id, old_value)
            new_resolved = resolve_custom_field_value(field_id, new_value)
            if not should_keep_custom_field(field_name, new_resolved):
                continue
            item = compact_dict({'field': field_name, 'from': old_resolved, 'to': new_resolved})
            if item:
                normalized.append(item)
            continue
        if property_name == 'attr' and name == 'status_id':
            item = compact_dict({
                'field': 'status',
                'from': resolve_status_name(old_value),
                'to': resolve_status_name(new_value),
            })
            if item:
                normalized.append(item)
            continue
        if property_name == 'attr' and name == 'assigned_to_id':
            item = compact_dict({
                'field': 'assigned_to',
                'from': resolve_user_name(old_value),
                'to': resolve_user_name(new_value),
            })
            if item:
                normalized.append(item)
            continue
        if property_name == 'attr' and name == 'done_ratio':
            continue
        if property_name == 'relation':
            continue
        item = compact_dict({
            'field': name,
            'from': normalize_text(old_value) if isinstance(old_value, str) else old_value,
            'to': normalize_text(new_value) if isinstance(new_value, str) else new_value,
        })
        if item:
            normalized.append(item)
    return normalized


def normalize_time_entry(entry, include_project=False):
    return compact_dict({
        'spent_on': entry.get('spent_on'),
        'hours': entry.get('hours'),
        'comments': normalize_text(entry.get('comments')),
        'activity': (entry.get('activity') or {}).get('name'),
        'project': (entry.get('project') or {}).get('name') if include_project else None,
    })


def normalize_custom_fields(custom_fields):
    result = {}
    for field in custom_fields or []:
        field_id = field.get('id')
        field_name = CUSTOM_FIELD_MAP.get(field_id, field.get('name'))
        field_value = resolve_custom_field_value(field_id, field.get('value'))
        if not should_keep_custom_field(field_name, field_value):
            continue
        result[field_name] = field_value
    return result


def normalize_journals(journals):
    result = []
    for journal in journals or []:
        notes = normalize_text(journal.get('notes'))
        changes = normalize_journal_details(journal.get('details', []))
        item = compact_dict({
            'created_on': journal.get('created_on'),
            'user': (journal.get('user') or {}).get('name'),
            'notes': notes,
            'changes': changes if changes else None,
        })
        if not notes and not changes:
            continue
        if item:
            result.append(item)
    return result