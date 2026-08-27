-- Сид проектов для БД "briefing" (вкладка «Проекты» + MCP-тудушки).
-- Прогоняется при КАЖДОМ деплое (migrations/apply.sh): идемпотентен —
-- INSERT ... ON DUPLICATE KEY UPDATE держит список проектов в БД равным сиду.
-- DDL схемы живёт отдельно: migrations/001_baseline.sql + последующие миграции.
-- SET NAMES обязателен — без него mysql CLI может побить кириллицу в INSERT ниже.

SET NAMES utf8mb4;

INSERT INTO projects (slug, title, local_path, contour, is_hub) VALUES
    ('meteopavel', 'meteopavel.space — Static Site Generator', '/Users/Work/PycharmProjects/meteopavel', 'public', FALSE),
    ('briefing', 'Briefing', '/Users/Work/PycharmProjects/Briefing', 'personal', TRUE),
    ('django_edu_multisite', 'Django EDU Multisite (VOA)', '/Users/Work/PycharmProjects/Django_EDU_Multisite', 'public', FALSE),
    ('home_router_panel', 'Home Router Panel', '/Users/Work/PycharmProjects/Home_Router_Panel', 'personal', FALSE),
    ('llm_server', 'LLM Server', '/Users/Work/PycharmProjects/LLM_Server', 'personal', FALSE),
    ('python_practice_hub', 'Python Practice Hub — веб-грейдер кода', '/Users/Work/PycharmProjects/Python_Practice_Hub', 'public', FALSE),
    ('home_chores', 'Домашние дела', '/Users/Work/PycharmProjects/home_chores', 'personal', FALSE)
ON DUPLICATE KEY UPDATE title = VALUES(title), local_path = VALUES(local_path), is_hub = VALUES(is_hub);
