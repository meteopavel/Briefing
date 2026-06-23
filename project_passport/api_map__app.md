# API map: app

Просканировано Python-файлов: 22
Включено в карту: 17
Пропущено без значимой API-информации: 5

Сводная статистика:
- модулей: 17
- классов: 1
- dataclass: 1
- функций: 72
- методов: 5
- констант: 26

---

# app/cli.py

Модуль:
CLI-точка входа для генерации документов и экспорта данных из Redmine.
Модуль отвечает за:
- генерацию акта и отчёта для бухгалтерии;
- экспорт сырого контекста задач Redmine за период;
- экспорт контекста задач чанками;
- сборку финального prompt для летописи.

Классы:

- `CliContext [dataclass]`
  Общий контекст выполнения CLI-команд.
  Поля:
  - `row: Any`
  - `start_date: str`
  - `end_date: str`
  - `report_url: str`
  - `redmine_filename: str`

Функции:

- `create_parser() -> argparse.ArgumentParser`
  Создаёт и настраивает CLI-парсер аргументов.

- `prepare_context() -> CliContext`
  Подготавливает общий контекст для выполнения CLI-команд.

- `print_report_url(report_url: str) -> None`
  Печатает ссылку для сверки данных в Redmine.

- `handle_export_chronicle_context(args: Namespace, context: CliContext) -> None`
  Обрабатывает сценарий экспорта сырого контекста задач Redmine.

- `handle_export_chronicle_context_chunks(args: Namespace, context: CliContext) -> None`
  Обрабатывает сценарий экспорта контекста задач чанками.

- `handle_build_chronicle_final_prompt(context: CliContext) -> None`
  Обрабатывает сценарий сборки финального prompt для летописи.

- `handle_generate_documents(args: Namespace, context: CliContext) -> None`
  Обрабатывает сценарий генерации бухгалтерских документов.

- `main() -> None`
  Запускает CLI-приложение и маршрутизирует выполнение по аргументам.

---

# app/config.py

Модуль:
Конфигурация приложения и загрузка значений из переменных окружения.
Модуль отвечает за:
- загрузку .env-файла;
- чтение и преобразование JSON-значений из переменных окружения;
- хранение путей к входным, шаблонным и выходным файлам;
- хранение справочников и констант, используемых в приложении.

Константы:
- `LOCAL_SECURE_DIR = '.local_secure'`
- `LOCAL_RUNTIME_DIR = '.local_runtime'`
- `ACTS_DATA_FILE = os.path.join(LOCAL_SECURE_DIR, 'salary_data.xlsx')`
- `TEMPLATES_DIR = os.path.join(LOCAL_SECURE_DIR, 'templates')`
- `ACT_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, 'template_act.docx')`
- `REPORT_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, 'template_report.docx')`
- `OUTPUT_DIR = os.path.join(LOCAL_RUNTIME_DIR, 'output')`
- `TIMELOGS_DIR = os.path.join(LOCAL_RUNTIME_DIR, 'timelogs')`
- `REDMINE_URL = os.getenv('REDMINE_URL', '').rstrip('/')`
- `REDMINE_API_KEY = os.getenv('REDMINE_API_KEY')`
- `REDMINE_USER_ID = os.getenv('REDMINE_USER_ID')`
- `DOCUMENT_OWNER = os.getenv('DOCUMENT_OWNER', 'Contractor')`
- `USER_MAP = load_int_key_dict_env('USER_MAP', {})`
- `ISSUE_STATUS_MAP = load_int_key_dict_env('ISSUE_STATUS_MAP', {})`
- `ISSUE_PRIORITY_MAP = load_int_key_dict_env('ISSUE_PRIORITY_MAP', {})`
- `CUSTOM_FIELD_MAP = load_int_key_dict_env('CUSTOM_FIELD_MAP', {})`
- `CUSTOM_FIELDS_HIDE_IF_NEGATIVE = load_set_dict_env('CUSTOM_FIELDS_HIDE_IF_NEGATIVE', {})`
- `USER_REFERENCE_CUSTOM_FIELD_IDS = {16, 17, 18, 19}`
- `MONTH_NAMES = {'01': 'января', '02': 'февраля', '03': 'марта', '04': 'апреля', '05': 'мая', '06': 'июня', '07': '…`
- `REPORT_TABLE_COLUMN_WIDTHS_INCH = [0.4, 1.6, 2.9, 1.3]`

