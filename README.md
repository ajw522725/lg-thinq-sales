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
- Backend: Python, FastAPI, Pydantic, SQLAlchemy
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

PostgreSQL을 먼저 실행합니다. Docker가 있으면 다음 명령을 사용합니다.

```bash
cd /Users/jwa/lg-thinq-sales
docker compose up -d postgres
```

Docker 없이 macOS 로컬 PostgreSQL을 사용할 경우 다음처럼 설치하고 실행합니다.

```bash
brew install postgresql@16
brew services start postgresql@16
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
```

프로젝트 기본 DB 계정과 데이터베이스를 생성합니다.

```bash
psql -d postgres -c "CREATE ROLE lg_thinq LOGIN PASSWORD 'lg_thinq';"
createdb -O lg_thinq lg_thinq_sales
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE lg_thinq_sales TO lg_thinq;"
psql -d lg_thinq_sales -c "GRANT ALL ON SCHEMA public TO lg_thinq;"
```

기본 DB 연결 주소는 다음과 같습니다.

```bash
DATABASE_URL=postgresql+psycopg://lg_thinq:lg_thinq@localhost:5432/lg_thinq_sales
```

백엔드를 실행합니다.

```bash
cd /Users/jwa/lg-thinq-sales
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api uvicorn app.main:app --reload --port 8000
```

API만 최소 실행할 경우에는 `pip install -r apps/api/requirements.txt`도 가능합니다. 다만 collector까지 함께 확인하려면 루트 `requirements.txt`를 사용하세요.

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

## TablePlus 접속

로컬 DB를 GUI로 확인할 때는 TablePlus에서 PostgreSQL connection을 만들고 다음 값을 입력합니다.

```text
Name: LG ThinQ Sales Local
Host: localhost
Port: 5432
User: lg_thinq
Password: lg_thinq
Database: lg_thinq_sales
SSL Mode: Disable
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
- `POST /api/v1/nlp/analyze`
- `POST /api/v1/pipeline/run`
- `GET /api/v1/demo/run`

## Collector demo 실행

기본 demo mode에서는 실제 외부 API key 없이 Danawa, Reddit, Naver Blog, YouTube collector stub 데이터를 반환합니다.

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
USE_DEMO_DATA=true PYTHONPATH=/Users/jwa/lg-thinq-sales \
  python -m services.collectors.runner --keyword "LG 공기청정기" --max 2 --no-save
```

확인 기준:

```text
Danawa 12건
Reddit 10건
NaverBlog 10건
YouTube 10건
전처리 통과 약 41건
```

collector 결과를 API DB 저장 흐름까지 확인하려면 `POST /api/v1/ingestion/vocs` 입력 계약에 맞춰 전송해야 합니다. 자세한 계약은 `docs/API_CONTRACT.md`를 확인하세요.

## 통합 검증 명령

팀원은 PR 전 또는 main pull 후 아래 검증을 실행하세요.

백엔드/서비스 컴파일:

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api \
  python -m compileall apps/api/app services scripts
```

API smoke test:

```bash
curl http://localhost:8000/api/v1/health
curl -X POST "http://localhost:8000/api/v1/demo/seed?reset=true"
curl http://localhost:8000/api/v1/dashboard/summary
curl http://localhost:8000/api/v1/vocs
curl http://localhost:8000/api/v1/vocs/stats
curl http://localhost:8000/api/v1/lead-scores
curl http://localhost:8000/api/v1/insights
curl http://localhost:8000/api/v1/demo/run
```

프론트엔드 검증:

```bash
cd /Users/jwa/lg-thinq-sales/apps/web
npm run typecheck
npm run lint
npm run build
```

Codex 통합 확인 결과:

```text
compileall apps/api/app services scripts: 통과
collector demo runner: 통과
API smoke test 10개 endpoint: 모두 200
npm run typecheck: 통과
npm run lint: 통과
npm run build: 통과
collector demo output 5건 -> /api/v1/ingestion/vocs -> DB 저장: 통과
```

현재 확인된 warning:

```text
Pydantic protected namespace 경고: model_version, model_used 필드명 관련 경고입니다. 현재 실행에는 영향이 없고, 추후 model_config로 정리할 수 있습니다.
```

## 현재 demo/stub 처리된 기능

- Danawa, Reddit, Naver Blog, YouTube collector 골격과 demo mode는 구현되어 있습니다. 실제 live 수집은 API key/session/cookie 설정과 플랫폼별 제한 대응이 필요합니다.
- X/Twitter collector는 아직 구현되지 않았습니다.
- 실제 OpenAI/Gemini API 호출은 demo mode에서는 하지 않습니다.
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

추가로 yuna0822 NLP/Scoring/Insight pipeline은 아래 단독 endpoint로 확인할 수 있습니다.

```text
VOC text
→ /api/v1/nlp/analyze
→ /api/v1/pipeline/run
→ demo NLP / Lead Score / Strategy Insight 응답
```

## 팀원별 다음 확인 항목

### `wldnjsrla085` Data Collection

- `USE_DEMO_DATA=true python -m services.collectors.runner ...`가 로컬에서 통과하는지 확인합니다.
- collector raw output을 `POST /api/v1/ingestion/vocs` 입력 구조로 매핑하는 script를 추가합니다.
- live mode는 API key/session이 없을 때 실패하지 않고 빈 리스트 또는 demo fallback을 반환해야 합니다.

### `yuna0822` AI/NLP

- `/api/v1/nlp/analyze`, `/api/v1/pipeline/run`, `/api/v1/demo/run`이 main에서 계속 200 응답인지 확인합니다.
- 다음 단계에서는 DB seed/ingestion pipeline이 yuna pipeline을 선택적으로 사용하도록 연결합니다.
- 기존 frontend가 사용하는 `VocRecord`, `DashboardSummary`, `StrategyInsight` 응답 구조는 깨지 않도록 유지합니다.

### `sksmsdngml-ui` Frontend

- API 서버가 켜진 상태와 꺼진 fallback 상태를 모두 확인합니다.
- `/`, `/voc`, `/lead-scoring`, `/strategy-insights`에서 text overflow와 모바일/데스크톱 layout 깨짐을 확인합니다.
- API 응답이 있을 때는 fallback보다 API 데이터를 우선 사용해야 합니다.

### `ajw522725` PM / Backend Integration

- main merge 후 `compileall`, API smoke test, frontend build를 실행합니다.
- TablePlus에서 seed/ingestion 후 `raw_documents`, `processed_vocs`, `lead_scores`, `strategy_insights` row count를 확인합니다.
- collector ingestion과 yuna pipeline을 하나의 DB 저장 pipeline으로 통합하는 작업을 다음 우선순위로 둡니다.

## 다음 구현 추천 단계

1. collector output을 `/api/v1/ingestion/vocs`로 자동 전송하는 demo ingestion script를 추가합니다.
2. DB seed/ingestion pipeline에 yuna NLP/Scoring/Insight pipeline을 선택적으로 연결합니다.
3. Alembic migration 체계를 추가합니다.
4. Danawa 또는 Reddit live connector를 하나만 우선 안정화합니다.
5. 외부 데이터 매칭을 기상청/AirKorea demo adapter부터 확장합니다.
6. LLM gateway를 추가하되 demo mode와 production mode를 명확히 분리합니다.
