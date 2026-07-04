from __future__ import annotations

import json
from pathlib import Path
import sys

HELPERS_DIR = Path(__file__).resolve().parents[1]
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from orbit_context import build_logger, default_log_file, load_context


def main() -> None:
    context = load_context()
    logger = build_logger(__file__)
    logger.info("Context dump started for '%s'", context.title or context.item_id or "unknown item")

    output_path = default_log_file(__file__).with_name("orbit_context_dump.json")
    output_path.write_text(
        json.dumps(context.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote context snapshot to %s", output_path)


if __name__ == "__main__":
    main()

