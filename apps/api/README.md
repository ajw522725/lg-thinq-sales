# LG ThinQ-Sales API

FastAPI 기반 Phase 0 + Phase 1 데모 백엔드입니다. 실제 크롤링, 실제 LLM API, 실제 외부 API는 아직 연결하지 않았고 `data/demo/voc_records.json`을 사용해 DB 기반 로컬 end-to-end 흐름을 제공합니다.

## 실행

```bash
cd /Users/jwa/lg-thinq-sales
docker compose up -d postgres
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api uvicorn app.main:app --reload --port 8000
```

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

## Endpoint

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/vocs`
- `GET /api/v1/vocs/stats`
- `GET /api/v1/lead-scores`
- `GET /api/v1/insights`
- `POST /api/v1/demo/seed`
- `POST /api/v1/ingestion/vocs`

## 검증

```bash
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api python -m compileall apps/api/app services
curl http://localhost:8000/api/v1/dashboard/summary
```
