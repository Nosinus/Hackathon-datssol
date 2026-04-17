# DatsSol release-hour import (first 60 minutes)

## 1) Куда класть официальные материалы

Все новые материалы складываем только в `docs/input/datssol_imports/`:

- `rules/` — текст правил, PDF-конспект, extracted markdown;
- `openapi/` — OpenAPI/Swagger JSON или YAML;
- `examples/` — JSON request/response примеры;
- `screenshots/` — скриншоты схем/таблиц/таймингов из официальных материалов;
- `notes/` — короткие заметки/уточнения от команды.

Не добавляем speculative код в `src/games/datssol/` до фиксации контракта.

## 2) Что запустить сразу после появления доков

```bash
python -m scripts.prepare_datssol_import --tag 20260417T180000Z
python -m scripts.check_contract_consistency
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

`prepare_datssol_import` создаёт папки и чеклист-манифест с ожидаемыми файлами.

## 3) Минимальный gate перед первым live submit

Перед первой live-отправкой обязательно:

1. `docs/contract/current_truth_table.md` и `.yaml` обновлены под новые источники.
2. Добавлены базовые фикстуры в `tests/fixtures/datssol/` из официальных примеров.
3. Нет guessed DatsSol mechanics в runtime.
4. Проходят проверки:
   - `pytest -q`
   - `ruff check src tests scripts`
   - `mypy src`
5. Dry-run цикл сохраняет replay с метаданными (reason/success/timestamp/run metadata).
