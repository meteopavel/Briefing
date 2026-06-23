# Briefing

[![Python](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/python.svg)](https://docs.python.org/3/)
[![FastAPI](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/pandas.svg)](https://fastapi.tiangolo.com/)
[![Requests](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/requests.svg)](https://docs.python-requests.org/)
[![Markdown](https://k2bz83mrsg.cdn.twcstorage.ru/images/shields/chronicle/markdown.svg)](https://www.markdownguide.org/)

Личный операционный центр разработчика. Объединяет рабочий трекер (Redmine),
личные проекты и задачи, генерацию документов и LLM-анализ в едином локальном
веб-интерфейсе.

Инструмент написан под себя и используется в реальном рабочем процессе
(production use): утренний обзор задач, логирование времени, ежемесячные отчёты
и хроника — всё в одном месте.

## Что внутри

**Рабочие задачи.** Задачи из Redmine в том виде, в каком удобно работать:
очередь с приоритетами, фильтры по проекту и статусу, логирование времени прямо
из интерфейса.

**Личные проекты.** Тудушки из всех личных проектов в одном месте. JSON-хранилище
с автоматическим бэкапом на сервер при изменениях.

**Генерация документов.** Кнопка — и готов акт или отчёт в DOCX. Загрузка
трудозатрат из Redmine, сборка CSV, генерация по локальным шаблонам.

**LLM-хроника.** Ежемесячный анализ задач через Claude CLI: подготовка
chunk-промптов, стриминг ответа в браузер через SSE, сохранение результата.

## Статус

CLI-часть (документооборот + хроника) — работает в production.
Веб-интерфейс (FastAPI + Jinja2, responsive) — в разработке.

## CLI-команды

```bash
# Документооборот
python main.py                       # генерация акта и отчёта за текущий месяц
python main.py --debug               # то же, с выводом расчётной таблицы в консоль

# Хроника задач
python main.py --export-chronicle-context-chunks --start ДД.ММ.ГГГГ --end ДД.ММ.ГГГГ
python main.py --build-chronicle-final-prompt --start ДД.ММ.ГГГГ --end ДД.ММ.ГГГГ
python main.py --chronicle-issue-id N
```

## Стек

Python, FastAPI, Jinja2, Redmine API, python-docx, pandas, Claude CLI, SSE, JSON,
systemd.

## Установка

```bash
git clone https://github.com/meteopavel/Briefing.git
cd Briefing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Затем создать `.env` и указать URL Redmine, API-ключ и параметры периода.

## Безопасность

В репозитории — только код проекта, шаблоны документов и безопасная инфраструктура.

Вне git (`.gitignore`): файл `.env`, сгенерированные документы и CSV в
`.local_runtime/output/`, выгруженный контекст задач и prompt-артефакты в
`.local_secure/`. Локальные данные хранятся зашифрованными в
`secure/sensitive_bundle.7z` с бэкапом на сервер. Реальные рабочие данные
в репозиторий не попадают.

## Автор

Павел Найдёнов — [meteopavel.space](https://meteopavel.space)
