#!/usr/bin/env bash
#===============================================================================
# Раннер SQL-миграций БД briefing.
#
# Гоняется на сервере из deploy-local.sh ДО restart сервиса. MySQL доступен
# только через docker exec (mysql-клиента на хосте нет), поэтому все вызовы —
# через контейнер (по умолчанию edu_mysql, переопределяется MYSQL_CONTAINER).
#
# Как это работает:
#   - файлы migrations/NNN_имя.sql применяются по порядку номеров; применённые
#     зафиксированы в таблице schema_migrations и повторно не гоняются;
#   - миграция записывается в schema_migrations ТОЛЬКО после успешного
#     применения: упавший файл повторится со следующего деплоя. DDL в MySQL
#     не транзакционный, поэтому миграции пишем маленькими и/или идемпотентными;
#   - применённые миграции не редактируем — новая правка схемы = новый файл
#     со следующим номером;
#   - после миграций всегда прогоняется сид проектов (seed.sql) — он
#     идемпотентен (ON DUPLICATE KEY UPDATE) и держит список проектов в БД
#     равным сиду.
#===============================================================================

set -euo pipefail

MIGRATIONS_DIR="$(cd "$(dirname "$0")" && pwd)"
SEED_FILE="${MIGRATIONS_DIR}/../app/services/projects/seed.sql"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-edu_mysql}"
MYSQL_DB="${MYSQL_DATABASE:-briefing}"

mysql_exec() {
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DB" "$@"
}

mysql_pipe() {
    docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DB"
}

mysql_exec -e "
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version INT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"

APPLIED="$(mysql_exec -sN -e "SELECT version FROM schema_migrations" | tr -d '\r' | sort -n)"

for f in "$MIGRATIONS_DIR"/[0-9][0-9][0-9]_*.sql; do
    [[ -f "$f" ]] || continue
    name="$(basename "$f")"
    version=$((10#${name%%_*}))
    if grep -qx "$version" <<<"$APPLIED"; then
        echo "⏭️  Миграция $name уже применена, пропуск."
        continue
    fi
    echo "🔁 Миграция $name..."
    mysql_pipe < "$f"
    mysql_exec -e "INSERT INTO schema_migrations (version, name) VALUES ($version, '$name')"
    echo "✅ Миграция $name применена."
done

mysql_pipe < "$SEED_FILE"
echo "✅ Сид проектов применён (seed.sql)."
