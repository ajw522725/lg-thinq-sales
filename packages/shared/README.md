# shared

프론트엔드와 백엔드가 공유할 타입, 스키마, 상수 후보를 두는 위치입니다.

현재 Phase 1에서는 중복을 줄이기보다 각 런타임의 타입 안정성을 우선하여 Python Pydantic schema와 TypeScript interface를 별도로 유지합니다.
