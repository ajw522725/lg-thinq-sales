from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_demo_raw_documents(data_path: Path) -> list[dict[str, Any]]:
    with data_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Demo VOC data must be a list.")

    return records
