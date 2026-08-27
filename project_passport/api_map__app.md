# API map: app

Просканировано Python-файлов: 28
Включено в карту: 21
Пропущено без значимой API-информации: 7

Сводная статистика:
- модулей: 21
- классов: 3
- dataclass: 1
- функций: 122
- методов: 17
- констант: 63

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
- `REDMINE_API_KEY_ADMIN = os.getenv('REDMINE_API_KEY_ADMIN') or os.getenv('REDMINE_API_KEY')`
- `REDMINE_USER_ID = os.getenv('REDMINE_USER_ID')`
- `REDMINE_REVIEW_STATUS_IDS = [int(x) for x in os.getenv('REDMINE_REVIEW_STATUS_IDS', '14').split(',') if x.strip()]`
- `REDMINE_STAGE_STATUS_IDS = [int(x) for x in os.getenv('REDMINE_STAGE_STATUS_IDS', '19').split(',') if x.strip()]`
- `REDMINE_PROD_STATUS_IDS = [int(x) for x in os.getenv('REDMINE_PROD_STATUS_IDS', '12').split(',') if x.strip()]`
- `REDMINE_CLOSED_STATUS_IDS = [int(x) for x in os.getenv('REDMINE_CLOSED_STATUS_IDS', '13,5').split(',') if x.strip()]`
- `GITLAB_URL = os.getenv('GITLAB_URL', '').rstrip('/')`
- `GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', '')`
- `GITLAB_PROJECT_PATH = os.getenv('GITLAB_PROJECT_PATH', 'mg/mailganer')`
- `GITLAB_AUTHOR_ID = int(os.getenv('GITLAB_AUTHOR_ID', '68'))`
- `DOCUMENT_OWNER = os.getenv('DOCUMENT_OWNER', 'Contractor')`
- `MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')`
- `MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))`
- `MYSQL_USER = os.getenv('MYSQL_USER', '')`
- `MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')`
- `MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'briefing')`
- `MCP_TOKEN = os.getenv('MCP_TOKEN', '')`
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

# app/mcp_server.py

Модуль:
MCP-сервер Briefing: тулы над тудушками проектов (та же БД и тот же
`repository.py`, что у веб-вкладки «Проекты»). Подключается по HTTP —
из Claude Code и из zcode — вместо чтения/записи docs/TODO.md.

Функции:

- `_project_or_raise(project_slug: str) -> dict`
  Нет докстринга.

- `_serialize_todo(todo: dict) -> dict`
  Нет докстринга.

- `list_projects() -> list[dict]`
  Список проектов, заведённых в Briefing (slug, title, contour).

- `list_todos(project_slug: str, section: str | None = None, include_closed: bool = True) -> list[dict]`
  Задачи проекта с подпунктами (без группировки/сортировки).
  
  section (опционально): bug|feat|ref|ques — только эта секция.
  include_closed=False: отбросить done/wontdo (для «что в тудушке?»).
  Без параметров — все задачи проекта. Для больших проектов фильтруй:
  полный список растёт с историей и может не влезть в лимит ответа тула.

- `create_todo(project_slug: str, section: str, priority: str, title: str, subitems: list[dict] | None = None) -> int`
  Создаёт задачу со следующим свободным номером в указанной секции.
  section: bug|feat|ref|ques. priority: critical|high|medium|low.
  subitems (опционально): [{"kind": "requirement"|"context", "text": "..."}].
  Возвращает id созданной задачи.

- `update_todo_status(todo_id: int, status: str, closed_note: str | None = None) -> None`
  Меняет статус задачи. status: open|in_progress|done|wontdo.
  При переходе в done/wontdo closed_note обязателен (что сделано / что решили).

- `update_todo_priority(todo_id: int, priority: str)`
  Меняет приоритет задачи. priority: critical|high|medium|low.

- `set_todo_placement_approved(todo_id: int, approved: bool) -> None`
  Ставит/снимает флаг «размещение (секция + приоритет) утверждено».
  Агент выставляет approved=True после ревью размещения (когда согласовал
  секцию и приоритет задачи); при ручном изменении секции/приоритета через
  веб флаг снимается автоматически на бэке, а через MCP — нет (агент сам
  управляет им этим тулом).

- `add_todo_subitem(todo_id: int, kind: str, text: str) -> None`
  Добавляет подпункт к задаче. kind: requirement|context.