Функции:

- `load_json_env(name: str, default: Any) -> Any`
  Загружает значение переменной окружения как JSON.
  Если переменная не задана или пуста, возвращает default.
  Если значение не является корректным JSON, выбрасывает ValueError.

- `load_int_key_dict_env(name: str, default: dict[Any, Any]) -> dict[int, Any]`
  Загружает JSON-словарь из переменной окружения и приводит его ключи к int.

- `load_set_dict_env(name: str, default: dict[Any, Any]) -> dict[Any, set[Any]]`
  Загружает JSON-словарь из переменной окружения и приводит его значения к set.

---

# app/services/acts_data.py

Модуль:
Загрузка и подготовка данных по актам из Excel-файла.
Модуль отвечает за чтение таблицы актов и преобразование относительных
имён файлов Redmine в полные пути внутри каталога таймлогов.

Функции:

- `load_acts_data() -> pd.DataFrame`
  Загружает данные по актам из Excel-файла.
  Возвращает DataFrame с приведёнными типами колонок и полными путями
  к CSV-файлам Redmine в колонке `redmine_file`.

---

# app/services/chronicle/chunking.py

Модуль:
Вспомогательные функции для разбиения данных Chronicle на chunk'и
и построения путей к директориям экспорта.

Константы:
- `T = TypeVar('T')`

Функции:

- `split_into_chunks(items: list[T], chunk_size: int) -> list[list[T]]`
  Разбивает список элементов на последовательные chunk'и фиксированного размера.
  Если размер chunk'а меньше или равен нулю, выбрасывает ValueError.

- `get_chronicle_base_dir(output_root_dir: str, start_date_str: str, end_date_str: str) -> str`
  Строит путь к базовой директории Chronicle-экспорта для заданного периода.

---

# app/services/chronicle/export.py

Модуль:
Функции экспорта Chronicle-контекста и сборки итоговых prompt-файлов.
Модуль отвечает за:
- экспорт полного контекста задач за период;
- разбиение задач на chunk'и и сохранение связанных файлов;
- сборку финального prompt'а по заполненным chunk summary.

Функции:

- `export_issue_contexts_for_period_in_chunks(start_date_str: str, end_date_str: str, output_root_dir: str, chunk_size: int = 6) -> str`
  Экспортирует контекст задач за период в полный JSON, chunk-файлы и prompt-файлы.
  Получает общий payload задач за период, делит задачи на chunk'и, сохраняет
  полный контекст, manifest, JSON по chunk'ам, prompt-файлы и пустые summary-файлы.
  Возвращает путь к директории экспорта.

- `build_final_chronicle_prompt(start_date_str: str, end_date_str: str, output_root_dir: str) -> str`
  Собирает финальный месячный prompt по заполненным summary-файлам chunk'ов.
  Читает manifest экспорта, проверяет наличие и непустое содержимое всех
  `*.summary.md` файлов, затем объединяет их в итоговый prompt для LLM.
  Дополнительно подготавливает пустой файл для финального анализа.

- `export_issue_contexts_for_period(start_date_str: str, end_date_str: str, output_filename: str, issue_id: int | None = None) -> str`
  Экспортирует контекст задач за период в один JSON-файл.
  Используется для сохранения полного payload без разбиения на chunk'и.
  Может ограничивать экспорт одной задачей через `issue_id`.

---

# app/services/chronicle/prompts.py

Модуль:
Функции генерации prompt'ов и вспомогательных markdown-текстов для Chronicle.
Модуль отвечает за подготовку prompt'ов для анализа chunk'ов задач,
README с дальнейшими шагами и итогового prompt'а для месячного анализа.

Функции:

