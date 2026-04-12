"""
Утилиты для работы со ссылками и параметрами Redmine.
"""

from app.config import REDMINE_URL


def build_redmine_report_url(start_date: str, end_date: str) -> str:
    """
    Собирает ссылку на отчёт Redmine по time entries за указанный период.
    """
    return (
        f'{REDMINE_URL}/time_entries/report'
        '?utf8=%E2%9C%93&set_filter=1&sort=spent_on%3Adesc'
        '&f%5B%5D=spent_on&op%5Bspent_on%5D=%3E%3C'
        f'&v%5Bspent_on%5D%5B%5D={start_date}&v%5Bspent_on%5D%5B%5D={end_date}'
        '&f%5B%5D=user_id&op%5Buser_id%5D=%3D&v%5Buser_id%5D%5B%5D=me'
        '&f%5B%5D=&group_by=&t%5B%5D=&columns=day&criteria%5B%5D=issue'
    )
