-- Схема БД "briefing" для вкладки «Проекты» (тудушки проектов).
-- Применяется вручную: mysql -h HOST -u USER -p briefing < schema.sql
-- SET NAMES обязателен — без него mysql CLI может побить кириллицу в INSERT ниже.

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

INSERT INTO projects (slug, title, local_path, contour) VALUES
    ('meteopavel', 'meteopavel.space — Static Site Generator', '/Users/Work/PycharmProjects/meteopavel', 'public'),
    ('briefing', 'Briefing', '/Users/Work/PycharmProjects/Briefing', 'personal'),
    ('django_edu_multisite', 'Django EDU Multisite (VOA)', '/Users/Work/PycharmProjects/Django_EDU_Multisite', 'public'),
    ('home_router_panel', 'Home Router Panel', '/Users/Work/PycharmProjects/Home_Router_Panel', 'personal'),
    ('llm_server', 'LLM Server', '/Users/Work/PycharmProjects/LLM_Server', 'personal'),
    ('python_practice_hub', 'Python Practice Hub — веб-грейдер кода', '/Users/Work/PycharmProjects/Python_Practice_Hub', 'public'),
    ('home_chores', 'Домашние дела', '/Users/Work/PycharmProjects/home_chores', 'personal')
ON DUPLICATE KEY UPDATE title = VALUES(title), local_path = VALUES(local_path);
