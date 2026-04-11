from datetime import datetime


def is_valid_dd_mm_yyyy(value):
    if not isinstance(value, str):
        return False

    parts = value.split('.')
    if len(parts) != 3:
        return False

    day, month, year = parts
    return (
        day.isdigit()
        and month.isdigit()
        and year.isdigit()
        and len(day) == 2
        and len(month) == 2
        and len(year) == 4
        and 1 <= int(day) <= 31
        and 1 <= int(month) <= 12
    )


def format_date(date_str, short=False):
    parts = date_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Неверный формат даты: '{date_str}'. Ожидается ДД.ММ.ГГГГ")

    day, month_num, year = parts

    if not (day.isdigit() and month_num.isdigit() and year.isdigit()):
        raise ValueError(f"Дата содержит нечисловые компоненты: '{date_str}'")

    if len(day) != 2 or len(month_num) != 2 or len(year) != 4:
        raise ValueError(f"Неверная длина компонентов даты: '{date_str}'. Требуется ДД.ММ.ГГГГ")

    month_names = {
        '01': 'января',
        '02': 'февраля',
        '03': 'марта',
        '04': 'апреля',
        '05': 'мая',
        '06': 'июня',
        '07': 'июля',
        '08': 'августа',
        '09': 'сентября',
        '10': 'октября',
        '11': 'ноября',
        '12': 'декабря',
    }

    if month_num not in month_names:
        raise ValueError(f"Неверный номер месяца: '{month_num}' в дате '{date_str}'")

    suffix = 'г.' if short else 'года'
    return f'«{day}» {month_names[month_num]} {year} {suffix}'


def dd_mm_yyyy_to_yyyy_mm_dd(date_str):
    day, month, year = date_str.split('.')
    return f'{year}-{month}-{day}'


def get_target_month_row(acts_df, acts_data_file):
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    if current_month == 1:
        target_month = 12
        target_year = current_year - 1
    else:
        target_month = current_month - 1
        target_year = current_year

    print(f"📅 Текущая дата: {now.strftime('%d.%m.%Y')}")
    print(f'🎯 Генерация документов за {target_year} год, месяц №{target_month}')

    mask = (acts_df['year'] == target_year) & (acts_df['month_num'] == target_month)
    matching_rows = acts_df[mask]

    if matching_rows.empty:
        raise ValueError(f'Не найдена запись за {target_year}-{target_month:02d} в {acts_data_file}')

    if len(matching_rows) > 1:
        raise ValueError(f'Найдено несколько записей за {target_year}-{target_month:02d}')

    return matching_rows.iloc[0]
