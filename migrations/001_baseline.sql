-- Базовая миграция: полная схема БД "briefing" (тудушки проектов: вкладка
-- «Проекты» + MCP-сервер briefing-todos).
-- На существующей БД — no-op (CREATE TABLE IF NOT EXISTS), на свежей —
-- создаёт всё с нуля. Изменения схемы дальше — только НОВЫМИ миграциями
-- (002_*.sql и т.д.); применённые миграции не редактируются.
-- SET NAMES обязателен — без него mysql CLI может побить кириллицу.

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    slug VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    local_path VARCHAR(500),
    contour VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS todos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    section ENUM('bug', 'feat', 'ref', 'ques') NOT NULL,
    number INT NOT NULL,
    status ENUM('open', 'in_progress', 'done', 'wontdo') NOT NULL DEFAULT 'open',
    priority ENUM('high', 'medium', 'low') NOT NULL,
    placement_approved BOOLEAN NOT NULL DEFAULT FALSE,
    title TEXT NOT NULL,
    closed_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_project_section_number (project_id, section, number),
    FOREIGN KEY (project_id) REFERENCES projects(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS todo_subitems (
    id INT PRIMARY KEY AUTO_INCREMENT,
    todo_id INT NOT NULL,
    kind ENUM('requirement', 'context') NOT NULL,
    text TEXT NOT NULL,
    position INT NOT NULL DEFAULT 0,
    FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
