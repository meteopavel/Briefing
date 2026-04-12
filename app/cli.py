import argparse
import os

from app.config import ACTS_DATA_FILE, OUTPUT_DIR, REDMINE_URL
from app.services.acts_data import load_acts_data
from app.services.documents import generate_act, generate_report
from app.services.chronicle.export import (
    build_final_chronicle_prompt, export_issue_contexts_for_period_in_chunks,
    export_issue_contexts_for_period
)
from app.services.redmine.exports import fetch_and_save_timelog
from app.utils.dates import dd_mm_yyyy_to_yyyy_mm_dd, get_target_month_row


def main():
    parser = argparse.ArgumentParser(description='Генерация акта, отчёта и экспорт контекста Redmine')
    parser.add_argument('--debug', action='store_true', help='Показать таблицу расчёта в консоли')
    parser.add_argument('--export-chronicle-context', action='store_true', help='Экспортировать сырой контекст задач из Redmine за целевой период')
    parser.add_argument('--export-chronicle-context-chunks', action='store_true', help='Экспортировать контекст задач чанками и подготовить prompt-файлы')
    parser.add_argument('--build-chronicle-final-prompt', action='store_true', help='Собрать финальный prompt из chunk summary файлов')
    parser.add_argument('--chronicle-issue-id', type=int, help='Экспортировать контекст только по одной задаче Redmine')
    parser.add_argument('--chronicle-chunk-size', type=int, default=6, help='Размер чанка по количеству задач, по умолчанию 6')
    args = parser.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    acts_dataframe = load_acts_data()
    row = get_target_month_row(acts_dataframe, ACTS_DATA_FILE)
    redmine_filename = row['redmine_file']
    start_date = dd_mm_yyyy_to_yyyy_mm_dd(row['start_date'])
    end_date = dd_mm_yyyy_to_yyyy_mm_dd(row['end_date'])
    report_url = (
        f'{REDMINE_URL}/time_entries/report'
        '?utf8=%E2%9C%93&set_filter=1&sort=spent_on%3Adesc'
        '&f%5B%5D=spent_on&op%5Bspent_on%5D=%3E%3C'
        f'&v%5Bspent_on%5D%5B%5D={start_date}&v%5Bspent_on%5D%5B%5D={end_date}'
        '&f%5B%5D=user_id&op%5Buser_id%5D=%3D&v%5Buser_id%5D%5B%5D=me'
        '&f%5B%5D=&group_by=&t%5B%5D=&columns=day&criteria%5B%5D=issue'
    )
    if args.export_chronicle_context:
        print('📚 Экспорт сырого контекста задач для летописи...\n')
        print(f'🔍 Ссылка для сверки в Redmine:\n{report_url}\n')
        filename_suffix = f'{start_date}_{end_date}'
        if args.chronicle_issue_id is not None:
            filename_suffix += f'-issue-{args.chronicle_issue_id}'
        chronicle_filename = os.path.join(OUTPUT_DIR, f'redmine-chronicle-context-{filename_suffix}.json')
        try:
            export_issue_contexts_for_period(
                start_date,
                end_date,
                chronicle_filename,
                issue_id=args.chronicle_issue_id,
            )
            print(f'\n🎉 Готово! Контекст сохранён в: {chronicle_filename}')
        except Exception as error:
            print(f'\n❌ ОШИБКА: {error}')
            raise SystemExit(1)
        return
    if args.export_chronicle_context_chunks:
        print('📚 Экспорт контекста задач чанками для летописи...\n')
        print(f'🔍 Ссылка для сверки в Redmine:\n{report_url}\n')
        try:
            output_dir = export_issue_contexts_for_period_in_chunks(
                start_date,
                end_date,
                output_root_dir=OUTPUT_DIR,
                chunk_size=args.chronicle_chunk_size,
            )
            print(f'\n🎉 Готово! Чанки и prompt-файлы сохранены в: {output_dir}')
        except Exception as error:
            print(f'\n❌ ОШИБКА: {error}')
            raise SystemExit(1)
        return
    if args.build_chronicle_final_prompt:
        print('🧠 Собираем финальный prompt по chunk summary...\n')
        try:
            output_dir = build_final_chronicle_prompt(
                start_date,
                end_date,
                output_root_dir=OUTPUT_DIR,
            )
            print(f'\n🎉 Готово! Финальный prompt сохранён в: {output_dir}')
        except Exception as error:
            print(f'\n❌ ОШИБКА: {error}')
            raise SystemExit(1)
        return
    print('📄 Генерация документов для бухгалтерии...\n')
    print(f'\n🔍 Ссылка для сверки в Redmine:\n{report_url}\n')
    fetch_and_save_timelog(start_date, end_date, redmine_filename)
    try:
        generate_act(row, OUTPUT_DIR)
        generate_report(row, OUTPUT_DIR, debug_print=args.debug)
        print(f'\n🎉 Готово! Файлы в папке: {OUTPUT_DIR}/')
    except Exception as error:
        print(f'\n❌ ОШИБКА: {error}')
        raise SystemExit(1)
