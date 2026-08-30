-- Project seed for the "briefing" DB (the "Projects" tab + the MCP todos).
-- Runs on EVERY deploy (migrations/apply.sh): idempotent —
-- INSERT ... ON DUPLICATE KEY UPDATE keeps the project list in the DB equal to the seed.
-- The schema DDL lives separately: migrations/001_baseline.sql + later migrations.
-- SET NAMES is mandatory — without it the mysql CLI may mangle the non-ASCII text below.

SET NAMES utf8mb4;

INSERT INTO projects (slug, title, local_path, contour, is_hub) VALUES
    ('meteopavel', 'meteopavel.space — Static Site Generator', '/Users/Work/PycharmProjects/meteopavel', 'public', FALSE),
    ('briefing', 'Briefing', '/Users/Work/PycharmProjects/Briefing', 'personal', TRUE),
    ('django_edu_multisite', 'Django EDU Multisite (VOA)', '/Users/Work/PycharmProjects/Django_EDU_Multisite', 'public', FALSE),
    ('home_router_panel', 'Home Router Panel', '/Users/Work/PycharmProjects/Home_Router_Panel', 'personal', FALSE),
    ('llm_server', 'LLM Server', '/Users/Work/PycharmProjects/LLM_Server', 'personal', FALSE),
    ('python_practice_hub', 'Python Practice Hub — web code grader', '/Users/Work/PycharmProjects/Python_Practice_Hub', 'public', FALSE),
    ('home_chores', 'Home chores', '/Users/Work/PycharmProjects/home_chores', 'personal', FALSE)
ON DUPLICATE KEY UPDATE title = VALUES(title), local_path = VALUES(local_path), is_hub = VALUES(is_hub);