- `build_chunk_prompt(chunk_payload: dict[str, Any]) -> str`
  Формирует markdown prompt для анализа одного chunk'а задач.
  На вход принимает payload чанка с периодом, метаданными chunk'а и списком задач.
  Встраивает в prompt сериализованный JSON-контекст для передачи в LLM.

- `build_next_steps_readme(start_date_str: str, end_date_str: str, total_chunks: int) -> str`
  Формирует README с инструкцией по дальнейшей работе после экспорта Chronicle.
  README описывает, какие файлы уже созданы, как обрабатывать chunk prompt'ы
  и куда сохранять итоговый месячный анализ.

- `build_final_prompt_content(period_from: str, period_to: str, chunk_summaries: list[dict[str, Any]]) -> str`
  Собирает финальный prompt для месячного анализа на основе summary по chunk'ам.
  Объединяет содержимое всех chunk summary в один текстовый блок,
  который затем используется как вход для итогового LLM-анализа.

---

# app/services/documents.py

Модуль:
Генерация документов акта и отчёта на основе шаблонов DOCX.
Модуль отвечает за:
- формирование акта по строке данных;
- формирование отчёта по CSV-файлу трудозатрат;
- подстановку значений в шаблоны документов;
- сохранение итоговых DOCX-файлов.

Функции:

- `generate_act(row: dict[str, Any] | pd.Series, output_dir: str = OUTPUT_DIR) -> str`
  Генерирует DOCX-акт по строке данных.
  В документ подставляются номер акта, даты периода и сумма вознаграждения
  в числовом и текстовом формате.

- `generate_report(row: dict[str, Any] | pd.Series, output_dir: str = OUTPUT_DIR, debug_print: bool = False) -> str`
  Генерирует DOCX-отчёт по строке данных и CSV-файлу трудозатрат.
  Загружает таблицу трудозатрат, рассчитывает распределение суммы
  вознаграждения по задачам, формирует итоговую таблицу и вставляет
  её в шаблон отчёта.

---

# app/services/redmine/client.py

Модуль:
HTTP-клиент для получения данных из Redmine API.
Модуль содержит методы для загрузки:
- time entries за период;
- названий задач по списку id;
- полной задачи;
- полной задачи вместе с journals.

Классы:

- `RedmineClient`
  Клиент для чтения данных из Redmine через REST API.
  Методы:
  - `fetch_time_entries(start_date_str: str, end_date_str: str) -> list[dict[str, Any]]`
    Загружает time entries текущего пользователя Redmine за указанный период.
  - `fetch_issue_subjects(issue_ids: set[int] | list[int]) -> dict[int, str]`
    Загружает названия задач по набору или списку идентификаторов.
  - `fetch_issue_with_journals(issue_id: int) -> dict[str, Any]`
    Загружает полные данные задачи вместе с journals.
  - `fetch_issue(issue_id: int) -> dict[str, Any]`
    Загружает полные данные одной задачи без journals.
  - `fetch_my_issues(status_id: str = 'open') -> list[dict[str, Any]]`
    Загружает задачи, назначенные на текущего пользователя.

---

# app/services/redmine/context_builder.py

Модуль:
Сборка нормализованного контекста задач Redmine для последующего экспорта.
Модуль отвечает за:
- получение brief-информации по связанным задачам;
- извлечение связанных issue id из relations и journals;
- сборку контекста одной задачи;
- формирование итогового payload по периоду или по одной задаче.

Функции:

- `safe_fetch_issue_brief(issue_id: int) -> dict[str, Any]`
  Безопасно загружает краткую информацию по задаче.
  Если задача недоступна или запрос завершается ошибкой, возвращает
  минимальный объект только с идентификатором задачи.

- `extract_related_issue_ids(issue_data: dict[str, Any]) -> list[int]`
  Извлекает идентификаторы связанных задач из relations и journals задачи.
  В результат не включается id текущей задачи. Возвращает отсортированный
  список уникальных идентификаторов.

- `build_related_issues(issue_data: dict[str, Any]) -> list[dict[str, Any]]`
  Строит список кратких описаний связанных задач для переданной задачи.

