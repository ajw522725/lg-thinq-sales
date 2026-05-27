# LG ThinQ-Sales 협업 에이전트 지침

이 문서는 각 팀원의 로컬 PC에서 AI 코딩 에이전트가 repo를 열었을 때 가장 먼저 참고해야 하는 작업 지침입니다.

## 프로젝트 목표

LG ThinQ-Sales는 VOC/SNS 데이터를 수집하고, NLP 분석과 리드 스코어링을 거쳐 외부 데이터 맥락과 LLM 전략 인사이트를 결합한 뒤 영업 관리자용 대시보드로 출력하는 MVP입니다.

핵심 흐름:

```text
VOC/SNS 수집
→ 텍스트 전처리
→ NLP 분석
→ 리드 스코어 생성
→ 외부 데이터 결합
→ LLM 전략 인사이트 생성
→ 영업 전략 운영 대시보드 출력
```

## 역할 배정

| GitHub ID | 역할 | 핵심 책임 | 주 담당 영역 |
|---|---|---|---|
| `ajw522725` | 총책임 / PM / Backend Integration Lead | 전체 아키텍처, 일정, API 계약, 통합 테스트, 최종 데모 흐름 관리 | `apps/api`, `db`, `docker-compose.yml`, `README.md` |
| `wldnjsrla085` | Data Collection / Dataset Lead | 다나와, Reddit, 네이버 블로그, YouTube 등 VOC 수집과 데이터셋 품질 관리 | `services/collectors`, `data/raw`, `data/demo`, `data/processed` |
| `yuna0822` | AI/NLP / Insight Lead | 감성분석, 구매의도 탐지, 토픽/경쟁사 분석, Lead Score, LLM 인사이트 생성 | `services/nlp`, `services/scoring`, `services/insights`, `packages/prompts` |
| `sksmsdngml-ui` | Frontend / Demo UX Lead | Next.js 관리자 대시보드, VOC/Lead/Insight 화면, 차트, 데모 UI polish | `apps/web` |

역할은 초기 배정입니다. 작업 중 변경이 필요하면 `ajw522725`와 합의한 뒤 README와 이 문서를 함께 수정합니다.

## 공통 개발 원칙

- 문서, README, PR 설명, 작업 보고는 한국어로 작성합니다.
- 코드 식별자, 함수명, 파일명, API endpoint, DB table명은 영어로 작성합니다.
- `main` 브랜치는 항상 실행 가능한 상태로 유지합니다.
- 작업은 개인 feature branch에서 진행하고 PR로 병합합니다.
- 실제 외부 연동이 아닌 경우 demo/stub임을 코드와 문서에 명확히 표시합니다.
- 이번 MVP에서 Auth, CRM/ERP, 실시간 스트리밍, 강화학습, 복잡한 ML 학습 구조는 우선순위가 아닙니다.

## 브랜치 권장 규칙

- `feature/backend-db-pipeline`
- `feature/data-collectors`
- `feature/nlp-insight-engine`
- `feature/frontend-dashboard`
- `docs/demo-scenario`

브랜치명은 역할과 작업 내용이 바로 보이게 작성합니다.

## 역할별 상세 지침

### `ajw522725` - 총책임 / PM / Backend Integration Lead

우선순위:

1. FastAPI API 계약 관리
2. PostgreSQL/SQLAlchemy 저장 구조 추가
3. 수집 데이터 → DB → 분석 → 인사이트 → 대시보드 API 연결
4. Docker Compose 실행 안정화
5. 최종 End-to-End 데모 시나리오 관리

주요 endpoint:

