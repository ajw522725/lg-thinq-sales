# LG ThinQ-Sales API

FastAPI 기반 Phase 0 + Phase 1 데모 백엔드입니다. 실제 크롤링, 실제 LLM API, 실제 외부 API는 아직 연결하지 않았고 `data/demo/voc_records.json`을 사용해 DB 기반 로컬 end-to-end 흐름을 제공합니다.

## 실행

Docker가 있으면 PostgreSQL을 Docker Compose로 실행합니다. Docker가 없으면 Homebrew PostgreSQL을 사용할 수 있습니다.

```bash
cd /Users/jwa/lg-thinq-sales
docker compose up -d postgres
```

macOS 로컬 PostgreSQL 방식:

```bash
brew install postgresql@16
brew services start postgresql@16
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
psql -d postgres -c "CREATE ROLE lg_thinq LOGIN PASSWORD 'lg_thinq';"
createdb -O lg_thinq lg_thinq_sales
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE lg_thinq_sales TO lg_thinq;"
psql -d lg_thinq_sales -c "GRANT ALL ON SCHEMA public TO lg_thinq;"
```

기본 연결 주소:

```bash
DATABASE_URL=postgresql+psycopg://lg_thinq:lg_thinq@localhost:5432/lg_thinq_sales
DEMO_MODE=true
LLM_PROVIDER=demo
DB_PIPELINE_PROVIDER=legacy
```

`DB_PIPELINE_PROVIDER=legacy`는 기존 DB seed/ingestion용 rule-based pipeline을 사용합니다. `DB_PIPELINE_PROVIDER=yuna`로 실행하면 `services/nlp`, `services/scoring`, `services/insights`의 통합 pipeline으로 분석 결과를 DB에 저장합니다.

백엔드를 실행합니다.

```bash
cd /Users/jwa/lg-thinq-sales
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api uvicorn app.main:app --reload --port 8000
```

yuna pipeline 검증 실행:

```bash
DB_PIPELINE_PROVIDER=yuna \
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api \
  uvicorn app.main:app --reload --port 8000
```

API 서버만 최소 실행할 때는 `pip install -r apps/api/requirements.txt`를 사용할 수 있습니다. collector runner까지 확인하려면 루트 `requirements.txt`를 설치하세요.

## Demo seed

서버 실행 후 다음 endpoint를 호출하면 demo data를 다시 적재합니다.

```bash
curl -X POST "http://localhost:8000/api/v1/demo/seed?reset=true"
```

## Collector ingestion

팀원 2의 collector 결과는 다음 endpoint로 넣을 수 있습니다.

```bash
curl -X POST "http://localhost:8000/api/v1/ingestion/vocs" \
  -H "Content-Type: application/json" \
  -d '[{"source":"Danawa","external_id":"manual-001","title":"VOC","content":"I want to buy LG air purifier because fine dust is bad.","url":"https://example.com","published_at":"2026-05-20T09:10:00Z","product_category":"Air Purifier","region":"Seoul","engagement":12}]'
```

collector runner 결과를 바로 DB pipeline에 넣을 때는 루트에서 다음 스크립트를 실행합니다.

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
PYTHONPATH=/Users/jwa/lg-thinq-sales \
  python scripts/run_collector_ingestion_demo.py --keyword "LG 공기청정기" --max 2 --limit 5 --reset
```

API 서버가 꺼져 있을 때 매핑만 확인하려면 `--dry-run`을 붙입니다.

## Endpoint

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/vocs`
- `GET /api/v1/vocs/stats`
- `GET /api/v1/lead-scores`
- `GET /api/v1/insights`
- `POST /api/v1/demo/seed`
- `POST /api/v1/ingestion/vocs`
- `POST /api/v1/nlp/analyze`
- `POST /api/v1/pipeline/run`
- `GET /api/v1/demo/run`

## NLP / Pipeline 단독 확인

```bash
curl -X POST "http://localhost:8000/api/v1/nlp/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text":"미세먼지가 심해서 LG 공기청정기를 구매하려고 합니다.","source":"naver_blog","language":"ko","product_category":"air_purifier","product_keyword":"LG 퓨리케어","engagement":12,"platform_meta":{"view_count":1200}}'

curl -X POST "http://localhost:8000/api/v1/pipeline/run" \
  -H "Content-Type: application/json" \
  -d '{"text":"미세먼지가 심해서 LG 공기청정기를 구매하려고 합니다.","source":"naver_blog","language":"ko","product_category":"air_purifier","product_keyword":"LG 퓨리케어","engagement":12,"platform_meta":{"view_count":1200}}'

curl "http://localhost:8000/api/v1/demo/run"
```

## Collector demo 확인

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
USE_DEMO_DATA=true PYTHONPATH=/Users/jwa/lg-thinq-sales \
  python -m services.collectors.runner --keyword "LG 공기청정기" --max 2 --no-save
```

현재 demo 기준 확인값:

```text
raw 42건
processed 약 41건
Danawa / Reddit / NaverBlog / YouTube demo source 정상 실행
```

## TablePlus 접속

```text
Connection type: PostgreSQL
Name: LG ThinQ Sales Local
Host: localhost
Port: 5432
User: lg_thinq
Password: lg_thinq
Database: lg_thinq_sales
SSL Mode: Disable
```

## 검증

```bash
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api python -m compileall apps/api/app services scripts
curl http://localhost:8000/api/v1/dashboard/summary
```

Codex 최종 확인 결과:

```text
compileall: 통과
API smoke test: health, seed, dashboard, vocs, voc stats, lead scores, insights, nlp, pipeline, demo run 모두 200
collector demo runner: 통과
collector demo output -> ingestion endpoint -> DB 저장: 통과
```
