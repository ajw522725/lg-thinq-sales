# migrations

PostgreSQL 스키마 마이그레이션 파일을 두는 위치입니다.

현재 MVP는 Alembic으로 초기 DB schema를 관리합니다.

주요 파일:

- `env.py`: FastAPI 설정의 `DATABASE_URL`을 읽어 migration을 실행합니다.
- `versions/20260528_0001_initial_schema.py`: Phase 1 DB 초기 schema입니다.

실행:

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api \
  alembic upgrade head
```

기존 로컬 DB가 이미 `Base.metadata.create_all()`로 만들어진 상태라면, 같은 테이블을 다시 만들지 않고 Alembic 버전만 표시합니다.

```bash
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api \
  alembic stamp head
```

새 migration 생성:

```bash
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api \
  alembic revision --autogenerate -m "변경 내용"
```