- `GET /api/v1/health`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/vocs`
- `GET /api/v1/vocs/stats`
- `GET /api/v1/lead-scores`
- `GET /api/v1/insights`
- `POST /api/v1/demo/seed`

### `wldnjsrla085` - Data Collection / Dataset Lead

우선순위:

1. 다나와 수집기 안정화
2. Reddit keyword 기반 수집기 구현
3. 네이버 블로그 API 연결
4. 가능하면 YouTube 댓글 수집
5. X/Twitter는 시간이 부족하면 demo/stub으로 대체
6. 발표용 고품질 VOC 샘플 데이터 정리

표준 VOC record 예시:

```json
{
  "source": "Danawa",
  "title": "Subscription care price concern",
  "content": "...",
  "url": "https://example.com",
  "published_at": "2026-05-20T09:10:00Z",
  "product_category": "Air Conditioner",
  "region": "Seoul",
  "engagement": 12
}
```

수집기는 대규모 완성도보다 분석 가능한 데이터 품질을 우선합니다.

### `yuna0822` - AI/NLP / Insight Lead

우선순위:

1. rule-based sentiment / intent / urgency 분석 개선
2. 경쟁사 언급 탐지 사전 관리
3. topic label 또는 BERTopic 연결 검토
4. Lead Score v2 공식 개선
5. LLM prompt template 작성
6. hallucination 방지 규칙 적용

LLM insight output은 JSON 구조를 유지합니다.

```json
{
  "title": "...",
  "summary": "...",
  "recommended_action": "...",
  "reasoning": "...",
  "priority": "High",
  "target_segment": "...",
  "confidence": 0.87
}
```

완벽한 모델 성능보다 점수와 근거가 설명 가능한지를 우선합니다.

### `sksmsdngml-ui` - Frontend / Demo UX Lead

우선순위:

1. Dashboard summary 고도화
2. VOC Analysis 화면의 필터, 테이블, 토픽 표시 개선
3. Lead Scoring 화면의 selected lead detail panel 구현
4. Strategy Insights 화면의 recommendation card와 context UI 개선
5. Loading/error state 처리
6. 발표용 UI polish

디자인 기준:

- `docs/reference/mockups/executive_intelligence_system/DESIGN.md`
- `docs/reference/mockups/*/code.html`
- Inter font, LG Red accent, soft gray background, white bento cards, subtle AI glow 유지

## 4일 액션 플랜

### Day 1 - 시스템 뼈대 구축

- `ajw522725`: FastAPI, PostgreSQL, Docker Compose, API 구조 확인
- `wldnjsrla085`: 다나와/Reddit/네이버 블로그 수집 초안
- `yuna0822`: sentiment baseline, 구매의도 rule, lead score baseline
- `sksmsdngml-ui`: Next.js 관리자 UI 골격과 공통 컴포넌트 확인

목표: 백엔드/프론트 실행, demo data API 출력, 기본 UI 렌더링

### Day 2 - 데이터 흐름 연결

- `ajw522725`: 수집 결과 DB 저장 API, 공통 모델, scheduler 초안
- `wldnjsrla085`: 다중 플랫폼 VOC 확보와 데이터 정제
- `yuna0822`: NLP 분석 pipeline, competitor detection, lead score 개선
- `sksmsdngml-ui`: Backend API 연결 화면 개선

목표: 실제 또는 demo VOC가 분석되어 화면에 표시됨

### Day 3 - AI 전략 인사이트 구현

- `ajw522725`: 기상청/AirKorea 또는 context stub 연결
- `wldnjsrla085`: 발표용 데이터셋과 platform metadata 정리
- `yuna0822`: LLM 전략 인사이트 생성, prompt tuning, reasoning formatting
- `sksmsdngml-ui`: Strategy Insights, External Context, Trend Chart 구현

목표: context-aware insight가 dashboard에서 설득력 있게 보임

### Day 4 - 발표 및 시연 완성

- `ajw522725`: 전체 pipeline 통합 테스트, demo flow 정리
- `wldnjsrla085`: 에어컨/공기청정기 발표 시나리오용 VOC 사례 정리
- `yuna0822`: hallucination 제거, 최종 prompt tuning
- `sksmsdngml-ui`: UI polish, loading state, 발표 화면 구성

목표: End-to-End 데모 가능

## PR 체크리스트

PR을 열기 전에 다음을 확인합니다.

- 담당 역할과 관련된 파일만 수정했는가?
- demo/stub 처리된 기능은 명확히 표시했는가?
- README 또는 관련 문서를 업데이트했는가?
- 가능한 검증 명령을 실행했는가?

권장 검증:

```bash
# Backend
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api .venv/bin/python -m compileall apps/api/app services

# Frontend
cd apps/web
npm run typecheck
npm run lint
npm run build
```

## MVP 성공 기준

- VOC/SNS 데이터가 확보된다.
- sentiment / purchase intent / topic / competitor 분석이 가능하다.
- Lead Score와 priority가 산출된다.
- 외부 context 또는 context stub이 연결된다.
- LLM 또는 demo LLM 전략 인사이트가 생성된다.
- 관리자 dashboard에서 전체 흐름을 시연할 수 있다.

