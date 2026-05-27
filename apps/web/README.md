# LG ThinQ-Sales Web

Next.js + React + TypeScript + Tailwind CSS 기반 Phase 0 + Phase 1 데모 프론트엔드입니다.

## 실행

백엔드가 `http://localhost:8000`에서 먼저 실행 중이어야 합니다.

```bash
cd /Users/jwa/lg-thinq-sales/apps/web
npm install
npm run dev
```

필요 시 API 주소를 변경할 수 있습니다.

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## Route

- `/`
- `/voc`
- `/lead-scoring`
- `/strategy-insights`

## 현재 상태

모든 화면은 FastAPI demo API를 통해 데이터를 가져옵니다. 실제 크롤링, 실제 LLM, 실제 CRM/ERP 연동은 아직 구현하지 않았습니다.
