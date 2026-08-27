-- Приоритет critical выше high (feat.10).
-- Расширение ENUM: значения существующих строк не меняются, старый код,
-- знающий только high/medium/low, работает с расширенным ENUM без изменений.
SET NAMES utf8mb4;

ALTER TABLE todos MODIFY COLUMN priority ENUM('critical', 'high', 'medium', 'low') NOT NULL;
