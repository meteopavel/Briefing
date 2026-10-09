-- Состояние пингов крит-багов Max-ботом (feat.30): вотчер поллинга Redmine
-- отмечает, какие задачи уже были в критическом приоритете, чтобы пинговать
-- один раз на «вход» в крит-состояние (повтор — после снятия и возврата).
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS max_ping_state (
    issue_id INT PRIMARY KEY,
    was_critical TINYINT(1) NOT NULL DEFAULT 0,
    pinged_at TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
