# LG ThinQ-Sales API 계약

이 문서는 팀원들이 collector, NLP, frontend 작업을 독립적으로 진행하기 위한 백엔드 API 계약입니다.

## 공통 원칙

- API prefix는 `/api/v1`입니다.
- 현재 MVP는 PostgreSQL + SQLAlchemy 저장 구조를 사용합니다.
- DB schema는 Alembic migration으로 관리하며, 로컬 MVP fallback으로 `AUTO_CREATE_TABLES=true`를 지원합니다.
- 실제 외부 API나 실제 LLM이 아직 없을 경우 demo/stub임을 명확히 표시합니다.
- 프론트엔드가 사용하는 기존 response shape은 유지합니다.

## Collector 입력 계약

팀원 2의 collector 결과는 다음 endpoint로 전달합니다.

```http
POST /api/v1/ingestion/vocs
```

입력은 VOC record 배열입니다.

```json
[
  {
    "source": "Danawa",
    "external_id": "danawa-001",
    "title": "Subscription care price concern",
    "content": "VOC 원문 텍스트",
    "url": "https://example.com/review/1",
    "published_at": "2026-05-20T09:10:00Z",
    "product_category": "Washer",
    "region": "Seoul",
    "engagement": 12,
    "author_hash": "optional_hash",
    "rating": 4
  }
]
```

필수 필드:

- `source`
- `external_id`
- `title`
- `content`
- `url`
- `published_at`
- `product_category`

선택 필드:

- `region`
- `engagement`
- `author_hash`
- `rating`

응답:

```json
{
  "seeded": true,
  "raw_documents": 20,
  "processed_documents": 20,
  "insights": 20
}
```

## Demo seed

```http
POST /api/v1/demo/seed?reset=true
```

- `reset=true`: 기존 demo pipeline 데이터를 삭제하고 다시 생성합니다.
- `reset=false` 또는 생략: 이미 저장된 `source + external_id` 조합은 중복 저장하지 않습니다.

DB 저장 pipeline은 환경변수 `DB_PIPELINE_PROVIDER`로 선택합니다.

- `legacy`: 기존 Phase 1 rule-based pipeline입니다. 기본값입니다.
- `yuna`: `services/nlp`, `services/scoring`, `services/insights`의 통합 pipeline을 사용합니다.

두 모드 모두 API response shape은 `VocRecord`, `DashboardSummary`, `StrategyInsight` 계약을 유지해야 합니다.

## NLP / Pipeline 단독 실행 계약

AI/NLP 담당 pipeline은 DB 저장 pipeline과 별도로 다음 endpoint에서 단독 확인할 수 있습니다.

```http
POST /api/v1/nlp/analyze
POST /api/v1/pipeline/run
GET /api/v1/demo/run
```

### POST /api/v1/nlp/analyze

입력:

```json
{
  "text": "미세먼지가 심해서 LG 공기청정기를 구매하려고 합니다.",
  "source": "naver_blog",
  "language": "ko",
  "product_category": "air_purifier",
  "product_keyword": "LG 퓨리케어",
  "rating": null,
  "engagement": 12,
  "platform_meta": {
    "view_count": 1200
  }
}
```

응답:

```json
{
  "voc_id": "uuid",
  "sentiment_label": "neutral",
  "sentiment_score": 0.5,
  "intent_label": "high",
  "purchase_intent_score": 0.85,
  "urgency_score": 0.2,
  "complaint_type": null,
  "topic_id": "air_quality",
  "topic_label": "공기질",
  "keywords": ["미세먼지", "공기청정기"],
  "competitor_mentions": {
    "dyson": 1
  },
  "competitor_comparison_flag": true,
  "model_version": "rule_based_v1.0"
}
```

### POST /api/v1/pipeline/run

`/nlp/analyze`와 같은 입력을 받아 NLP, lead scoring, strategy insight를 한 번에 반환합니다.

응답:

```json
{
  "voc_id": "uuid",
  "source": "naver_blog",
  "product_category": "air_purifier",
  "nlp": {},
  "score": {
    "lead_score": 62.5,
    "priority": "medium",
    "score_reason": {}
  },
  "insight": {
    "title": "...",
    "summary": "...",
    "recommended_action": "...",
    "reasoning": "...",
    "confidence": 0.8,
    "llm_model": "demo"
  },
  "processing_time_ms": 12.3,
  "demo_mode": true
}
```

