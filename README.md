# Redmine Documents & Chronicle Automation

[![Python](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/python.svg)](https://docs.python.org/3/)
[![pandas](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/pandas.svg)](https://pandas.pydata.org/docs/)
[![Markdown](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/markdown.svg)](https://www.markdownguide.org/)

Python CLI для генерации документов, экспорта данных из Redmine, подготовки
Chronicle-контекста и LLM-friendly prompt workflow.

Личный инструмент, используемый в реальном рабочем процессе (production use):
автоматизирует выгрузку трудозатрат из Redmine, формирование отчётных документов
и подготовку структурированного контекста задач для последующего LLM-анализа.

## Два режима работы

**Документооборот.** Загрузка трудозатрат из Redmine за выбранный период, сборка
CSV-таблицы с итогами по датам и задачам, генерация акта и отчёта в формате DOCX
на основе локальных шаблонов.

**Летопись задач (Chronicle).** Подготовка структурированного контекста задач,
разбиение его на chunk'и, сборка итогового monthly prompt и выгрузка JSON- и
markdown-артефактов для дальнейшего анализа языковой моделью.

## CLI-команды

```bash
# Документооборот
python main.py                       # генерация акта и отчёта за текущий месяц
python main.py --debug               # то же, с выводом расчётной таблицы в консоль

# Летопись задач (Chronicle)
python main.py --export-chronicle-context-chunks --start ДД.ММ.ГГГГ --end ДД.ММ.ГГГГ
                                     # экспорт контекста задач чанками
python main.py --build-chronicle-final-prompt --start ДД.ММ.ГГГГ --end ДД.ММ.ГГГГ
                                     # финальный prompt из chunk summary
python main.py --chronicle-issue-id N
                                     # экспорт контекста по одной задаче
```

Все сценарии маршрутизируются через единый CLI entrypoint (`main.py`).

## Стек

Python, Redmine API, pandas, python-docx, python-dotenv, JSON, CSV, Markdown.

## Установка

Рекомендуется виртуальное окружение Python 3.9.

```bash
git clone https://github.com/meteopavel/Chronicle_Reporting_Automation.git
cd Chronicle_Reporting_Automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Затем создать `.env` и указать URL Redmine, API-ключ и параметры периода.

## Безопасность

В репозитории — только код проекта, шаблоны документов и безопасная инфраструктура.

Вне git (`.gitignore`): файл `.env`, сгенерированные документы и CSV в
`.local_runtime/output/`, выгруженный контекст задач и prompt-артефакты в
`.local_secure/`. При необходимости локальные данные хранятся зашифрованными в
`secure/sensitive_bundle.7z`. Реальные рабочие данные в репозиторий не попадают.

## Автор

Павел Найдёнов — разработчик, пришедший в IT из метеорологии и преподавания.

[meteopavel.space](https://meteopavel.space)
