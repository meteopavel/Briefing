"""
CLI-точка входа для генерации документов и экспорта данных из Redmine.
Модуль отвечает за:
- генерацию акта и отчёта для бухгалтерии;
- экспорт сырого контекста задач Redmine за период;
- экспорт контекста задач чанками;
- сборку финального prompt для летописи.
"""

import argparse
import os
from argparse import Namespace
from dataclasses import dataclass
from typing import Any

from app.config import ACTS_DATA_FILE, OUTPUT_DIR
from app.services.acts_data import load_acts_data
from app.services.chronicle.export import (
    build_final_chronicle_prompt,
    export_issue_contexts_for_period,
    export_issue_contexts_for_period_in_chunks,
)
from app.services.documents import generate_act, generate_report
from app.services.redmine.exports import fetch_and_save_timelog
from app.utils.dates import dd_mm_yyyy_to_yyyy_mm_dd, get_target_month_row, is_valid_dd_mm_yyyy
from app.utils.redmine import build_redmine_report_url


@dataclass
class CliContext:
    """
    Общий контекст выполнения CLI-команд.
    """
    row: Any
    start_date: str
    end_date: str
    report_url: str
    redmine_filename: str


def create_parser() -> argparse.ArgumentParser:
    """
    Создаёт и настраивает CLI-парсер аргументов.
    """
    parser = argparse.ArgumentParser(
        description='Генерация акта, отчёта и экспорт контекста Redmine',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Показать таблицу расчёта в консоли',
    )
    parser.add_argument(
        '--export-chronicle-context',
        action='store_true',
        help='Экспортировать сырой контекст задач из Redmine за целевой период',
    )
    parser.add_argument(
        '--export-chronicle-context-chunks',
        action='store_true',
        help='Экспортировать контекст задач чанками и подготовить prompt-файлы',
    )
    parser.add_argument(
        '--build-chronicle-final-prompt',
        action='store_true',
        help='Собрать финальный prompt из chunk summary файлов',
    )
    parser.add_argument(
        '--chronicle-issue-id',
        type=int,
        help='Экспортировать контекст только по одной задаче Redmine',
    )
    parser.add_argument(
        '--chronicle-chunk-size',
        type=int,
        default=6,
        help='Размер чанка по количеству задач, по умолчанию 6',
    )
    parser.add_argument(
        '--start',
        type=str,
        default=None,
        help='Дата начала периода ДД.ММ.ГГГГ — переопределяет автоопределение из salary_data.xlsx',
    )
    parser.add_argument(
        '--end',
        type=str,
        default=None,
        help='Дата окончания периода ДД.ММ.ГГГГ — переопределяет автоопределение из salary_data.xlsx',
    )
    return parser