### GET /api/v1/demo/run

`data/demo/sample_voc.json`의 demo VOC 10건을 yuna pipeline으로 일괄 분석합니다. DB 저장은 하지 않고 pipeline 단독 검증용으로 사용합니다.

## 주요 응답 구조

### VocRecord

`GET /api/v1/vocs`, `GET /api/v1/lead-scores`는 다음 구조의 배열을 반환합니다.

```json
{
  "voc": {
    "id": "uuid",
    "raw_document_id": "uuid",
    "source": "Danawa",
    "title": "VOC title",
    "normalized_text": "정제된 VOC 텍스트",
    "product_category": "Air Conditioner",
    "brand_mentions": ["LG"],
    "competitor_mentions": ["samsung"],
    "keywords": ["subscription care"],
    "region": "Seoul",
    "published_at": "2026-05-20T09:10:00Z",
    "url": "https://example.com",
    "created_at": "2026-05-27T00:00:00Z"
  },
  "analysis": {
    "sentiment_label": "positive",
    "sentiment_score": 0.7,
    "intent_label": "high",
    "purchase_intent_score": 0.88,
    "urgency_label": "medium",
    "urgency_score": 0.3,
    "complaint_type": null,
    "topic_id": "energy_efficiency",
    "topic_label": "Energy Efficiency",
    "confidence": 0.83,
    "model_version": "rule-based-v1"
  },
  "lead_score": {
    "lead_score": 87,
    "priority": "high",
    "score_reason": {
      "intent_points": 40.5
    },
    "model_version": "lead-score-v1"
  },
  "insight": {
    "title": "Energy-saving value proposition is resonating",
    "summary": "...",
    "recommended_action": "...",
    "reasoning": "...",
    "priority": "high",
    "target_segment": "Refrigerator",
    "confidence": 0.92,
    "llm_model": "demo-rule-generator",
    "prompt_version": "demo-v1"
  },
  "context": {
    "context_type": "energy",
    "region": "Seoul",
    "match_reason": "energy efficiency keyword",
    "match_score": 0.74
  }
}
```

## Enum 후보

### source

- `Danawa`
- `Reddit`
- `Naver Blog`
- `NaverBlog`
- `YouTube`
- `X/Twitter`

### product_category

DB ingestion 화면용 값:

- `Washer`
- `Air Conditioner`
- `Refrigerator`
- `Air Purifier`
- `LG Styler`
- `Subscription Care`

NLP/pipeline 단독 endpoint와 collector 내부 값:

- `air_conditioner`
- `air_purifier`
- `refrigerator`
- `washing_machine`
- `dehumidifier`
- `dryer`
- `general`

### sentiment_label

- `positive`
- `neutral`
- `negative`

### intent_label

- `high`
- `medium`
- `low`

### urgency_label

- `critical`
- `medium`
- `low`

### priority

- `high`
- `medium`
- `low`

## 팀별 맞춰야 할 구조

### Data Collection 담당

- collector output은 반드시 `POST /api/v1/ingestion/vocs` 입력 구조를 따릅니다.
- `source + external_id`는 중복 방지 기준이므로 안정적으로 생성해야 합니다.
- 개인정보는 원문 저장 전 `author_hash` 형태로 비식별화합니다.
- `services.collectors.runner`의 raw output은 `platform_meta` 중심 필드가 포함되므로 ingestion 전 아래 매핑을 적용합니다.

Collector raw output -> ingestion input 매핑:

| collector field | ingestion field | 비고 |
|---|---|---|
| `source` | `source` | `Danawa`, `Reddit`, `NaverBlog`, `YouTube` |
| `external_id` | `external_id` | 없으면 collector에서 안정 ID 생성 필요 |
| `title` | `title` | 없으면 `"Untitled VOC"` |
| `content` | `content` | 필수 |
| `url` | `url` | 없으면 원 source URL 또는 placeholder |
| `published_at` | `published_at` | 없으면 `collected_at` |
| `product_category` | `product_category` | DB 화면용 enum과 매핑 필요 |
| `author_hash` | `author_hash` | 비식별화 값 |
| `platform_meta.rating` 또는 `rating` | `rating` | 선택 |
| `platform_meta.view_count/comment_count/upvotes/likes/helpful_count` | `engagement` | 정수로 정규화 |

