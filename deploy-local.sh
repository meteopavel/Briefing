#!/bin/bash
set -euo pipefail

NON_INTERACTIVE=false
COMMIT_MESSAGE_ARG=''
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[$i]}" in
    --non-interactive) NON_INTERACTIVE=true ;;
    --message|-m) COMMIT_MESSAGE_ARG="${args[$((i+1))]}"; i=$((i+1)) ;;
  esac
done

REPO_REQUIRED_REMOTE='git@github.com:meteopavel/Chronicle_Reporting_Automation.git'
BRANCH_NAME='main'
REPO_ROOT="$(git rev-parse --show-toplevel)"
ENV_FILE="${REPO_ROOT}/.env"

LOCAL_SECURE_DIR='.local_secure'
ARCHIVE_DIR='secure'
ARCHIVE_NAME='sensitive_bundle.7z'
ARCHIVE_PATH="${ARCHIVE_DIR}/${ARCHIVE_NAME}"

# ================= ФУНКЦИИ =================

get_env() {
  local var_name="$1"
  local env_file="$2"

  if [[ ! -f "$env_file" ]]; then
    echo ""
    return
  fi

  grep -E "^${var_name}=" "$env_file" 2>/dev/null | head -1 | cut -d'=' -f2-
}

require_env() {
  local var_name="$1"
  local var_value="$2"

  if [[ -z "$var_value" ]]; then
    echo "❌ Ошибка: переменная ${var_name} не найдена или пуста в ${ENV_FILE}"
    exit 1
  fi
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "❌ Ошибка: команда '${command_name}' не найдена."
    exit 1
  fi
}

update_project_passport() {
  echo '🪪 Обновляем паспорт проекта...'

  local tools_dir
  tools_dir="$(dirname "${REPO_ROOT}")/meteopavel/tools"

  (
    cd "${REPO_ROOT}"
    .venv/bin/python "${tools_dir}/build_project_passport.py" --project-root .
    .venv/bin/python "${tools_dir}/extract_api_map.py" app --project-root .
  )

  echo '✅ Паспорт проекта обновлён.'
}

# ================= ПРОВЕРКИ =================

echo '🔍 Проверяем, что мы внутри git-репозитория...'
git rev-parse --is-inside-work-tree >/dev/null 2>&1

echo '🔍 Проверяем remote origin...'
REMOTE_URL="$(git remote get-url origin)"
echo "   origin = ${REMOTE_URL}"

if [[ "${REMOTE_URL}" != "${REPO_REQUIRED_REMOTE}" ]]; then
  echo '❌ Ошибка: origin указывает не на ожидаемый GitHub-репозиторий.'
  echo "Ожидалось: ${REPO_REQUIRED_REMOTE}"
  exit 1
fi

echo '🔍 Проверяем обязательные команды...'
require_command 7z
require_command rsync
require_command sshpass
require_command python

echo '🔍 Загружаем переменные из .env...'
ARCHIVE_PASSWORD="$(get_env "ARCHIVE_PASSWORD" "$ENV_FILE")"
SECURE_RSYNC_USER="$(get_env "SECURE_RSYNC_USER" "$ENV_FILE")"
SECURE_RSYNC_HOST="$(get_env "SECURE_RSYNC_HOST" "$ENV_FILE")"
SECURE_RSYNC_PATH="$(get_env "SECURE_RSYNC_PATH" "$ENV_FILE")"
SECURE_RSYNC_PASSWORD="$(get_env "SECURE_RSYNC_PASSWORD" "$ENV_FILE")"

require_env "ARCHIVE_PASSWORD" "$ARCHIVE_PASSWORD"
require_env "SECURE_RSYNC_USER" "$SECURE_RSYNC_USER"
require_env "SECURE_RSYNC_HOST" "$SECURE_RSYNC_HOST"
require_env "SECURE_RSYNC_PATH" "$SECURE_RSYNC_PATH"
require_env "SECURE_RSYNC_PASSWORD" "$SECURE_RSYNC_PASSWORD"

if [[ ! -d "${LOCAL_SECURE_DIR}" ]]; then
  echo "❌ Ошибка: папка ${LOCAL_SECURE_DIR} не найдена."
  exit 1
fi

mkdir -p "${ARCHIVE_DIR}"

# ================= АРХИВАЦИЯ =================

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "❌ Ошибка: файл ${ENV_FILE} не найден."
  exit 1
fi

if [[ ! -f "${REPO_ROOT}/TODO" ]]; then
  echo "❌ Ошибка: файл TODO не найден в корне проекта."
  exit 1
fi

if [[ -f "${ARCHIVE_PATH}" ]]; then
  echo "🗑 Удаляем старый архив: ${ARCHIVE_PATH}"
  rm -f "${ARCHIVE_PATH}"
fi

echo '🔐 Создаём зашифрованный архив (.local_secure/, .env, TODO, CLAUDE.md)...'
(
  cd "${REPO_ROOT}"
  7z a -p"${ARCHIVE_PASSWORD}" -mhe=on "${ARCHIVE_PATH}" "${LOCAL_SECURE_DIR}" ".env" "TODO" "CLAUDE.md"
)
echo '✅ Архив успешно создан.'

# ================= RSYNC =================

echo '📤 Отправляем архив на backup-сервер...'
export SSHPASS="${SECURE_RSYNC_PASSWORD}"
rsync -avz --progress \
  --rsh="sshpass -e ssh" \
  "${ARCHIVE_PATH}" "${SECURE_RSYNC_USER}@${SECURE_RSYNC_HOST}:${SECURE_RSYNC_PATH}"

echo '✅ Архив успешно отправлен на сервер.'

# ================= PROJECT PASSPORT =================

update_project_passport

# ================= GIT =================

echo
echo '📋 Текущий git status:'
git status --short
echo

DEFAULT_COMMIT_MESSAGE='Update project'

if [[ -n "$COMMIT_MESSAGE_ARG" ]]; then
  COMMIT_MESSAGE="$COMMIT_MESSAGE_ARG"
elif [[ "$NON_INTERACTIVE" == true ]]; then
  COMMIT_MESSAGE="$DEFAULT_COMMIT_MESSAGE"
  echo "ℹ️ Режим без ввода: используется сообщение по умолчанию: ${COMMIT_MESSAGE}"
else
  read -r -p '✍️ Введите сообщение коммита (Enter = по умолчанию): ' COMMIT_MESSAGE
  COMMIT_MESSAGE="${COMMIT_MESSAGE:-$DEFAULT_COMMIT_MESSAGE}"
fi

echo "📝 Будет использовано сообщение коммита: ${COMMIT_MESSAGE}"

echo '➕ Добавляем изменения в git...'
git add .

if git diff --cached --quiet; then
  echo 'ℹ️ Нет изменений для коммита.'
  exit 0
fi

echo '📝 Создаём коммит...'
git commit -m "${COMMIT_MESSAGE}"

echo "🚀 Выполняем push в origin/${BRANCH_NAME}..."
git push origin "${BRANCH_NAME}"

echo '🎉 Готово: код отправлен на GitHub, архив сохранён локально и отправлен на backup-сервер, паспорт проекта обновлён.'