def prepare_context() -> CliContext:
    """
    Подготавливает общий контекст для выполнения CLI-команд.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    acts_dataframe = load_acts_data()
    row = get_target_month_row(acts_dataframe, ACTS_DATA_FILE)
    start_date = dd_mm_yyyy_to_yyyy_mm_dd(row['start_date'])
    end_date = dd_mm_yyyy_to_yyyy_mm_dd(row['end_date'])
    report_url = build_redmine_report_url(start_date, end_date)
    return CliContext(
        row=row,
        start_date=start_date,
        end_date=end_date,
        report_url=report_url,
        redmine_filename=row['redmine_file'],
    )


def print_report_url(report_url: str) -> None:
    """
    Печатает ссылку для сверки данных в Redmine.
    """
    print(f'🔍 Ссылка для сверки в Redmine:\n{report_url}\n')


def handle_export_chronicle_context(args: Namespace, context: CliContext) -> None:
    """
    Обрабатывает сценарий экспорта сырого контекста задач Redmine.
    """
    print('📚 Экспорт сырого контекста задач для летописи...\n')
    print_report_url(context.report_url)
    filename_suffix = f'{context.start_date}_{context.end_date}'
    if args.chronicle_issue_id is not None:
        filename_suffix += f'-issue-{args.chronicle_issue_id}'
    chronicle_filename = os.path.join(
        OUTPUT_DIR,
        f'redmine-chronicle-context-{filename_suffix}.json',
    )
    try:
        export_issue_contexts_for_period(
            context.start_date,
            context.end_date,
            chronicle_filename,
            issue_id=args.chronicle_issue_id,
        )
        print(f'\n🎉 Готово! Контекст сохранён в: {chronicle_filename}')
    except Exception as error:
        print(f'\n❌ ОШИБКА: {error}')
        raise SystemExit(1)


def handle_export_chronicle_context_chunks(args: Namespace, context: CliContext) -> None:
    """
    Обрабатывает сценарий экспорта контекста задач чанками.
    """
    print('📚 Экспорт контекста задач чанками для летописи...\n')
    print_report_url(context.report_url)
    try:
        output_dir = export_issue_contexts_for_period_in_chunks(
            context.start_date,
            context.end_date,
            output_root_dir=OUTPUT_DIR,
            chunk_size=args.chronicle_chunk_size,
        )
        print(f'\n🎉 Готово! Чанки и prompt-файлы сохранены в: {output_dir}')
    except Exception as error:
        print(f'\n❌ ОШИБКА: {error}')
        raise SystemExit(1)


def handle_build_chronicle_final_prompt(context: CliContext) -> None:
    """
    Обрабатывает сценарий сборки финального prompt для летописи.
    """
    print('🧠 Собираем финальный prompt по chunk summary...\n')
    try:
        output_dir = build_final_chronicle_prompt(
            context.start_date,
            context.end_date,
            output_root_dir=OUTPUT_DIR,
        )
        print(f'\n🎉 Готово! Финальный prompt сохранён в: {output_dir}')
    except Exception as error:
        print(f'\n❌ ОШИБКА: {error}')
        raise SystemExit(1)


def handle_generate_documents(args: Namespace, context: CliContext) -> None:
    """
    Обрабатывает сценарий генерации бухгалтерских документов.
    """
    if context.row is None:
        print('❌ Ошибка: --start/--end не поддерживается для генерации документов.')
        print('Уберите флаги --start и --end — период определяется автоматически из salary_data.xlsx.')
        raise SystemExit(1)
    print('📄 Генерация документов для бухгалтерии...\n')
    print_report_url(context.report_url)
    fetch_and_save_timelog(
        context.start_date,
        context.end_date,
        context.redmine_filename,
    )
    try:
        generate_act(context.row, OUTPUT_DIR)
        generate_report(context.row, OUTPUT_DIR, debug_print=args.debug)
        print(f'\n🎉 Готово! Файлы в папке: {OUTPUT_DIR}/')
    except Exception as error:
        print(f'\n❌ ОШИБКА: {error}')
        raise SystemExit(1)


def main() -> None:
    """
    Запускает CLI-приложение и маршрутизирует выполнение по аргументам.
    """
    parser = create_parser()
    args = parser.parse_args()

    if bool(args.start) != bool(args.end):
        print('❌ Ошибка: --start и --end должны быть указаны вместе.')
        raise SystemExit(1)

    if args.start and args.end:
        if not is_valid_dd_mm_yyyy(args.start):
            print(f'❌ Ошибка: неверный формат --start: {args.start!r}. Ожидается ДД.ММ.ГГГГ')
            raise SystemExit(1)
        if not is_valid_dd_mm_yyyy(args.end):
            print(f'❌ Ошибка: неверный формат --end: {args.end!r}. Ожидается ДД.ММ.ГГГГ')
            raise SystemExit(1)
        start_date = dd_mm_yyyy_to_yyyy_mm_dd(args.start)
        end_date = dd_mm_yyyy_to_yyyy_mm_dd(args.end)
        print(f'📅 Период задан вручную: {args.start} — {args.end}\n')
        context = CliContext(
            row=None,
            start_date=start_date,
            end_date=end_date,
            report_url=build_redmine_report_url(start_date, end_date),
            redmine_filename=None,
        )
    else:
        context = prepare_context()

    if args.export_chronicle_context:
        handle_export_chronicle_context(args, context)
        return
    if args.export_chronicle_context_chunks:
        handle_export_chronicle_context_chunks(args, context)
        return
    if args.build_chronicle_final_prompt:
        handle_build_chronicle_final_prompt(context)
        return
    handle_generate_documents(args, context)
