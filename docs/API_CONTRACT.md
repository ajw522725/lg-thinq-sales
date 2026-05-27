# LG ThinQ-Sales API 계약

이 문서는 팀원들이 collector, NLP, frontend 작업을 독립적으로 진행하기 위한 백엔드 API 계약입니다.

## 공통 원칙

- API prefix는 `/api/v1`입니다.
- 현재 MVP는 PostgreSQL + SQLAlchemy 저장 구조를 사용합니다.
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
- `YouTube`
- `X/Twitter`

### product_category

- `Washer`
- `Air Conditioner`
- `Refrigerator`
- `Air Purifier`
- `LG Styler`
- `Subscription Care`

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

### AI/NLP 담당

- `services/nlp`, `services/scoring`, `services/insights`의 함수 output shape을 유지합니다.
- LLM 연동 시에도 `StrategyInsight` JSON 구조는 유지합니다.
- hallucination 방지를 위해 VOC 원문, 분석 결과, context match에 없는 내용은 생성하지 않습니다.

### Frontend 담당

- 기존 `VocRecord`, `DashboardSummary`, `StrategyInsight` response shape을 기준으로 화면을 구현합니다.
- API가 비어 있을 수 있으므로 empty state를 처리합니다.

## 현재 demo/stub 범위

- 실제 OpenAI/Gemini API는 아직 연결하지 않았습니다.
- 실제 기상청/AirKorea API는 아직 연결하지 않았습니다.
- context matching은 `services/context/demo_context_matcher.py` 기반 demo logic입니다.
- NLP와 Lead Score는 rule-based baseline입니다.
