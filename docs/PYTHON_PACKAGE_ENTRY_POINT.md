# Python 패키지 진입점 (__main__.py) 가이드

## 📚 기본 이해

### `__main__.py`의 역할

Python 패키지에서 `__main__.py`는 **패키지를 모듈처럼 실행할 때의 진입점**입니다.

```
mcp_api_server/              ← 패키지 (디렉토리)
├── __main__.py              ← 패키지 진입점
├── mcp_cli.py               ← 모듈
├── main.py                  ← 모듈
└── ...
```

### 🔄 Python `-m` 실행 방식

**패키지를 실행:**
```bash
python -m mcp_api_server
```
↓
`mcp_api_server/__main__.py` 실행 ✓

**모듈을 직접 실행:**
```bash
python -m mcp_api_server.mcp_cli
```
↓
`mcp_api_server/mcp_cli.py` 직접 실행 ✓

---

## 📊 비교: `__main__.py` 있을 때 vs 없을 때

| 항목 | `__main__.py` 있음 | `__main__.py` 없음 |
|------|-------------------|-------------------|
| 패키지 실행 | ✅ `python -m mcp_api_server` | ❌ 불가능 |
| 모듈 직접 실행 | ✅ `python -m mcp_api_server.mcp_cli` | ✅ 같음 |
| 파일 개수 | 더 많음 | 적음 |
| 초기화 로직 | 중앙화 가능 | 분산됨 |

---

## 🎯 실제 사용 사례: 여러 시작점

### 상황: 프로젝트에 여러 모드가 필요할 때

```
프로젝트 실행 방식:
1. StdIO 모드 (Claude Desktop용)
2. HTTP 서버 모드 (네트워크 배포용)
3. 클라이언트 테스트 모드
```

### ✅ 해결책: `__main__.py`에서 모드 선택

```python
# mcp_api_server/__main__.py
import asyncio
import argparse
import sys

async def main() -> None:
    """Run MCP server with configurable mode."""
    parser = argparse.ArgumentParser(description="MCP API Server")
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="Server mode: stdio (Claude Desktop) or http (network)"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.mode == "stdio":
        # StdIO 모드
        from .mcp_cli import main as mcp_stdio_main
        await mcp_stdio_main()
    elif args.mode == "http":
        # HTTP 서버 모드
        import uvicorn
        from .main import app
        uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### 사용 방식

```bash
# StdIO 모드 (기본)
python -m mcp_api_server

# HTTP 모드
python -m mcp_api_server --mode http --port 8000

# 도움말
python -m mcp_api_server --help
```

---

## 🔍 현재 프로젝트 상황

### 현재 구조
```
mcp_api_server/
├── __main__.py          ← 단순 wrapper (mcp_cli.main() 호출만)
├── mcp_cli.py           ← StdIO 실행 로직
├── main.py              ← HTTP 서버 로직
└── ...
```

### 현재 필요성
- ❌ 여러 시작점이 실제로 필요하지 않음
- ❌ HTTP 서버는 별도 `uvicorn` 명령으로 실행
- ❌ `__main__.py`는 단순 wrapper일 뿐

### 선택지

#### ✅ 선택 1: `__main__.py` 유지 (현재)
**장점:**
- 패키지 진입점 관례 따름
- 향후 확장성 좋음
- `Claude Desktop: python -m mcp_api_server` 깔끔

**단점:**
- 파일 하나 추가
- 현재는 불필요한 wrapper

#### ✅ 선택 2: `__main__.py` 제거 (간단)
**장점:**
- 파일 줄임
- 간단하고 직관적
- 현재 상황에 적합

**단점:**
- `mcp_cli.py`에 `if __name__ == "__main__":` 추가 필요
- `Claude Desktop: python -m mcp_api_server.mcp_cli` (조금 길어짐)

---

## 💡 결론

`__main__.py`는 **필수가 아니라 선택**입니다.

### 언제 사용할 것인가?

- ✅ **여러 시작점이 있을 때** (모드 선택, 서브커맨드 등)
- ✅ **공개 라이브러리/도구일 때** (관례 따르기)
- ✅ **복잡한 초기화 로직이 필요할 때**

### 언제 불필요한가?

- ❌ **시작점이 하나뿐일 때** (현재 프로젝트)
- ❌ **간단한 프로젝트일 때**
- ❌ **모듈을 직접 실행할 때**

---

## 📌 권장사항

**현재 프로젝트:** 선택 2 (간단하게 정리)
- `mcp_cli.py`에 `if __name__ == "__main__":` 추가
- `__main__.py` 제거
- Claude Desktop: `python -m mcp_api_server.mcp_cli`

**향후:** 필요하면 다시 선택 1로 변경 가능 (언제든 추가 가능)
