# LG ThinQ-Sales

LG ThinQ-Sales는 VOC, SNS, 공공·외부 데이터를 통합 수집·분석하여 고객 니즈, 구매 가능성, 불만, 외부 환경 맥락을 파악하고 LLM 기반 영업 전략 인사이트를 생성하는 AI 기반 영업 전략 운영 플랫폼입니다.

이번 구현은 Phase 0 + Phase 1 기반 구축입니다. 실제 크롤링, 실제 LLM API, 실제 외부 API 연동보다 먼저 로컬에서 실행 가능한 MVP 골격과 demo mode 기반 end-to-end 흐름을 제공합니다.

## 협업 역할분담

팀원과 각자의 로컬 AI 에이전트는 작업 전 루트의 `AGENTS.md`와 `docs/TEAM_ROLES.md`를 먼저 확인하세요.

| GitHub ID | 역할 | 주 담당 영역 |
|---|---|---|
| `ajw522725` | 총책임 / PM / Backend Integration Lead | 전체 아키텍처, API 계약, DB, Docker, 통합 테스트 |
| `wldnjsrla085` | Data Collection / Dataset Lead | VOC/SNS 수집, source metadata, demo dataset |
| `yuna0822` | AI/NLP / Insight Lead | NLP 분석, Lead Score, LLM prompt, 전략 인사이트 |
| `sksmsdngml-ui` | Frontend / Demo UX Lead | Next.js dashboard, chart, table, 발표 UI |

## 기술 스택

- Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts
- Backend: Python, FastAPI, Pydantic
- Database: PostgreSQL, SQLAlchemy
- Local Infra: Docker Compose

## 프로젝트 구조

```text
lg-thinq-sales/
├─ apps/
│  ├─ web/
│  └─ api/
├─ packages/
│  ├─ shared/
│  └─ prompts/
├─ services/
│  ├─ collectors/
│  ├─ preprocessing/
│  ├─ nlp/
│  ├─ scoring/
│  ├─ context/
│  └─ insights/
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ demo/
├─ db/
│  ├─ migrations/
│  └─ seed/
├─ docs/
└─ docker-compose.yml
```

## 백엔드 실행

PostgreSQL을 먼저 실행합니다.

```bash
cd /Users/jwa/lg-thinq-sales
docker compose up -d postgres
```

백엔드를 실행합니다.

```bash
cd /Users/jwa/lg-thinq-sales
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api uvicorn app.main:app --reload --port 8000
```

Demo data 재적재:

```bash
curl -X POST "http://localhost:8000/api/v1/demo/seed?reset=true"
```

Collector 결과를 직접 넣을 수도 있습니다.

```bash
curl -X POST "http://localhost:8000/api/v1/ingestion/vocs" \
  -H "Content-Type: application/json" \
  -d '[{"source":"Danawa","external_id":"manual-001","title":"VOC","content":"I want to buy LG air purifier because fine dust is bad.","url":"https://example.com","published_at":"2026-05-20T09:10:00Z","product_category":"Air Purifier","region":"Seoul","engagement":12}]'
```

## 프론트엔드 실행

```bash
cd /Users/jwa/lg-thinq-sales/apps/web
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

브라우저에서 `http://localhost:3000`을 엽니다.

## Docker Compose 실행

```bash
cd /Users/jwa/lg-thinq-sales
docker compose up
```

## API endpoint

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/vocs`
- `GET /api/v1/vocs/stats`
- `GET /api/v1/lead-scores`
- `GET /api/v1/insights`
- `POST /api/v1/demo/seed`
- `POST /api/v1/ingestion/vocs`

## 현재 demo/stub 처리된 기능

- 실제 Danawa, Reddit, Naver Blog, YouTube, X/Twitter 수집은 아직 구현하지 않았습니다. 다만 collector output을 받을 `POST /api/v1/ingestion/vocs` endpoint는 준비되어 있습니다.
- 실제 OpenAI/Gemini API 호출은 하지 않습니다.
- 실제 기상청, AirKorea, 전기요금, 입주물량 API는 아직 연결하지 않았습니다.
- PostgreSQL + SQLAlchemy 저장 구조를 사용합니다. migration은 아직 Alembic이 아니라 `Base.metadata.create_all()` 방식입니다.
- CRM/ERP 연동, 자동 이메일/문자 발송, 실시간 스트리밍은 MVP 범위에서 제외했습니다.

## 현재 구현된 end-to-end 흐름

`data/demo/voc_records.json`의 VOC 20건을 읽어 다음 파이프라인을 실행합니다.

```text
Demo VOC 수집
→ 텍스트 정규화
→ 룰 기반 sentiment / intent / urgency / topic 분석
→ lead score 계산
→ demo 외부 맥락 매칭
→ demo strategy insight 생성
→ PostgreSQL 저장
→ FastAPI endpoint 제공
→ Next.js dashboard 화면 렌더링
```

## 다음 구현 추천 단계

1. Alembic migration 체계를 추가합니다.
2. demo pipeline을 batch job 형태로 분리합니다.
3. Danawa 또는 Reddit connector 하나를 실제 수집기로 구현합니다.
4. 외부 데이터 매칭을 기상청/AirKorea demo adapter부터 확장합니다.
5. LLM gateway를 추가하되 demo mode와 production mode를 명확히 분리합니다.