표준 매핑과 API 전송은 다음 스크립트로 확인합니다.

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
PYTHONPATH=/Users/jwa/lg-thinq-sales \
  python scripts/run_collector_ingestion_demo.py --keyword "LG 공기청정기" --max 2 --limit 5 --reset
```

지원 옵션:

- `--dry-run`: API 전송 없이 collector raw output -> ingestion payload 매핑만 확인합니다.
- `--reset`: 전송 전 기존 DB pipeline 데이터를 삭제하고 재적재합니다.
- `--limit N`: 전송할 VOC 수를 제한합니다.
- `--source Reddit`: 특정 source만 실행합니다. `Danawa`, `Reddit`, `NaverBlog`, `YouTube`를 지원합니다.
- `--live`: `USE_DEMO_DATA=false`로 live collector를 실행합니다. API key/session 설정이 필요할 수 있습니다.

Reddit live mode는 `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`이 없으면 public JSON fallback을 사용합니다. Reddit 제한 응답, 네트워크 차단, 검색 결과 없음은 빈 리스트로 안전 종료합니다.

### AI/NLP 담당

- `services/nlp`, `services/scoring`, `services/insights`의 함수 output shape을 유지합니다.
- LLM 연동 시에도 `StrategyInsight` JSON 구조는 유지합니다.
- hallucination 방지를 위해 VOC 원문, 분석 결과, context match에 없는 내용은 생성하지 않습니다.
- 현재 `/api/v1/nlp/analyze`, `/api/v1/pipeline/run`, `/api/v1/demo/run`은 단독 검증용입니다.
- DB seed/ingestion pipeline은 `DB_PIPELINE_PROVIDER=yuna` 설정으로 yuna NLP/Scoring/Insight pipeline을 선택적으로 사용합니다.

### Frontend 담당

- 기존 `VocRecord`, `DashboardSummary`, `StrategyInsight` response shape을 기준으로 화면을 구현합니다.
- API가 비어 있을 수 있으므로 empty state를 처리합니다.
- API 응답이 있으면 API 데이터를 우선 사용하고, API가 꺼져 있거나 실패할 때만 `apps/web/lib/demo-data.ts` fallback을 사용합니다.

## Codex 확인 결과

2026-05-28 기준 main에서 확인한 결과입니다.

```text
python -m compileall apps/api/app services scripts db/migrations: 통과
alembic upgrade head: 통과
AUTO_CREATE_TABLES=false + demo seed: 통과
AUTO_CREATE_TABLES=false + DB_PIPELINE_PROVIDER=yuna + demo seed: 통과
npm run typecheck: 통과
npm run lint: 통과
npm run build: 통과
GET /api/v1/health: 200
POST /api/v1/demo/seed?reset=true: 200
GET /api/v1/dashboard/summary: 200
GET /api/v1/vocs: 200
GET /api/v1/vocs/stats: 200
GET /api/v1/lead-scores: 200
GET /api/v1/insights: 200
POST /api/v1/nlp/analyze: 200
POST /api/v1/pipeline/run: 200
GET /api/v1/demo/run: 200
collector demo runner: 통과
collector demo output 5건 -> /api/v1/ingestion/vocs -> DB 저장: 통과
Danawa parser smoke test: 통과
Reddit public JSON fallback smoke test: 통과
Reddit public JSON fallback live run: 2건 수집 확인
Reddit public JSON fallback live run -> ingestion endpoint -> DB 저장: 통과
```

현재 남은 warning:

```text
Pydantic protected namespace 경고: model_version, model_used 필드명 관련 경고입니다. 실행 실패는 아니며 추후 model_config로 정리합니다.
```

## 현재 demo/stub 범위

- 실제 OpenAI/Gemini API는 아직 연결하지 않았습니다.
- 실제 기상청/AirKorea API는 아직 연결하지 않았습니다.
- context matching은 `services/context/demo_context_matcher.py` 기반 demo logic입니다.
- NLP와 Lead Score는 rule-based baseline입니다.
- Danawa/Reddit/NaverBlog/YouTube collector는 demo mode에서 검증되었습니다.
- Reddit live mode는 public JSON fallback으로 API key 없이 2건 수집을 확인했습니다.
- Danawa live mode는 상품 검색까지 확인했으며, 리뷰 전문 수집은 `DANAWA_SESSION_COOKIE`가 필요할 수 있습니다.
- X/Twitter collector는 아직 없습니다.
