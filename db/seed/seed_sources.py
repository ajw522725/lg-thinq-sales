"""
DB Source 테이블 seed 스크립트.
사용법: python db/seed/seed_sources.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from db.database import SessionLocal, init_db
from db.models import Source


def run():
    init_db()
    db = SessionLocal()

    seed_path = Path(__file__).parent / "sources.json"
    sources_data = json.loads(seed_path.read_text(encoding="utf-8"))

    inserted, skipped = 0, 0
    for item in sources_data:
        exists = db.query(Source).filter_by(name=item["name"]).first()
        if exists:
            skipped += 1
            continue
        db.add(Source(name=item["name"], type=item["type"], status=item["status"]))
        inserted += 1

    db.commit()
    db.close()
    print(f"Seed 완료 — 삽입: {inserted}건 / 스킵(중복): {skipped}건")


if __name__ == "__main__":
    run()
