import json
import os

from datetime import datetime
from pathlib import Path

from app.services.chronicle.chunking import split_into_chunks, get_chronicle_base_dir
from app.services.chronicle.promts import (
    build_chunk_prompt, build_next_steps_readme, build_final_prompt_content
)
from app.services.redmine.context_builder import build_issue_context_payload
from app.services.redmine.normalizers import compact_dict
from app.utils.files import write_text_file, write_json_file


def export_issue_contexts_for_period_in_chunks(start_date_str, end_date_str, output_root_dir, chunk_size=6):
    payload = build_issue_context_payload(start_date_str, end_date_str)
    issues = payload.get('issues')
    if not issues:
        if payload.get('issue'):
            issues = [payload['issue']]
        else:
            raise ValueError('Не удалось найти задачи для экспорта чанков')
    total_issues = len(issues)
    issue_chunks = split_into_chunks(issues, chunk_size)
    total_chunks = len(issue_chunks)
    base_dir = get_chronicle_base_dir(output_root_dir, start_date_str, end_date_str)
    chunks_dir = os.path.join(base_dir, 'chunks')
    full_context_filename = os.path.join(base_dir, 'full_context.json')
    write_json_file(full_context_filename, payload)
    manifest = {
        'period': {'from': start_date_str, 'to': end_date_str},
        'total_issues': total_issues,
        'chunk_size': chunk_size,
        'total_chunks': total_chunks,
        'files': {
            'full_context': 'full_context.json',
        },
        'chunks': [],
    }
    for index, chunk_issues in enumerate(issue_chunks, start=1):
        chunk_payload = compact_dict({
            'period': {'from': start_date_str, 'to': end_date_str},
            'chunk': {
                'index': index,
                'total_chunks': total_chunks,
                'issues_in_chunk': len(chunk_issues),
                'total_issues': total_issues,
            },
            'issues': chunk_issues,
        })
        if payload.get('entries_without_issue'):
            chunk_payload['entries_without_issue'] = payload['entries_without_issue']
        chunk_json_filename = os.path.join(chunks_dir, f'chunk_{index:02d}.json')
        chunk_prompt_filename = os.path.join(chunks_dir, f'chunk_{index:02d}.prompt.md')
        chunk_summary_filename = os.path.join(chunks_dir, f'chunk_{index:02d}.summary.md')
        write_json_file(chunk_json_filename, chunk_payload)
        write_text_file(chunk_prompt_filename, build_chunk_prompt(chunk_payload))
        write_text_file(chunk_summary_filename, '')
        manifest['chunks'].append({
            'index': index,
            'json_file': os.path.relpath(chunk_json_filename, base_dir),
            'prompt_file': os.path.relpath(chunk_prompt_filename, base_dir),
            'summary_file': os.path.relpath(chunk_summary_filename, base_dir),
            'issues_in_chunk': len(chunk_issues),
        })
    manifest_filename = os.path.join(base_dir, 'manifest.json')
    write_json_file(manifest_filename, manifest)
    readme_filename = os.path.join(base_dir, 'README_NEXT_STEPS.md')
    write_text_file(readme_filename, build_next_steps_readme(start_date_str, end_date_str, total_chunks))
    print(f'💾 Полный контекст сохранён: {full_context_filename}')
    print(f'💾 Manifest сохранён: {manifest_filename}')
    print(f'💾 README сохранён: {readme_filename}')
    print(f'💾 Чанки сохранены в: {chunks_dir}')
    print(f'🧩 Всего задач: {total_issues}, всего чанков: {total_chunks}, размер чанка: {chunk_size}')
    return base_dir


def build_final_chronicle_prompt(start_date_str, end_date_str, output_root_dir):
    base_dir = get_chronicle_base_dir(output_root_dir, start_date_str, end_date_str)
    manifest_filename = os.path.join(base_dir, 'manifest.json')
    if not os.path.isfile(manifest_filename):
        raise ValueError(f'Не найден manifest.json: {manifest_filename}. Сначала запусти экспорт чанков.')
    with open(manifest_filename, 'r', encoding='utf-8') as file:
        manifest = json.load(file)
    chunk_summaries = []
    missing_summary_files = []
    for chunk_meta in manifest.get('chunks', []):
        summary_rel_path = chunk_meta['summary_file']
        summary_abs_path = os.path.join(base_dir, summary_rel_path)
        if not os.path.isfile(summary_abs_path):
            missing_summary_files.append(summary_rel_path)
            continue
        with open(summary_abs_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        if not content:
            missing_summary_files.append(summary_rel_path)
            continue
        chunk_summaries.append({
            'index': chunk_meta['index'],
            'content': content,
        })
    if missing_summary_files:
        missing_list = '\n'.join(f'- {path}' for path in missing_summary_files)
        raise ValueError(
            'Не найдены или пустые summary-файлы.\n'
            'Нужно сначала получить ответы по всем chunk prompt и сохранить их в соответствующие *.summary.md файлы:\n'
            f'{missing_list}'
        )
    final_prompt = build_final_prompt_content(
        manifest['period']['from'],
        manifest['period']['to'],
        chunk_summaries,
    )
    final_prompt_filename = os.path.join(base_dir, 'final_analysis.prompt.md')
    write_text_file(final_prompt_filename, final_prompt)
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    period_year = start_date.strftime("%Y")
    period_month = start_date.strftime("%m")
    final_summary_filename = f'final_analysis.summary_{period_year}_{period_month}.md'
    final_summary_path = Path('.local_secure/chronicle') / final_summary_filename
    final_summary_path.parent.mkdir(parents=True, exist_ok=True)
    if not final_summary_path.exists():
        final_summary_path.write_text('', encoding='utf-8')
    print(f'💾 Финальный prompt сохранён: {final_prompt_filename}')
    print(f'📝 Пустой файл для итогового анализа подготовлен: {final_summary_path}')
    return final_prompt_filename


def export_issue_contexts_for_period(start_date_str, end_date_str, output_filename, issue_id=None):
    payload = build_issue_context_payload(start_date_str, end_date_str, issue_id=issue_id)
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    print(f'💾 Контекст задач сохранён: {output_filename}')
    return output_filename