- `edit_todo(todo_id: int, title: str, section: str, subitems: list[dict] | None = None) -> None`
  Меняет заголовок задачи и (опционально) секцию. section: bug|feat|ref|ques.
  При смене секции номер перевыпускается (bug.3 → feat.5), т.к. номер привязан
  к секции. Статус и приоритет сохраняются.
  
  subitems (опционально): полная замена подпунктов списком
  [{"kind": "requirement"|"context", "text": "..."}] в указанном порядке.
  Пустой список [] — удалить все подпункты. None (по умолчанию) — не трогать.

- `delete_todo(todo_id: int) -> None`
  Удаляет задачу вместе с подпунктами (они снимаются каскадом).

- `create_asgi_app()`
  Нет докстринга.

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

# app/services/gitlab/client.py

Константы:
- `_MR_CACHE_TTL = 300`
- `_BRANCH_SEP_RE = re.compile('[-/._]')`

Классы:

- `GitLabClient`
  Нет докстринга.
  Методы:
  - `_fetch_all_mrs() -> list[dict]`
    Нет докстринга.
  - `_ensure_cache() -> None`
    Нет докстринга.
  - `get_mrs_for_issue(issue_id: int) -> list[dict]`
    Возвращает список MR, связанных с задачей, по номеру в имени ветки.
  - `invalidate_cache() -> None`
    Нет докстринга.

---

# app/services/projects/db.py

Модуль:
Подключение к MySQL для вкладки «Проекты».
Без ORM — обычный курсор, в стиле остальных сервисных модулей проекта.

Функции:

- `get_connection()`
  Отдаёт открытое соединение с БД briefing (autocommit включён).
  Закрывает соединение при выходе из контекста в любом случае.

---

# app/services/projects/repository.py

Модуль:
CRUD для тудушек проектов (секции bug/feat/ref/ques, статусы, приоритеты,
подпункты). Формат данных — тот же, что у скилла `todo`.

Константы:
- `SECTIONS = ['bug', 'feat', 'ref', 'ques']`
- `SECTION_TITLES = {'bug': 'Баги', 'feat': 'Идеи / Фичи', 'ref': 'Рефакторинг / Техдолг', 'ques': 'Вопросы / Исследова…`
- `STATUSES = ['open', 'in_progress', 'done', 'wontdo']`
- `PRIORITIES = ['critical', 'high', 'medium', 'low']`
- `STATUS_META = {'open': {'label': 'Открыта', 'icon': 'i-status-open', 'icon_class': 'icon-status-open'}, 'in_progr…`
- `PRIORITY_META = {'critical': {'label': 'Критический', 'icon': 'i-prio', 'icon_class': 'icon-prio-critical'}, 'high'…`

Функции:

- `list_projects() -> list[dict]`
  Нет докстринга.

- `get_project_by_slug(slug: str) -> dict | None`
  Нет докстринга.

- `get_todos(project_id: int) -> list[dict]`
  Возвращает все задачи проекта с подпунктами, без группировки/сортировки
  (этим занимается вызывающий код — см. `app/web.py:_group_todos`).

- `_next_number(cursor, project_id: int, section: str) -> int`
  Нет докстринга.

- `import_todo(project_id: int, section: str, number: int, status: str, priority: str, title: str, closed_note: str | None, subitems: list[dict]) -> int`
  Вставляет задачу с явно заданным номером (для миграции из docs/TODO.md,
  где нумерация уже существует и должна сохраниться 1:1). В отличие от
  `create_todo`, номер не назначается автоматически.

- `create_todo(project_id: int, section: str, priority: str, title: str, subitems: list[dict]) -> int`
  Создаёт задачу со следующим свободным номером в секции.
  `subitems` — список {'kind': 'requirement'|'context', 'text': str}.

- `update_status(todo_id: int, status: str, closed_note: str | None = None) -> None`
  Меняет статус. При переходе в done/wontdo заметка обязательна —
  вызывающий код (роут) должен это проверить до вызова.

- `update_priority(todo_id: int, priority: str, reset_approved: bool = False) -> None`
  Меняет приоритет. reset_approved=True (ручное изменение через веб) дополнительно
  сбрасывает placement_approved — т.к. размещение (секция+приоритет) изменилось,
  его надо заново утвердить. MCP-вызовы идут с reset_approved=False (агент сам
  выставляет флаг после ревью через update_placement_approved).

