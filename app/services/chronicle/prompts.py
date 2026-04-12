"""
Функции генерации prompt'ов и вспомогательных markdown-текстов для Chronicle.
Модуль отвечает за подготовку prompt'ов для анализа chunk'ов задач,
README с дальнейшими шагами и итогового prompt'а для месячного анализа.
"""

import json

from datetime import datetime
from pathlib import Path
from typing import Any


def build_chunk_prompt(chunk_payload: dict[str, Any]) -> str:
    """
    Формирует markdown prompt для анализа одного chunk'а задач.
    На вход принимает payload чанка с периодом, метаданными chunk'а и списком задач.
    Встраивает в prompt сериализованный JSON-контекст для передачи в LLM.
    """
    period = chunk_payload['period']
    chunk = chunk_payload['chunk']
    json_text = json.dumps(chunk_payload, ensure_ascii=False, indent=2)
    return f"""
    Ты анализируешь часть месячного контекста работы разработчика.
    Период: {period['from']} — {period['to']}
    Это chunk {chunk['index']} из {chunk['total_chunks']}.
    В этом chunk {chunk['issues_in_chunk']} задач из {chunk['total_issues']}.
    Что нужно сделать:
    1. Ответь в Markdown.
    2. Не дублируй JSON и не копируй его большими кусками.
    3. Сфокусируйся на вкладе разработчика:
       - что именно было сделано;
       - какой был практический результат;
       - были ли итерации, правки, ревью, доработки;
       - был ли вклад в код, документацию, отладку, коммуникацию.
    4. Для каждой задачи дай краткий, содержательный разбор.
    5. После разбора задач сделай обобщение по chunk.
    Желаемый формат ответа:
    # Анализ chunk {chunk['index']}/{chunk['total_chunks']}
    ## Задача #<id> — <краткое название>
    - Суть задачи:
    - Вклад разработчика:
    - Результат:
    - Итерации / сложности:
    ## Итог по chunk
    Краткое обобщение по этому набору задач.
    ## Ключевые достижения
    - ...
    - ...
    ## Наблюдения
    - ...
    - ...
    Ниже JSON-контекст:
    ```json
    {json_text}
    ```
    """


def build_next_steps_readme(start_date_str: str, end_date_str: str, total_chunks: int) -> str:
    """
    Формирует README с инструкцией по дальнейшей работе после экспорта Chronicle.
    README описывает, какие файлы уже созданы, как обрабатывать chunk prompt'ы
    и куда сохранять итоговый месячный анализ.
    """
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    period_year = start_date.strftime("%Y")
    period_month = start_date.strftime("%m")
    final_summary_filename = f"final_analysis.summary_{period_year}_{period_month}.md"
    final_summary_path = Path(".local_secure/chronicle") / final_summary_filename
    return f"""
    # Chronicle export: next steps

    Период: {start_date_str} — {end_date_str}

    ## Что уже сгенерировано
    - `full_context.json` — полный контекст за период
    - `manifest.json` — индексный файл
    - `chunks/chunk_XX.json` — JSON по чанкам
    - `chunks/chunk_XX.prompt.md` — готовые prompt-файлы для анализа
    - `chunks/chunk_XX.summary.md` — пустые файлы, в которые нужно сохранить ответы LLM

    ## Как работать дальше

    ### 1. Последовательно открыть prompt-файлы
    Для каждого чанка по очереди:
    - открыть `chunks/chunk_01.prompt.md`
    - отправить его в LLM
    - получить ответ
    - сохранить ответ в `chunks/chunk_01.summary.md`
    Повторить для всех чанков до `chunk_{total_chunks:02d}.summary.md`.

    ### 2. После заполнения всех summary-файлов
    Запустить сборку финального prompt:
    python main.py --build-chronicle-final-prompt

    ### 3. Отправить финальный промт в LLM
    Скопировать итоговый ответ в уже созданный файл: {final_summary_path}
    """


def build_final_prompt_content(
    period_from: str,
    period_to: str,
    chunk_summaries: list[dict[str, Any]],
) -> str:
    """
    Собирает финальный prompt для месячного анализа на основе summary по chunk'ам.
    Объединяет содержимое всех chunk summary в один текстовый блок,
    который затем используется как вход для итогового LLM-анализа.
    """
    summaries_text = '\n\n'.join(
        f'--- chunk {item["index"]} ---\n\n{item["content"]}'
        for item in chunk_summaries
    )
    return f"""
    Ниже даны summary по chunk'ам задач разработчика за месяц.
    Нужно подготовить итоговый анализ деятельности разработчика за месяц.
    Период: {period_from} — {period_to}
    Сделай:
    Общую сводку по месяцу.
    Основные направления работы.
    Самые значимые результаты.
    Что занимало больше всего внимания.
    Какие были признаки качества работы:
    доведение задач до конца,
    реакция на ревью,
    работа с документацией,
    аккуратность итераций.
    Какие зоны роста можно отметить.
    Сформируй итог в формате, пригодном для отчёта или самоанализа.
    Summary по chunk'ам:
    {summaries_text}
    """
