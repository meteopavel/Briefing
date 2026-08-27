-- Сид проектов для БД "briefing" (вкладка «Проекты» + MCP-тудушки).
-- Прогоняется при КАЖДОМ деплое (migrations/apply.sh): идемпотентен —
-- INSERT ... ON DUPLICATE KEY UPDATE держит список проектов в БД равным сиду.
-- DDL схемы живёт отдельно: migrations/001_baseline.sql + последующие миграции.
-- SET NAMES обязателен — без него mysql CLI может побить кириллицу в INSERT ниже.

SET NAMES utf8mb4;

INSERT INTO projects (slug, title, local_path, contour) VALUES
    ('meteopavel', 'meteopavel.space — Static Site Generator', '/Users/Work/PycharmProjects/meteopavel', 'public'),
    ('briefing', 'Briefing', '/Users/Work/PycharmProjects/Briefing', 'personal'),
    ('django_edu_multisite', 'Django EDU Multisite (VOA)', '/Users/Work/PycharmProjects/Django_EDU_Multisite', 'public'),
    ('home_router_panel', 'Home Router Panel', '/Users/Work/PycharmProjects/Home_Router_Panel', 'personal'),
    ('llm_server', 'LLM Server', '/Users/Work/PycharmProjects/LLM_Server', 'personal'),
    ('python_practice_hub', 'Python Practice Hub — веб-грейдер кода', '/Users/Work/PycharmProjects/Python_Practice_Hub', 'public'),
    ('home_chores', 'Домашние дела', '/Users/Work/PycharmProjects/home_chores', 'personal')
ON DUPLICATE KEY UPDATE title = VALUES(title), local_path = VALUES(local_path);