- `add_subitem(todo_id: int, kind: str, text: str) -> None`
  Нет докстринга.

- `edit_todo(todo_id: int, title: str, section: str, subitems: list[dict] | None = None, reset_approved: bool = False) -> None`
  Атомарно меняет заголовок/секцию и (опционально) подпункты задачи в одной
  транзакции. Соединение по умолчанию в autocommit, поэтому оборачиваем
  явные begin()/commit() с rollback() при ошибке — иначе replace+update
  прошли бы в раздельных авто-коммитах и при сбое второго шага подпункты
  оказались бы перезаписаны при старом заголовке/секции (рассинхрон).
  
  title — новый заголовок; section — bug|feat|ref|ques (при смене номер
  перевыпускается как следующий свободный в новой секции, UNIQUE-констрейнт
  project_id+section+number не даёт сохранить старый);
  subitems — None (не трогать) либо полная замена списком
  {'kind': 'requirement'|'context', 'text': str}; пустой список — удалить все.
  reset_approved — сбросить placement_approved при смене секции (ручное
  изменение через веб; MCP не передаёт — агент сам управляет флагом). Сброс
  применяется только когда секция реально меняется; при правке только title
  флаг не трогается.
  Валидация значений — на вызывающей стороне (роут/MCP).

- `update_placement_approved(todo_id: int, approved: bool) -> None`
  Ставит/снимает флаг «размещение (секция+приоритет) утверждено».

- `delete_todo(todo_id: int) -> None`
  Удаляет задачу. Подпункты снимаются каскадом (FK ON DELETE CASCADE).

---

# app/services/redmine/client.py

Модуль:
HTTP-клиент для получения данных из Redmine API.
Модуль содержит методы для загрузки:
- time entries за период;
- названий задач по списку id;
- полной задачи;
- полной задачи вместе с journals.

Константы:
- `_SPENT_CACHE_TTL = 300`
- `_CLOSED_CACHE_TTL = 300`

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
  - `fetch_passive_issues() -> dict`
    Задачи на пассивных статусах (ревью/stage/prod), над которыми работал пользователь.
    
    Закрытые отсюда убраны — их выборка дорогая (батчи по всем работанным id,
    число растёт с историей) и раньше тормозила открытие страницы. Теперь они
    грузятся отдельно по клику — см. fetch_closed_issues().
  - `fetch_closed_issues() -> list[dict]`
    Закрытые задачи, над которыми работал пользователь.
    
    Дорогая выборка: идёт от всех работанных id и батчами по 100
    переспрашивает у Redmine, оставляя лишь закрытые. Вызывается по клику
    «Показать закрытые» (не при открытии страницы), результат кэшируется на
    _CLOSED_CACHE_TTL — повторные клики мгновенны.
  - `_fetch_and_cache() -> None`
    Загружает все записи времени и сохраняет в кэш.
  - `_ensure_cache() -> None`
    Нет докстринга.
  - `fetch_my_spent_hours() -> dict[int, dict]`
    Возвращает {issue_id: {hours: float, today: bool}}.
  - `fetch_daily_summary(days: int = 3) -> list[dict]`
    Возвращает список {date, total, entries} за последние N дней — быстрый прямой запрос.

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
- `_EMAIL_RE = re.compile('_?[a-zA-Z0-9._+%-]+@[a-zA-Z0-9._-]+\\.[a-zA-Z0-9._-]+_?')`
- `_REAL_TAGS = {'a', 'b', 'i', 'u', 's', 'p', 'br', 'hr', 'em', 'strong', 'code', 'pre', 'span', 'div', 'ul', 'ol'…`
- `_ANGLE_RE = re.compile('</?([a-zA-Z][a-zA-Z0-9_-]*)(?:\\s[^>]*)?>|<([a-zA-Z][a-zA-Z0-9_-]*)>')`
- `_NOTEXTILE_RE = re.compile('<notextile>(.*?)</notextile>', re.DOTALL)`
- `_QUOTE_BLOCK_RE = re.compile('((?:^> ?.*$\\n?)+)', re.MULTILINE)`
- `_GROUP_DEFS = [('в_работе', 'В работе', lambda s: 'работ' in s), ('на_ревью', 'На ревью', lambda s: 'ревью' in s …`
- `_MR_URL_RE = re.compile('(https?://\\S+/merge_requests/(\\d+))\\s*[-–]?\\s*(stage|master)?', re.IGNORECASE)`
- `_TODO_PRIORITY_ORDER = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}`
- `_TODO_STATUS_ORDER = {'in_progress': 0, 'open': 1}`
- `_LABEL_Q_RE = re.compile('\\[Q', re.IGNORECASE)`
- `_LABEL_AI_RE = re.compile('\\[ai\\]', re.IGNORECASE)`
- `_PRIORITY_ORDER = {'критичный баг': 0, 'недельный фокус': 1, 'высокий': 2, 'high': 2, 'нормальный': 3, 'normal': 3, '…`
- `_ATTR_LABELS: dict[str, str] = {'status_id': 'Статус', 'assigned_to_id': 'Назначена', 'priority_id': 'Приоритет', 'done_ratio': 'Г…`