- `build_issue_context(issue_data: dict[str, Any], time_entries_in_period: list[dict[str, Any]]) -> dict[str, Any]`
  Собирает нормализованный контекст одной задачи Redmine.
  В итоговый контекст включаются основные поля задачи, связанные задачи,
  custom fields, journals и трудозатраты за выбранный период.

- `build_issue_context_payload(start_date_str: str, end_date_str: str, issue_id: int | None = None) -> dict[str, Any]`
  Формирует итоговый payload контекста задач за период.
  Загружает time entries за указанный диапазон дат, группирует их по задачам,
  подгружает расширенный контекст задач с journals и возвращает итоговую
  структуру либо для одной задачи, либо для набора задач.

---

# app/services/redmine/exports.py

Модуль:
Экспорт трудозатрат Redmine в табличный CSV-формат.
Модуль отвечает за:
- преобразование time entries в плоские записи;
- построение таблицы трудозатрат по дням;
- форматирование значений для CSV;
- добавление итогов по строкам и по всем задачам;
- сохранение итогового файла.

Функции:

- `build_timelog_records(entries: list[dict[str, Any]], subjects_map: dict[int, str]) -> list[dict[str, Any]]`
  Преобразует список time entries в плоские записи для табличного экспорта.
  Для каждой записи формирует имя задачи и сохраняет дату и количество часов.

- `build_date_columns(start_date_str: str, end_date_str: str) -> list[str]`
  Строит список дат периода в формате YYYY-MM-DD с дневным шагом.

- `build_timelog_dataframe(records: list[dict[str, Any]], all_dates: list[str]) -> pd.DataFrame`
  Строит pivot-таблицу трудозатрат по задачам и датам.
  На выходе возвращает DataFrame, где строки — задачи, а колонки — даты периода.

- `format_timelog_value(value: Any) -> str`
  Форматирует числовое значение трудозатрат для CSV.
  Нулевые значения преобразуются в `""`, дробная часть записывается через запятую.

- `format_timelog_dataframe(dataframe: pd.DataFrame, all_dates: list[str]) -> pd.DataFrame`
  Применяет форматирование значений ко всем дневным колонкам DataFrame.

- `parse_formatted_timelog_value(value: Any) -> float`
  Преобразует форматированное строковое значение трудозатрат обратно в число.

- `add_row_totals(dataframe: pd.DataFrame, all_dates: list[str]) -> pd.DataFrame`
  Добавляет в DataFrame колонку с итоговым временем по каждой строке.

- `build_total_row(dataframe: pd.DataFrame, all_dates: list[str]) -> list[str]`
  Строит итоговую строку с суммами по всем датам и общим итогом.

- `append_totals_row(dataframe: pd.DataFrame, all_dates: list[str]) -> pd.DataFrame`
  Переименовывает колонку задачи и добавляет в конец DataFrame итоговую строку.

- `save_dataframe_to_csv(dataframe: pd.DataFrame, filename: str) -> str`
  Сохраняет DataFrame в CSV-файл с разделителем `;`.
  Если директория назначения отсутствует, она будет создана.

- `fetch_and_save_timelog(start_date_str: str, end_date_str: str, redmine_filename: str) -> str`
  Загружает time entries из Redmine за период, строит CSV-таблицу и сохраняет её в файл.

---

# app/services/redmine/normalizers.py

Модуль:
Функции нормализации и упрощения данных Redmine.
Модуль содержит утилиты для:
- очистки словарей от пустых значений;
- нормализации текстовых полей;
- разрешения идентификаторов пользователей, статусов и приоритетов в имена;
- нормализации custom fields, journals и time entries.

Функции:

- `remove_empty_values(data: dict[str, Any]) -> dict[str, Any]`
  Возвращает копию словаря без пустых значений.
  Из результата удаляются значения None, пустые строки, пустые списки
  и пустые словари.

- `normalize_text(value: Any) -> str | None`
  Нормализует текстовое значение.
  Приводит переводы строк к формату `\n`, удаляет хвостовые пробелы
  в строках, схлопывает слишком большие пустые блоки и обрезает
  пробелы по краям.

