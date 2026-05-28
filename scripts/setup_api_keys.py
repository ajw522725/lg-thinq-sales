"""
실제 API 키 설정 및 live 모드 전환 스크립트.

실행:
  python scripts/setup_api_keys.py

대화형으로 각 API 키를 입력받아 .env 파일을 업데이트한다.
이미 값이 있는 키는 Enter로 건너뛸 수 있다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ENV_FILE = ROOT / ".env"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def save_env(path: Path, env: dict[str, str], original_lines: list[str]) -> None:
    result = []
    updated: set[str] = set()
    for line in original_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            result.append(line)
            continue
        if "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k in env:
                result.append(f"{k}={env[k]}")
                updated.add(k)
                continue
        result.append(line)
    # 새로 추가된 키
    for k, v in env.items():
        if k not in updated:
            result.append(f"{k}={v}")
    path.write_text("\n".join(result) + "\n", encoding="utf-8")


def prompt_key(name: str, current: str, description: str) -> str:
    display = f"***...{current[-4:]}" if len(current) > 6 else ("(미설정)" if not current else current)
    value = input(f"  {name} [{display}] ({description}): ").strip()
    return value if value else current


def main() -> None:
    print("=== LG ThinQ-Sales API 키 설정 ===\n")
    print("Enter를 누르면 기존 값을 유지합니다.\n")

    original_lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    env = load_env(ENV_FILE)

    print("[ Reddit API ]  https://www.reddit.com/prefs/apps")
    env["REDDIT_CLIENT_ID"]     = prompt_key("REDDIT_CLIENT_ID",     env.get("REDDIT_CLIENT_ID", ""),     "앱 ID")
    env["REDDIT_CLIENT_SECRET"] = prompt_key("REDDIT_CLIENT_SECRET", env.get("REDDIT_CLIENT_SECRET", ""), "앱 시크릿")
    print()

    print("[ Naver Search API ]  https://developers.naver.com/apps")
    env["NAVER_CLIENT_ID"]     = prompt_key("NAVER_CLIENT_ID",     env.get("NAVER_CLIENT_ID", ""),     "클라이언트 ID")
    env["NAVER_CLIENT_SECRET"] = prompt_key("NAVER_CLIENT_SECRET", env.get("NAVER_CLIENT_SECRET", ""), "클라이언트 시크릿")
    print()

    print("[ YouTube Data API v3 ]  https://console.cloud.google.com")
    env["YOUTUBE_API_KEY"] = prompt_key("YOUTUBE_API_KEY", env.get("YOUTUBE_API_KEY", ""), "API 키")
    print()

    print("[ LLM API (하나만 입력) ]")
    env["OPENAI_API_KEY"] = prompt_key("OPENAI_API_KEY", env.get("OPENAI_API_KEY", ""), "OpenAI API 키 (sk-...)")
    env["GEMINI_API_KEY"] = prompt_key("GEMINI_API_KEY", env.get("GEMINI_API_KEY", ""), "Gemini API 키")
    print()

    # LLM provider 자동 설정
    if env.get("OPENAI_API_KEY"):
        env["LLM_PROVIDER"] = "openai"
        env["OPENAI_MODEL"] = env.get("OPENAI_MODEL", "gpt-4o-mini")
    elif env.get("GEMINI_API_KEY"):
        env["LLM_PROVIDER"] = "gemini"
        env["GEMINI_MODEL"] = env.get("GEMINI_MODEL", "gemini-1.5-flash")
    else:
        env["LLM_PROVIDER"] = "demo"

    # 실제 API 키가 하나라도 있으면 demo 모드 해제
    live_apis = [
        env.get("REDDIT_CLIENT_ID"),
        env.get("NAVER_CLIENT_ID"),
        env.get("YOUTUBE_API_KEY"),
    ]
    if any(live_apis):
        env["USE_DEMO_DATA"] = "false"
        env["DEMO_MODE"]     = "false"
        env["SCHEDULER_ENABLED"] = "true"
        print("✅ 실제 API 키 감지 — 라이브 모드로 전환합니다.")
    else:
        env["USE_DEMO_DATA"] = "true"
        env["DEMO_MODE"]     = "true"
        print("⚠️  API 키 미설정 — 데모 모드 유지.")

    save_env(ENV_FILE, env, original_lines)
    print(f"\n.env 저장 완료: {ENV_FILE}")
    print(f"LLM provider: {env['LLM_PROVIDER']}")
    print(f"Demo mode: {env.get('DEMO_MODE')}")
    print("\n서버를 재시작하면 설정이 반영됩니다.")


if __name__ == "__main__":
    main()