Классы:

- `_BearerAuthASGIApp`
  Оборачивает ASGI-приложение проверкой заголовка Authorization: Bearer <token>.
  Методы:
  - `__init__(self, inner_app, token: str)`
    Нет докстринга.
  - `__call__(self, scope, receive, send)`
    Нет докстринга.

Функции:

- `_lifespan(_: FastAPI)`
  Нет докстринга.

- `_fix_spans(html: str) -> str`
  Нет докстринга.

- `_escape_template_vars(text: str) -> str`
  Экранирует <placeholder> которые не являются HTML-тегами.

- `_render(text: str | None) -> str`
  Нет докстринга.

- `_calc_workdays(due_str: str | None) -> int | None`
  Нет докстринга.

- `_parse_mrs(custom_fields: list) -> list[dict]`
  Нет докстринга.

- `_enrich(issue: dict, spent_map: dict | None = None) -> dict`
  Нет докстринга.

- `_group_issues(issues: list) -> list`
  Нет докстринга.

- `_group_todos(todos: list) -> list`
  Группирует задачи проекта по секциям (bug/feat/ref/ques, всегда все
  четыре) и делит каждую на открытые/закрытые. Открытые сортируются по
  приоритету, внутри приоритета — in_progress выше open (как в скилле `todo`).

- `_detect_label(subject: str) -> str`
  Нет докстринга.

- `_issue_sort_key(issue: dict) -> tuple`
  Нет докстринга.

- `index(request: Request)`
  Нет докстринга.

- `api_closed(request: Request)`
  Закрытые задачи (lazy) — рендерит фрагмент HTML секции «Закрытые».
  
  Грузится по клику «Показать закрытые», а не при открытии страницы: выборка
  дорогая (батчи по всем работанным id), поэтому вынесена из GET /. Результат
  кэшируется в RedmineClient._closed_cache на 5 минут.

- `api_spent()`
  Нет докстринга.

- `api_mrs(issue_ids: str = '')`
  Нет докстринга.

- `issue_by_id(request: Request, issue_id: int)`
  Нет докстринга.

- `issue_journals(issue_id: int)`
  Нет докстринга.

- `attachment_thumbnail(attachment_id: int)`
  Нет докстринга.

- `attachment_download(attachment_id: int, filename: str = '')`
  Нет докстринга.

- `_get_redmine_meta() -> dict`
  Нет докстринга.

- `_resolve_attr(name: str, value: str | None) -> str | None`
  Нет докстринга.

- `_build_attr_changes(details: list[dict]) -> list[dict]`
  Нет докстринга.

- `avatar(user_id: int)`
  Нет докстринга.

- `projects_index(request: Request)`
  Нет докстринга.

- `project_detail(request: Request, slug: str)`
  Нет докстринга.

- `create_project_todo(slug: str, request: Request)`
  Нет докстринга.

- `update_todo_status(slug: str, todo_id: int, request: Request)`
  Нет докстринга.

- `update_todo_priority(slug: str, todo_id: int, request: Request)`
  Нет докстринга.

- `add_todo_subitem(slug: str, todo_id: int, request: Request)`
  Нет докстринга.

- `edit_project_todo(slug: str, todo_id: int, request: Request)`
  Нет докстринга.

- `set_todo_placement_approved(slug: str, todo_id: int, request: Request)`
  Нет докстринга.

- `delete_project_todo(slug: str, todo_id: int)`
  Нет докстринга.

- `health()`
  Нет докстринга.