- `resolve_user_name(value: Any) -> str | None`
  Преобразует id пользователя в отображаемое имя.
  Если значение не удаётся привести к числу, возвращает его как есть.

- `resolve_status_name(value: Any) -> str | None`
  Преобразует id статуса задачи в отображаемое имя.

- `resolve_priority_name(value: Any) -> str | None`
  Преобразует id приоритета задачи в отображаемое имя.

- `resolve_custom_field_value(field_id: int | None, value: Any) -> Any`
  Нормализует значение custom field с учётом его типа.
  Для пользовательских полей, содержащих user id, возвращает имя пользователя.
  Для строковых значений выполняет текстовую нормализацию.

- `should_keep_custom_field(field_name: str | None, field_value: Any) -> bool`
  Определяет, нужно ли сохранять custom field в итоговом результате.
  Поле отбрасывается, если оно пустое или его значение входит в список
  скрываемых отрицательных значений для данного поля.

- `normalize_journal_details(details: list[dict[str, Any]] | None) -> list[dict[str, Any]]`
  Нормализует список изменений из journal details.
  Преобразует специальные поля Redmine в более читаемый вид, разрешает
  custom fields, статусы и пользователей, а также отбрасывает изменения,
  которые не нужно включать в итоговый контекст.

- `normalize_time_entry(entry: dict[str, Any], include_project: bool = False) -> dict[str, Any]`
  Нормализует одну запись трудозатрат Redmine.
  При необходимости может дополнительно включать название проекта.

- `normalize_custom_fields(custom_fields: list[dict[str, Any]] | None) -> dict[str, Any]`
  Нормализует набор custom fields задачи в плоский словарь.

- `normalize_journals(journals: list[dict[str, Any]] | None) -> list[dict[str, Any]]`
  Нормализует journals задачи.
  В результат включаются только записи, содержащие заметки и/или значимые изменения.

---

# app/utils/dates.py

Модуль:
Утилиты для работы с датами и выбора записей по целевому месяцу.
Модуль содержит функции для:
- валидации дат в формате ДД.ММ.ГГГГ;
- форматирования дат для документов;
- преобразования даты в формат ГГГГ-ММ-ДД;
- выбора строки данных за предыдущий месяц;
- определения диапазона дат по строке трудозатрат.

Функции:

- `is_valid_dd_mm_yyyy(value: Any) -> bool`
  Проверяет, что значение имеет формат ДД.ММ.ГГГГ.
  Проверка включает:
  - строковый тип;
  - наличие трёх компонентов, разделённых точками;
  - числовой состав компонентов;
  - длину компонентов;
  - допустимые диапазоны дня и месяца.
  Функция не проверяет корректность календарной даты полностью,
  например 31.02.2024 будет считаться валидной.

- `format_date(date_str: str, short: bool = False) -> str`
  Форматирует дату из вида ДД.ММ.ГГГГ в текстовый формат для документов.
  Примеры:
  - `01.02.2025` -> `«01» февраля 2025 года`
  - `01.02.2025`, short=True -> `«01» февраля 2025 г.`

- `dd_mm_yyyy_to_yyyy_mm_dd(date_str: str) -> str`
  Преобразует дату из формата ДД.ММ.ГГГГ в формат ГГГГ-ММ-ДД.

- `get_target_month_row(acts_df: pd.DataFrame, acts_data_file: str) -> pd.Series`
  Возвращает единственную строку данных за предыдущий календарный месяц.
  Если текущий месяц январь, выбирается декабрь предыдущего года.
  Функция печатает диагностическую информацию о текущей дате и целевом периоде.
  Выбрасывает ValueError, если запись не найдена или найдено несколько записей.

- `get_date_range(row_data: pd.Series, date_columns: pd.Index | list[str]) -> tuple[str, str]`
  Определяет диапазон дат оказания услуги по строке трудозатрат.
  Находит первую и последнюю дату среди переданных колонок, в которых
  присутствуют непустые значения. Если таких значений нет, возвращает `('-', '-')`.
  Ожидается, что имена колонок дат находятся в формате ГГГГ-ММ-ДД.

---

# app/utils/docx_utils.py

