# Release-hour import (DatsSol)

Цель: зафиксировать официальный релизный пакет в одном месте без догадок о механике.

## 1) Куда класть материалы

Используем только `docs/input/datssol_imports/`.

Рекомендуемая структура на релизный тег (UTC), например `20260417T180000Z`:
- `{tag}_event_notes.md` — краткий текстовый конспект официальных правил;
- `{tag}_openapi.json` — официальный OpenAPI/Swagger snapshot;
- `{tag}_examples.json` — примеры request/response;
- `{tag}_extra_notes.md` — скриншоты, спорные пункты, ручные заметки.

## 2) Команды сразу после публикации

```bash
python -m scripts.prepare_datssol_import --tag 20260417T180000Z
python -m scripts.check_contract_consistency
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

После этого обновите:
- `docs/contract/current_truth_table.md`
- `docs/contract/current_truth_table.yaml`
- `docs/contract/open_questions.md`

## 3) Минимум перед первым live submit

Перед первым live-запуском все условия должны быть выполнены:
1. нет угадываний `games/datssol` — только официальные поля/эндпоинты;
2. contract docs синхронизированы с импортированными файлами;
3. smoke checks (`pytest`, `ruff`, `mypy`) зелёные;
4. replay пишет метаданные запроса/результата для дебага;
5. fallback-логика активна и детерминирована.
