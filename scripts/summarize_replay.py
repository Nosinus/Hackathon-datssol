from __future__ import annotations

import argparse
import json
from pathlib import Path

from datsteam_core.replay.summary import summarize_replay_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize replay directory")
    parser.add_argument("replay_dir", type=Path, nargs="?", default=Path("logs/replay"))
    args = parser.parse_args()
    summary = summarize_replay_dir(args.replay_dir)
    print(json.dumps(summary.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
