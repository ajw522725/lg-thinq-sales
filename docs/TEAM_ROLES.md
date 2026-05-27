# 팀 역할분담 및 4일 개발 액션 플랜

이 문서는 LG ThinQ-Sales MVP를 4명이 병렬로 개발하기 위한 역할분담 문서입니다. 각자의 로컬 AI 에이전트는 작업 전 이 문서와 루트 `AGENTS.md`를 먼저 읽어야 합니다.

## 역할 배정

| GitHub ID | 역할 | 핵심 책임 | 최종 산출물 |
|---|---|---|---|
| `ajw522725` | 총책임 / PM / Backend Integration Lead | 전체 시스템 흐름, API 계약, DB, Docker, 통합 테스트, 발표 demo flow | 실행 가능한 백엔드와 End-to-End demo |
| `wldnjsrla085` | Data Collection / Dataset Lead | VOC/SNS 수집, source metadata, demo dataset 품질 관리 | 다중 플랫폼 VOC 데이터셋 |
| `yuna0822` | AI/NLP / Insight Lead | NLP 분석, lead score, LLM prompt, 전략 인사이트 생성 | 분석 결과와 전략 문장 |
| `sksmsdngml-ui` | Frontend / Demo UX Lead | Next.js dashboard, chart, table, insight UI, 발표용 polish | 발표 가능한 관리자 UI |

## Day 1 - 시스템 뼈대 구축

| 담당 | 주요 작업 | 목표 산출물 |
|---|---|---|
| `ajw522725` | FastAPI 구조, PostgreSQL 연결, Docker Compose, API 계약 정리 | Backend 서버 실행 및 DB 연결 준비 |
| `wldnjsrla085` | 다나와, Reddit, 네이버 블로그 수집 초안 | 기본 VOC JSON 확보 |
| `yuna0822` | sentiment baseline, 구매의도 keyword rule, Lead Score baseline | sentiment / lead_score 출력 |
| `sksmsdngml-ui` | Next.js + Tailwind dashboard layout 확인 및 개선 | SaaS형 Admin UI 골격 |

## Day 2 - 데이터 흐름 연결

| 담당 | 주요 작업 | 목표 산출물 |
|---|---|---|
| `ajw522725` | 수집 → DB 저장 API, scheduler 초안, 공통 모델 | 데이터 저장 pipeline |
| `wldnjsrla085` | 다나와 안정화, Reddit keyword 확장, YouTube API 검토, 데이터 정제 | 다중 플랫폼 VOC |
| `yuna0822` | 감성분석 개선, topic 분석, 경쟁사 언급 탐지, Lead Score 개선 | NLP 분석 pipeline |
| `sksmsdngml-ui` | Backend API 연결, VOC list, Lead Score, Insight card 개선 | 실제 데이터 화면 출력 |

## Day 3 - AI 전략 인사이트 구현

| 담당 | 주요 작업 | 목표 산출물 |
|---|---|---|
| `ajw522725` | 기상청/AirKorea 또는 context stub, VOC-context mapping | context-aware 분석 |
| `wldnjsrla085` | SNS source 안정화, 발표용 sample dataset, platform metadata | 발표용 데이터셋 |
| `yuna0822` | LLM 전략 인사이트, prompt tuning, reasoning formatting | 전략 문장 생성 |
| `sksmsdngml-ui` | Strategy Insights 화면, External Context UI, Trend Chart | AI 영업 전략 플랫폼 화면 |

## Day 4 - 발표 및 시연 완성

| 담당 | 주요 작업 | 목표 산출물 |
|---|---|---|
| `ajw522725` | 전체 pipeline 점검, API 오류 수정, demo flow 정리 | End-to-End demo |
| `wldnjsrla085` | 에어컨/공기청정기 VOC 시나리오 정리 | 발표용 sample scenario |
| `yuna0822` | insight 품질 개선, hallucination 제거, 최종 prompt tuning | 안정적인 전략 insight |
| `sksmsdngml-ui` | UI polish, loading state, 발표용 화면 구성 | 발표 가능한 dashboard |

## MVP에서 반드시 집중할 것

1. 데이터 흐름 완성
2. 분석 결과 연결
3. 전략 인사이트 생성
4. Dashboard 출력

## 이번 MVP에서 욕심내지 말 것

- 실시간 스트리밍
- 강화학습
- 완벽한 ML 성능
- 복잡한 Auth
- 고급 인프라
- 실제 기업 CRM/ERP 연동

## 최종 성공 기준

고객의 목소리가 다음 흐름으로 실제 시연되어야 합니다.

```text
VOC 원문
→ NLP 분석
→ Lead Score
→ 외부 context
→ 전략 insight
→ Dashboard
```

이 흐름이 발표에서 자연스럽게 설명되고 화면으로 확인되면 MVP 성공입니다.

