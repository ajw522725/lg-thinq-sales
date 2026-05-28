# LG ThinQ-Sales Web

Next.js + React + TypeScript + Tailwind CSS 기반 Phase 0 + Phase 1 데모 프론트엔드입니다.

## 실행

백엔드가 `http://localhost:8000`에서 먼저 실행 중이어야 합니다.

전체 end-to-end 화면을 보려면 루트에서 백엔드를 먼저 실행하고 demo seed를 적재합니다.

```bash
cd /Users/jwa/lg-thinq-sales
source .venv/bin/activate
PYTHONPATH=/Users/jwa/lg-thinq-sales:/Users/jwa/lg-thinq-sales/apps/api \
  uvicorn app.main:app --reload --port 8000
curl -X POST "http://localhost:8000/api/v1/demo/seed?reset=true"
```

그 다음 프론트엔드를 실행합니다.

```bash
cd /Users/jwa/lg-thinq-sales/apps/web
npm install
npm run dev
```

브라우저에서 `http://localhost:3000`을 엽니다.

프론트 화면만 먼저 확인하려면 `npm run dev`만 실행해도 됩니다. 이 경우 API 연결이 실패하면 화면은 fallback data를 사용할 수 있습니다.

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
