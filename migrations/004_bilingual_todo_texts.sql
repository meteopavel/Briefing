-- Двуязычные тексты задач (feat.27): title → title_ru/title_en,
-- text → text_ru/text_en. Обе версии вводятся вручную (форма правки);
-- однострочные клиенты (MCP) кладут текст в колонку его языка.
-- Бэкфилл: текст с кириллицей → ru-колонка, без кириллицы → en-колонка;
-- недостающая версия остаётся NULL, пока её не заполнят. UPDATE-шаги
-- идемпотентны (перетирают тем же значением), DDL — как в 002/003, одним
-- прогоном до конца.
SET NAMES utf8mb4;

ALTER TABLE todos
    ADD COLUMN title_ru TEXT NULL AFTER placement_approved,
    ADD COLUMN title_en TEXT NULL AFTER title_ru;

UPDATE todos SET title_ru = title WHERE title REGEXP '[А-Яа-яЁё]';
UPDATE todos SET title_en = title WHERE title_ru IS NULL;

ALTER TABLE todo_subitems
    ADD COLUMN text_ru TEXT NULL AFTER kind,
    ADD COLUMN text_en TEXT NULL AFTER text_ru;

UPDATE todo_subitems SET text_ru = text WHERE text REGEXP '[А-Яа-яЁё]';
UPDATE todo_subitems SET text_en = text WHERE text_ru IS NULL;

ALTER TABLE todos DROP COLUMN title;
ALTER TABLE todo_subitems DROP COLUMN text;
