# MCP API 서버

FastAPI 기반의 Model Context Protocol (MCP) 서버로, YOLOv8 이미지 분석과 임베딩 통합을 지원합니다.

## 프로젝트 개요

이 프로젝트는 Claude와 같은 AI 에이전트가 이미지 분석 기능을 활용할 수 있도록 MCP 프로토콜을 통해 제공합니다.

**주요 기능:**
- YOLOv8 기반 객체 감지 (Object Detection)
- 감지된 객체 자동 크롭 및 base64 인코딩
- 외부 임베딩 서버를 통한 벡터 임베딩 (192.168.0.100:7997)
- FastAPI를 통한 MCP 프로토콜 지원 (SSE + StreamableHTTP)

---

## 시스템 요구사항

- **Python:** 3.13.3 이상
- **패키지 매니저:** `uv` ([설치 가이드](https://docs.astral.sh/uv/getting-started/installation/))
- **메모리:** 2GB 이상 (YOLOv8 모델 로드용)
- **네트워크:** 임베딩 서버(192.168.0.100:7997) 접근 가능

---

## 빠른 시작

### 1단계: 의존성 설치

```bash
# 프로젝트 루트에서 실행
uv sync
```

이 명령어는 자동으로:
- `.venv/` 가상환경 생성
- 모든 의존성 설치 (FastAPI, YOLOv8, MCP 등)
- `uv.lock` 파일 생성 (재현 가능한 환경)

### 2단계: 환경 설정

프로젝트 루트에 `.env` 파일을 생성합니다:

```bash
# .env 파일 생성
cat > .env << EOF
# 임베딩 서버 설정
EMBEDDING_HOST=http://192.168.0.100:7997
EMBEDDING_MODEL=openai/clip-vit-large-patch14

# YOLOv8 모델 설정
YOLO_MODEL=yolov8n.pt
YOLO_HOME=./src/mcp_api_server/models
YOLO_CONF_THRESHOLD=0.5

# MCP 서버 설정
MCP_SERVER_NAME=mcp-api-server
LOG_LEVEL=INFO
EOF
```

**설정 항목 설명:**

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `EMBEDDING_HOST` | `http://192.168.0.100:7997` | 임베딩 서버 주소 |
| `EMBEDDING_MODEL` | `openai/clip-vit-large-patch14` | 사용할 임베딩 모델 |
| `YOLO_MODEL` | `yolov8n.pt` | YOLOv8 모델 (nano~x) |
| `YOLO_HOME` | `./src/mcp_api_server/models` | 모델 다운로드 디렉토리 (프로젝트 루트 기준 상대경로) |
| `YOLO_CONF_THRESHOLD` | `0.5` | 감지 신뢰도 임계값 (0~1) |
| `MCP_SERVER_NAME` | `mcp-api-server` | MCP 서버 이름 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG/INFO/WARNING) |

**YOLOv8 모델 선택 가이드:**
- `yolov8n.pt` (nano): 가장 빠름, 메모리 적음, 정확도 낮음
- `yolov8s.pt` (small): 균형잡힘 (권장)
- `yolov8m.pt` (medium): 느림, 메모리 많음, 정확도 높음

### 3단계: 서버 실행

**MCP StdIO 서버 (Claude Desktop 연결용):**

```bash
# MCP SDK 방식 (기본값, 권장)
uv run python -m mcp_api_server

# 또는 FastMCP 방식
MCP_SERVER_TYPE=fastmcp uv run python -m mcp_api_server
```

**FastAPI HTTP/WebSocket 서버 (원격 클라이언트용):**

```bash
# 개발 모드 (자동 리로드 활성화)
uv run uvicorn src.mcp_api_server.main:app --reload

# 또는 프로덕션 모드 (4개 워커)
uv run uvicorn src.mcp_api_server.main:app --workers 4
```

**서버 시작 확인:**
- MCP StdIO: 터미널에서 로그 메시지 확인
- FastAPI HTTP: 브라우저에서 `http://localhost:8000/health` 접속 → `{"status": "ok"}`

---

## 프로젝트 구조

```
mcp-api-server/
│
├── .git/                           # Git 저장소
├── .python-version                 # Python 3.13.3
├── .env.example                    # 환경변수 템플릿
├── .gitignore                      # Git 무시 목록
│
├── pyproject.toml                  # 프로젝트 메타데이터 및 의존성
├── uv.lock                         # 의존성 잠금 파일
│
├── README.md                       # 프로젝트 개요 (이 파일)
├── CLAUDE.md                       # 개발 규약 및 환경 가이드
│
├── src/
│   └── mcp_api_server/             # 메인 패키지
│       │
│       ├── __init__.py             # 패키지 초기화
│       ├── main.py                 # FastAPI 진입점 (HTTP/SSE/WebSocket)
│       ├── mcp_cli.py              # MCP StdIO CLI 진입점
│       ├── server.py               # MCP 서버 인스턴스
│       ├── config.py               # 환경변수 설정 (Pydantic)
│       ├── models.py               # Pydantic 데이터 모델
│       ├── logging_config.py       # 로깅 설정
│       │
│       ├── tools/                  # MCP Tool 구현
│       │   ├── __init__.py
│       │   └── image_analysis.py   # YOLOv8 + 임베딩 분석
│       │
│       ├── resources/              # MCP Resource 구현 (선택)
│       │   └── __init__.py
│       │
│       └── prompts/                # MCP Prompt 구현 (선택)
│           └── __init__.py
│
├── examples/                       # 클라이언트 예제
│   ├── http_client.py              # HTTP/JSON-RPC 클라이언트 예제
│   └── websocket_client.py         # WebSocket 클라이언트 예제
│
└── tests/                          # 테스트 스위트
    ├── __init__.py
    ├── conftest.py                 # pytest 공유 fixtures
    ├── test_server.py              # FastAPI 엔드포인트 테스트
    └── test_models.py              # Pydantic 모델 테스트
```

---

## 주요 기능 설명

### `analyze_image` MCP Tool

이미지 파일 경로를 입력받아 객체를 감지하고 임베딩을 추출합니다.

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `image_path` | string | ✅ | 이미지 파일의 절대 경로 (PNG/JPEG) |
| `conf_threshold` | float | ❌ | 감지 신뢰도 임계값 (0~1, 기본값: 0.5) |

**사용 예:**

```python
from src.mcp_api_server.tools.image_analysis import analyze_image_impl
import asyncio

# 이미지 파일 경로로 분석
result = await analyze_image_impl(
    image_path="/path/to/image.jpg",
    conf_threshold=0.5
)

print(result.model_dump_json(indent=2))
```

**반환 결과:**

```json
{
  "detections": [
    {
      "class_name": "person",
      "confidence": 0.91,
      "bbox": [100.0, 50.0, 200.0, 300.0],
      "embedding": [0.12, -0.34, 0.56, ...]
    },
    {
      "class_name": "cat",
      "confidence": 0.78,
      "bbox": [300.0, 100.0, 400.0, 250.0],
      "embedding": [0.11, 0.22, -0.33, ...]
    }
  ],
  "total_objects": 2
}
```

**처리 흐름:**

1. 파일 경로 → PIL Image 로드 (RGB 변환)
2. 이미지를 1024×1024 해상도로 리사이징 (LANCZOS 필터)
3. YOLOv8 모델로 객체 감지 (리사이징된 이미지 사용)
4. 각 객체에 대해:
   - Bounding box 추출
   - 해당 영역을 리사이징된 이미지에서 crop
   - Crop 이미지 → PNG → base64 인코딩
   - 임베딩 서버 API 호출 (`/embeddings`)
   - 임베딩 벡터 추출
5. 결과 JSON 반환

**주요 특징:**
- 파일 경로 기반 입력으로 메모리 효율 향상
- 자동 리사이징으로 일관된 처리 품질
- 임베딩 API 실패 시 기본 영벡터(모두 0) 사용으로 견고성 제공

---

## API 엔드포인트

### 헬스 체크 및 서버 정보

```bash
# 헬스 체크
GET /health
응답: {"status": "ok"}

# 서버 정보
GET /info
응답: {
  "name": "mcp-api-server",
  "version": "0.1.0",
  "protocol": "MCP (Model Context Protocol)",
  "transport": "HTTP/SSE and WebSocket",
  "description": "YOLOv8-based image analysis with embedding integration"
}
```

### MCP HTTP/JSON-RPC 엔드포인트 (네트워크 기반)

**엔드포인트:** `POST /mcp/messages`

FastAPI를 통한 HTTP 기반 MCP 서버로, 네트워크를 통해 원격에서 접근 가능합니다.

**특징:**
- JSON-RPC 2.0 프로토콜 준수
- 네트워크 기반 통신 (원격 배포 가능)
- 비동기 처리
- 별도 노드에서 실행 가능

**사용 예 (Python):**

```python
import asyncio
import httpx

async def call_mcp_tool():
    async with httpx.AsyncClient() as client:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "analyze_image",
                "arguments": {
                    "image_path": "/absolute/path/to/image.jpg",  # 절대 경로
                    "conf_threshold": 0.5
                }
            }
        }
        response = await client.post(
            "http://localhost:8000/mcp/messages",
            json=payload
        )
        print(response.json())

asyncio.run(call_mcp_tool())
```

**이용 가능한 메서드:**
- `initialize` - 서버 초기화
- `tools/list` - 사용 가능한 tool 목록 조회
- `tools/call` - 특정 tool 호출

### MCP WebSocket 엔드포인트

**엔드포인트:** `WS /mcp/ws`

저지연, 양방향 통신이 필요한 경우 WebSocket 사용:

```python
import asyncio
import json
import websockets

async def ws_client():
    async with websockets.connect("ws://localhost:8000/mcp/ws") as ws:
        # 초기화 요청
        await ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }))
        response = await ws.recv()
        print(f"초기화 응답: {response}")

asyncio.run(ws_client())
```

**장점:**
- 지속적인 연결 (latency 낮음)
- 양방향 통신
- 스트리밍 응답에 유리

### MCP 프로토콜 (StdIO 기반)

**로컬 사용:** Claude.app이나 다른 MCP 클라이언트에서 직접 사용

```bash
# StdIO 기반 MCP 서버 실행
uv run python -m mcp_api_server.mcp_cli
```

**Claude에서 설정 (Claude.app):**

```json
{
  "mcpServers": {
    "mcp-api-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_api_server.mcp_cli"],
      "cwd": "D:\works\ai-projects\mcp-api-server\"
    }
  }
}
```

### 예제 클라이언트

`examples/` 디렉토리에 완전한 클라이언트 예제가 있습니다:

```bash
# HTTP 클라이언트 예제 실행
uv run python examples/http_client.py

# WebSocket 클라이언트 예제 실행
uv run python examples/websocket_client.py
```

---

## 개발 명령어

### 테스트 실행

```bash
# 모든 테스트 실행
uv run pytest

# 상세 출력 (-v: verbose)
uv run pytest -v

# 특정 테스트 파일만 실행
uv run pytest tests/test_models.py -v

# 커버리지 리포트
uv run pytest --cov=src
```

### 코드 린트 및 포맷팅

```bash
# 린트 검사 (Ruff)
uv run ruff check .

# 자동 포맷팅
uv run ruff format .

# 린트 + 포맷 함께 실행
uv run ruff check . && uv run ruff format .
```

### 타입 검사 (선택사항)

```bash
# Pylance strict mode 검사를 위해 IDE 사용
# VS Code 설정: python.analysis.typeCheckingMode = "strict"
```

---

## 임베딩 서버 구성

MCP 서버는 192.168.0.100:7997 주소의 임베딩 서버가 필요합니다.

### 방법 1: Infinity Embedding Server (권장)

가장 간단하고 빠른 방법입니다.

```bash
# 설치
pip install "infinity-emb[all]"

# GPU 지원 실행
infinity_emb v2 --model-id openai/clip-vit-large-patch14 --port 7997 --device cuda

# CPU 실행 (GPU 없을 경우)
infinity_emb v2 --model-id openai/clip-vit-large-patch14 --port 7997 --device cpu
```

### 방법 2: Docker로 LocalAI 실행

```bash
docker run -p 8080:8080 \
  -v $(pwd)/models:/build/models \
  localai/localai:latest \
  clip_image_embeddings
```

`.env` 파일에서 포트 수정:
```env
EMBEDDING_HOST=http://192.168.0.100:8080
```

### 방법 3: 직접 FastAPI 임베딩 서버 구축

자세한 내용은 [CLAUDE.md](CLAUDE.md)의 "임베딩 서버 구성" 섹션을 참고하세요.

---

## 트러블슈팅

### YOLOv8 모델이 자동으로 다운로드되지 않음

첫 실행 시 모델이 `.env`에 설정된 `YOLO_HOME` 디렉토리에 자동 다운로드됩니다.
기본값은 프로젝트 루트의 `./models/` 디렉토리입니다.

**해결:**
```bash
# 수동으로 모델 다운로드
YOLO_HOME=./models python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# 또는 서버 실행 (자동 다운로드)
uv run uvicorn src.mcp_api_server.main:app
```

**모델 저장 위치:**
- 설정: `.env` 파일의 `YOLO_HOME=./src/mcp_api_server/models`
- 실제 경로: `프로젝트_루트/src/mcp_api_server/models/`
- `.gitignore`에 등록되어 있음 (커밋 제외)

### 임베딩 API 타임아웃 오류

```
httpx.ConnectError: Could not connect to http://192.168.0.100:7997
```

**확인:**
```bash
# 임베딩 서버 접근 가능 확인
curl http://192.168.0.100:7997/health

# 방화벽 설정 확인
# Windows: Defender 방화벽에서 포트 7997 허용
```

### Ruff 포맷 충돌

VS Code에서 자동 포맷팅을 설정하려면:

```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit"
    }
  }
}
```

### 메모리 부족

YOLOv8 모델이 크면 메모리 부족 오류가 발생할 수 있습니다.

**해결:**
- 더 작은 모델 사용: `yolov8n.pt` 또는 `yolov8s.pt`
- 시스템 메모리 확인
- 다른 프로세스 종료

---

## 개발 규약

모든 개발 규약은 [CLAUDE.md](CLAUDE.md)에 자세히 기술되어 있습니다.

**주요 규약:**
- **언어:** Python 3.13.3
- **타입 힌팅:** Pylance strict mode 준수 (필수)
- **코드 스타일:** Ruff (line-length: 100)
- **커밋 메시지:** Conventional Commits
- **테스트:** pytest + pytest-asyncio
- **데이터 모델:** Pydantic BaseModel 사용

---

## Git 워크플로우

### 새 기능 추가

```bash
# 1. 새 브랜치 생성
git checkout -b feature/새-기능-이름

# 2. 코드 작성 및 테스트
uv run pytest
uv run ruff check .

# 3. 커밋
git add .
git commit -m "feat: 기능 설명"

# 4. 푸시 및 PR 생성
git push -u origin feature/새-기능-이름
```

### 버그 수정

```bash
git checkout -b fix/버그-이름
# ... 수정 ...
git commit -m "fix: 버그 설명"
```

---

## 성능 최적화

### YOLOv8 모델 선택

- **nano (yolov8n.pt):** ~3ms 추론시간, 메모리 100MB 이하
- **small (yolov8s.pt):** ~10ms 추론시간, 메모리 200MB
- **medium (yolov8m.pt):** ~20ms 추론시간, 메모리 400MB

### 임베딩 API 최적화

- Batch 처리: 여러 이미지를 한 번에 임베딩 (향후 구현)
- 캐싱: 같은 이미지 재사용 시 캐시 활용 (향후 구현)

---

## 라이선스

MIT License

---

## 참고 자료

- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [YOLOv8 문서](https://docs.ultralytics.com/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [uv 패키지 매니저](https://docs.astral.sh/uv/)

더 자세한 개발 정보는 [CLAUDE.md](CLAUDE.md)를 참고하세요.
