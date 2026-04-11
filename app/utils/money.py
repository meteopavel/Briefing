from num2words import num2words


def amount_to_words_rubles(amount):
    rubles = int(amount)
    words = num2words(rubles, lang='ru', to='cardinal')
    words = words.replace('рубль', '').replace('рубля', '').replace('рублей', '')
    return f'({words.strip()}) рублей'
