"""
Утилиты для работы с денежными суммами.
Модуль содержит функции для преобразования числовой суммы
в текстовое представление в рублях.
"""
from __future__ import annotations

from num2words import num2words


def amount_to_words_rubles(amount: int | float) -> str:
    """
    Преобразует сумму в текстовое представление рублей.
    Дробная часть отбрасывается. Результат возвращается в формате:
    "(текстовая сумма) рублей".
    """
    rubles = int(amount)
    words = num2words(rubles, lang='ru', to='cardinal')
    words = words.replace('рубль', '').replace('рубля', '').replace('рублей', '')
    return f'({words.strip()}) рублей'
