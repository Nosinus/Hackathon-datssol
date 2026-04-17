# Backlog

## P0
- Подключить policy disagreement signal в replay parser extras из реальных тренировочных данных.
- Добавить regression fixtures для anomaly/export контуров replay analytics.
- Добавить p99 latency и histogram buckets в replay summary/analytics.
- Добавить CI-проверку, что `docs/input/datssol_imports/` содержит manifest после release-hour импорта.

## P1
- Улучшить benchmark contour: optional per-endpoint scenario profile (scan/command/register).
- Добавить CLI команду для пакетного сравнения N запусков по mode/environment.
- Расширить training playbook чеклистами для night/finals handoff.

## P2
- Импортировать официальный DatsSol OpenAPI и реализовать concrete adapter после релиза.
- Добавить datssol-specific legal generator в offline lab без нарушения generic boundary.