Модуль:
Утилиты для работы с DOCX-документами.
Модуль содержит функции для:
- настройки шрифта run-элементов;
- замены плейсхолдеров в абзацах и таблицах документа;
- добавления границ таблице;
- вставки таблицы DataFrame на место плейсхолдера;
- выделения первого абзаца жирным шрифтом.

Функции:

- `set_font(run: Run, name: str = 'Times New Roman', size: int = 11) -> None`
  Устанавливает шрифт и размер для текстового фрагмента run.

- `replace_in_paragraph(paragraph: Paragraph, placeholder: str, replacement_text: str) -> None`
  Заменяет плейсхолдер в одном абзаце на переданный текст.
  Если плейсхолдер отсутствует, функция ничего не делает.
  После замены текст абзаца пересобирается через run-элементы
  с единым форматированием.

- `replace_text_with_formatting(doc: DocumentType, placeholder: str, replacement_text: Any) -> None`
  Заменяет плейсхолдер на текст во всех абзацах документа и в таблицах.
  Значение replacement_text приводится к строке перед подстановкой.

- `add_table_borders(table: Table) -> None`
  Добавляет границы ко всем внешним и внутренним линиям таблицы.

- `add_table_at_placeholder(doc: DocumentType, df: pd.DataFrame, placeholder: str = '{{TABLE}}') -> None`
  Вставляет таблицу из DataFrame на место указанного плейсхолдера.
  Плейсхолдер ищется среди абзацев документа. После нахождения
  соответствующий абзац удаляется, а на его место вставляется таблица.

- `make_bold_first_paragraph(doc: DocumentType) -> None`
  Делает все run-элементы первого абзаца документа жирными.

---

# app/utils/files.py

Модуль:
Утилиты для записи файлов.
Модуль содержит функции для:
- записи данных в JSON-файл;
- записи текста в обычный текстовый файл.

Функции:

- `write_json_file(filename: str, payload: Any) -> None`
  Записывает переданные данные в JSON-файл.
  Если директория для файла не существует, она будет создана.
  JSON сохраняется в UTF-8 с отступами и без ASCII-экранирования.

- `write_text_file(filename: str, content: str) -> None`
  Записывает текст в файл.
  Если директория для файла не существует, она будет создана.
  Файл сохраняется в кодировке UTF-8.

---

# app/utils/money.py

Модуль:
Утилиты для работы с денежными суммами.
Модуль содержит функции для преобразования числовой суммы
в текстовое представление в рублях.

Функции:

- `amount_to_words_rubles(amount: int | float) -> str`
  Преобразует сумму в текстовое представление рублей.
  Дробная часть отбрасывается. Результат возвращается в формате:
  "(текстовая сумма) рублей".

---

# app/utils/redmine.py

Модуль:
Утилиты для работы со ссылками и параметрами Redmine.

Функции:

- `build_redmine_report_url(start_date: str, end_date: str) -> str`
  Собирает ссылку на отчёт Redmine по time entries за указанный период.

---

# app/web.py

Модуль:
FastAPI web application: маршруты Briefing.

Константы:
- `PROJECT_ROOT = Path(__file__).resolve().parent.parent`
- `STATIC_DIR = PROJECT_ROOT / 'web_static'`
- `TEMPLATES_DIR = PROJECT_ROOT / 'templates'`
- `_SPAN_RE = re.compile('%\\{([^}]+)\\}([^%]*)%')`
- `_EMAIL_RE = re.compile('[a-zA-Z0-9._+%-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}')`

Функции:

- `_fix_spans(html: str) -> str`
  Нет докстринга.

- `_protect_emails(text: str) -> str`
  Оборачивает email-адреса в <notextile>, чтобы @ не интерпретировался как код.

- `_render(text: str | None) -> str`
  Нет докстринга.

- `index(request: Request)`
  Нет докстринга.

- `issue_journals(issue_id: int)`
  Нет докстринга.

- `attachment_thumbnail(attachment_id: int)`
  Нет докстринга.

- `avatar(user_id: int)`
  Нет докстринга.

- `health()`
  Нет докстринга.