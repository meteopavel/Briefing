-- Хаб-проект (feat.17): флаг is_hub на projects. Хаб — узловой проект, куда
-- ложатся кросс-проектные фичи (общие задачи, мониторинг). Кто именно хаб,
-- определяет сид seed.sql (ON DUPLICATE KEY UPDATE is_hub=VALUES(is_hub)) —
-- миграция только добавляет колонку со значением по умолчанию FALSE.
SET NAMES utf8mb4;

ALTER TABLE projects ADD COLUMN is_hub BOOLEAN NOT NULL DEFAULT FALSE AFTER contour;
