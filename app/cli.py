import argparse
import os

from app.config import ACTS_DATA_FILE, OUTPUT_DIR, REDMINE_URL
from app.services.acts_data import load_acts_data
from app.services.documents import generate_act, generate_report
from app.services.redmine import fetch_and_save_timelog
from app.utils.dates import dd_mm_yyyy_to_yyyy_mm_dd, get_target_month_row


def main():
    parser = argparse.ArgumentParser(description='Генерация акта и отчёта')
    parser.add_argument('--debug', action='store_true', help='Показать таблицу расчёта в консоли')
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print('📄 Генерация документов для бухгалтерии...\n')

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
    print(f'\n🔍 Ссылка для сверки в Redmine:\n{report_url}\n')

    fetch_and_save_timelog(start_date, end_date, redmine_filename)

    try:
        generate_act(row, OUTPUT_DIR)
        generate_report(row, OUTPUT_DIR, debug_print=args.debug)
        print(f'\n🎉 Готово! Файлы в папке: {OUTPUT_DIR}/')
    except Exception as error:
        print(f'\n❌ ОШИБКА: {error}')
        raise SystemExit(1)
