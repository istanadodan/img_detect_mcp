# MCP API Server — 개발 규약 및 환경 가이드

## 프로젝트 개요

YOLOv8 이미지 분석 기능을 제공하는 Model Context Protocol (MCP) 서버입니다. Claude와 같은 AI 에이전트가 이미지를 분석하고 임베딩할 수 있도록 합니다.

**핵심 기능:**
- YOLOv8을 이용한 이미지 객체 감지
- 감지된 객체 자동 crop 및 base64 인코딩
- 외부 임베딩 서버(192.168.0.100:7997)를 통한 벡터 임베딩
- MCP 프로토콜 준수 (3가지 전송 방식 지원)
  - **StdIO:** 로컬 MCP 클라이언트 (Claude.app 등)
  - **HTTP/JSON-RPC:** 네트워크 기반 (원격 배포 가능)
  - **WebSocket:** 저지연 양방향 통신

---

## 개발 환경

### 필수 요구사항
- **Python:** 3.13.3 이상
- **패키지 매니저:** `uv` ([설치 가이드](https://docs.astral.sh/uv/getting-started/installation/))
- **가상환경:** 자동 생성 (`.venv`)

### 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다:

```bash
cat > .env << EOF
# 임베딩 서버
EMBEDDING_HOST=http://192.168.0.100:7997
EMBEDDING_MODEL=openai/clip-vit-large-patch14

# YOLOv8 설정
YOLO_MODEL=yolov8n.pt
YOLO_HOME=./src/mcp_api_server/models
YOLO_CONF_THRESHOLD=0.5

# MCP 서버
MCP_SERVER_NAME=mcp-api-server
LOG_LEVEL=INFO
EOF
```

---

## 주요 명령어

### 의존성 설치
```bash
uv sync
```

### MCP 서버 실행 (3가지 방식)

**1. StdIO 기반 (로컬 MCP 클라이언트용)**
```bash
uv run python -m mcp_api_server.mcp_cli
```
- Claude.app에서 직접 사용
- 표준 입출력(stdin/stdout) 통신

**2. HTTP/JSON-RPC 기반 (네트워크 기반, 권장)**
```bash
# FastAPI 개발 모드
uv run uvicorn src.mcp_api_server.main:app --reload

# 프로덕션 모드 (4 워커)
uv run uvicorn src.mcp_api_server.main:app --workers 4
```
- 엔드포인트: `POST /mcp/messages` (JSON-RPC 2.0)
- 원격 네트워크 접근 가능
- 별도 노드에서 독립적으로 배포 가능

**3. WebSocket 기반 (저지연 양방향 통신)**
```bash
# FastAPI 실행 후 사용
uv run uvicorn src.mcp_api_server.main:app
```
- 엔드포인트: `WS /mcp/ws`
- 지속적인 연결, 낮은 지연시간
- 스트리밍 응답에 최적화

**HTTP 엔드포인트:**
- 헬스 체크: `GET /health` → `{"status": "ok"}`
- 서버 정보: `GET /info` → 버전, 프로토콜, 전송 방식 정보
- MCP 메시지: `POST /mcp/messages` → JSON-RPC 2.0 요청/응답
- WebSocket: `WS /mcp/ws` → 양방향 JSON-RPC 통신

### 테스트 실행
```bash
uv run pytest
uv run pytest -v                    # 상세 출력
uv run pytest tests/test_image_analysis.py -v
```

### Lint 및 코드 포맷팅
```bash
# 린트 검사
uv run ruff check .

# 자동 포맷팅
uv run ruff format .

# 린트 + 포맷 함께
uv run ruff check . && uv run ruff format .
```

---

## 코드 규약

### 네이밍 컨벤션
- **함수/변수:** `snake_case` (예: `analyze_image`, `image_base64`)
- **클래스:** `PascalCase` (예: `ImageDetection`, `Settings`)
- **상수:** `UPPER_SNAKE_CASE` (예: `DEFAULT_TIMEOUT`, `MAX_IMAGE_SIZE`)
- **비공개 함수:** `_leading_underscore` (예: `_get_yolo_model`)

### 타입 힌팅 (필수) — Pylance 규칙

**모든 함수는 파라미터와 반환값에 type hint를 작성해야 합니다. Pylance strict mode 준수.**

```python
# ✅ 올바른 예
async def analyze_image(
    image_base64: str,
    conf_threshold: float | None = None,
) -> TextContent:
    """Analyze an image using YOLOv8."""
    ...

# ❌ 잘못된 예
async def analyze_image(image_base64, conf_threshold=None):  # Pylance error
    ...
```

**Pylance 설정 (권장):**

`.vscode/settings.json`:
```json
{
  "python.analysis.typeCheckingMode": "strict",
  "python.linting.enabled": true,
  "python.linting.pylanceEnabled": true
}
```

**주의 사항:**
- 함수 파라미터의 타입을 명시할 수 없으면 `Any` 사용 금지 → 리팩토링 필요
- 변수 초기화 시 명시적 타입 표기:
  ```python
  # ✅ 좋음
  embedding: list[float] | None = None
  detections: list[Detection] = []
  
  # ❌ Pylance 경고
  embedding = None  # Pylance: Type of "embedding" is partially unknown
  ```
- `Dict`, `List` 대신 `dict`, `list` 사용 (Python 3.12+)
- 예외 처리 시 구체적인 예외 타입 명시:
  ```python
  # ✅ 좋음
  try:
      embedding = await _get_embedding(crop_b64)
  except httpx.HTTPError:
      embedding = None
  
  # ❌ Pylance 경고
  except Exception:  # Too generic
      pass
  ```

### Pydantic 모델 사용 (권장)

복잡한 데이터 구조는 **Pydantic 모델**로 정의하여 타입 안정성과 자동 검증을 확보합니다.

```python
from pydantic import BaseModel, Field

class Detection(BaseModel):
    """Single object detection result."""
    class_name: str = Field(..., description="Detected class name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bbox: list[float] = Field(..., description="[x1, y1, x2, y2]")
    embedding: list[float] | None = Field(None, description="Embedding vector")

class AnalysisResult(BaseModel):
    """Image analysis result."""
    detections: list[Detection] = Field(..., description="List of detections")
    total_objects: int = Field(..., ge=0)
```

**사용 예:**
```python
detections = [Detection(class_name="person", confidence=0.91, bbox=[...], embedding=[...])]
result = AnalysisResult(detections=detections, total_objects=len(detections))
return result.model_dump_json()
```

### Docstring

공개 함수와 클래스는 한 줄 요약 docstring을 작성합니다. 상세 설명이 필요하면 추가로 작성합니다.

```python
def _get_yolo_model() -> YOLO:
    """Load YOLOv8 model (lazy loading)."""
    ...

async def _get_embedding(image_base64: str) -> list[float]:
    """
    Get embedding for an image by calling external embedding API.

    Args:
        image_base64: Base64-encoded image data

    Returns:
        Embedding vector as list of floats

    Raises:
        httpx.HTTPError: If embedding API call fails
    """
    ...
```

### 코드 스타일

- **린터:** `ruff` (line-length: 100)
- **포맷터:** `ruff format`
- **라인 길이:** 100자 (pyproject.toml에서 설정)

---

## MCP 개발 규약

### Tool (도구) 등록

MCP Tool은 항상 `list_tools()` 와 `call_tool()` 핸들러 쌍으로 등록합니다. 
데코레이터로 자동 등록되므로, 다양한 전송 방식(StdIO, HTTP, WebSocket)에서 일관되게 작동합니다.

```python
from mcp.types import Tool

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="analyze_image",
            description="Analyze image with YOLOv8 and get embeddings",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string"},
                    "conf_threshold": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["image_base64"],
            },
        ),
    ]

@mcp_server.call_tool()  # type: ignore
async def analyze_image(image_base64: str, conf_threshold: float | None = None) -> str:
    """Process tool call (used by StdIO and protocol layers)."""
    result = await analyze_image_impl(image_base64, conf_threshold)
    return result.model_dump_json()
```

**중요:** `call_tool()` 데코레이터가 있는 함수는 StdIO 기반 MCP 프로토콜에서만 호출됩니다.
HTTP/WebSocket에서는 구현 함수(`analyze_image_impl`)를 직접 호출합니다.

### Resource (리소스) 등록

```python
@mcp_server.list_resources()
async def list_resources() -> list[Resource]:
    ...

@mcp_server.read_resource()
async def read_resource(uri: str) -> str:
    ...
```

### Prompt (프롬프트) 등록

```python
@mcp_server.list_prompts()
async def list_prompts() -> list[Prompt]:
    ...

@mcp_server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
    ...
```

### 파일 구조

- 각 기능은 별도 파일로 분리: `tools/`, `resources/`, `prompts/`
- MCP 서버 인스턴스는 `server.py`에서 관리
- Tool 등록은 decorator로 자동 처리

**동작 흐름:**

```
mcp_cli.py (진입점)
  └─> register_tools() 호출
      └─> tools 모듈 import
          └─> 각 tool 파일의 @mcp_server.call_tool() 데코레이터 실행
              └─> Tool 등록 완료
  └─> stdio_server() 시작
      └─> StdIO를 통해 MCP 클라이언트와 통신
```

**코드 예시:**

```python
# tools/__init__.py
from .image_analysis import register_image_analysis_tool
__all__ = ["register_image_analysis_tool"]

# server.py
async def register_tools() -> None:
    """Register all MCP tools by importing tool modules."""
    from . import tools  # noqa: F401

# mcp_cli.py
async def main() -> None:
    """Run MCP server with stdio transport."""
    from .server import mcp_server, register_tools
    await register_tools()
    async with stdio_server(mcp_server) as streams:
        await streams.keep_alive()
```

---

## YOLOv8 + 임베딩 Tool 설계

### `analyze_image` Tool

**입력 스키마:**
```json
{
  "image_path": "string (절대 경로, PNG/JPEG)",
  "conf_threshold": "number (0-1, optional, 기본값: 0.5)"
}
```

**처리 흐름:**

1. 파일 경로 → PIL Image 로드 (RGB 변환)
2. 이미지를 1024×1024로 리사이징 (LANCZOS 필터)
3. YOLOv8 모델로 객체 감지 (리사이징된 이미지 사용)
   ```python
   results = model.predict(image_resized, conf=conf_threshold, verbose=False)
   ```
4. 감지된 각 객체에 대해:
   - Bounding box 추출 (리사이징된 좌표)
   - 해당 영역 crop (리사이징된 이미지에서)
   - Crop 이미지 → PNG → base64
   - 임베딩 API 호출 (비동기)
5. 결과 AnalysisResult Pydantic 모델로 직렬화

**출력 (MCP TextContent):**
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

### Tool 등록

`register_image_analysis_tool()` 함수에서 명시적으로 등록:

```python
def register_image_analysis_tool() -> None:
    """Register image analysis tool handlers."""
    # 1. YOLOv8 모델 미리 로드 (첫 요청 응답 시간 단축)
    logger.info("Pre-loading YOLOv8 model...")
    _get_yolo_model()
    
    # 2. Tool 핸들러 명시적 등록
    mcp_server.call_tool()(analyze_image)  # type: ignore
    mcp_server.list_tools()(list_tools)    # type: ignore
    logger.info("Image analysis tool registered")
```

**장점:**
- YOLOv8 모델을 서버 시작 시 미리 로드 → 첫 요청 응답 시간 단축
- 명시적 등록으로 초기화 순서 명확화
- Tool 로드 실패 시 즉시 감지

### 에러 처리

- **임베딩 API 장애:** 기본 영벡터(모두 0, 768차원)로 설정하고 계속 진행
- **파일 로드 실패:** `FileNotFoundError` 발생 → MCP 프로토콜 에러 반환
- **YOLOv8 로드 실패:** 도구 등록 시점에 감지

```python
# 임베딩 API 실패 처리
try:
    embedding = await _get_embedding(crop_b64)
except Exception as e:
    embedding_dim = 768  # CLIP 모델 기본 차원
    embedding = [0.0] * embedding_dim
    logger.warning(f"Failed to get embedding: {e}. Using default zero vector.")
```

---

## 임베딩 서버 구성 (192.168.0.100)

### 방법 1: Infinity Embedding Server (권장)

CLIP 계열 이미지 임베딩에 최적화된 경량 서버.

```bash
# 설치
pip install "infinity-emb[all]"

# 실행 (CUDA 지원)
infinity_emb v2 --model-id openai/clip-vit-large-patch14 --port 7997 --device cuda
```

**API 스펙:**
```bash
curl -X POST http://192.168.0.100:7997/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/clip-vit-large-patch14",
    "input": ["<base64_encoded_image>"]
  }'
```

**응답:**
```json
{
  "data": [
    {
      "embedding": [0.12, -0.34, ..., ]
    }
  ]
}
```

### 방법 2: Docker (LocalAI)

```bash
docker run -p 8080:8080 \
  -v $(pwd)/models:/build/models \
  localai/localai:latest \
  clip_image_embeddings
```

포트를 `.env`에서 `EMBEDDING_HOST`로 설정:
```env
EMBEDDING_HOST=http://192.168.0.100:8080
```

### 방법 3: 직접 FastAPI 구축

```python
# embed_server.py (192.168.0.100에서 실행)
from fastapi import FastAPI
from transformers import CLIPModel, CLIPProcessor
from PIL import Image
import torch, base64, io

app = FastAPI()
model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

@app.post("/embeddings")
async def embed(payload: dict):
    img_bytes = base64.b64decode(payload["input"][0])
    image = Image.open(io.BytesIO(img_bytes))
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    return {"data": [{"embedding": features[0].tolist()}]}
```

---

## 테스트 규약

### 파일 구조
- 테스트 파일명: `test_*.py` 또는 `*_test.py`
- 테스트 경로: `tests/` 디렉토리

### 비동기 테스트

`pytest.mark.asyncio` 데코레이터 사용:

```python
import pytest
from httpx import AsyncClient
from src.mcp_api_server.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

### Tool 테스트

```python
@pytest.mark.asyncio
async def test_analyze_image_empty():
    """Test analyze_image with empty detections."""
    # Create a blank white image
    from PIL import Image
    import base64, io
    
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Call tool
    result = await analyze_image_impl(img_b64)
    
    # Check result is valid JSON
    import json
    parsed = json.loads(result)
    assert isinstance(parsed, list)
```

### Fixtures

공용 fixtures는 `tests/conftest.py`에서 정의:

```python
# tests/conftest.py
import pytest
from PIL import Image
import base64, io

@pytest.fixture
def sample_image_base64():
    """Generate a sample 100x100 white image."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")
```

---

## Git 규약

### 커밋 메시지

Conventional Commits 형식 준수:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**타입:**
- `feat:` 새 기능
- `fix:` 버그 수정
- `docs:` 문서 추가/수정
- `refactor:` 코드 구조 개선 (기능 변화 없음)
- `test:` 테스트 추가/수정
- `chore:` 빌드 설정, 의존성 업데이트 등

**예:**
```
feat(tools): add analyze_image MCP tool for YOLOv8 detection

- Implement YOLOv8-based object detection
- Integrate embedding API for detected objects
- Add Pydantic models for type safety

Closes #42
```

### 브랜치 전략

- **main:** 기본 브랜치 (direct push 금지)
- **개발 브랜치:** `feature/`, `fix/` 프리픽스 사용
  ```bash
  git checkout -b feature/analyze-image
  git checkout -b fix/embedding-timeout
  ```

### Pull Request

1. 기능별 브랜치에서 작업
2. 커밋 메시지는 Conventional Commits 준수
3. `main`으로 PR 생성 (코드 리뷰)
4. 최소 1명 승인 후 merge

---

## 프로젝트 구조 개요

```
mcp-api-server/
├── .git/                           # Git 저장소
├── .gitignore
├── .python-version                 # Python 3.12
├── .env.example                    # 환경변수 템플릿
├── pyproject.toml                  # uv 프로젝트 설정
├── uv.lock                         # 잠금 파일 (커밋)
├── README.md
├── CLAUDE.md                       # 이 파일
├── src/
│   └── mcp_api_server/
│       ├── __init__.py
│       ├── main.py                 # FastAPI + MCP 진입점
│       ├── server.py               # MCP 서버 인스턴스
│       ├── config.py               # 환경변수 설정 (Pydantic)
│       ├── tools/
│       │   ├── __init__.py
│       │   └── image_analysis.py   # YOLOv8 + 임베딩 Tool
│       ├── resources/
│       │   └── __init__.py
│       └── prompts/
│           └── __init__.py
└── tests/
    ├── __init__.py
    ├── conftest.py                 # pytest fixtures
    └── test_*.py                   # 테스트 파일들
```

---

## 트러블슈팅

### YOLOv8 모델 자동 다운로드 문제

첫 실행 시 모델이 자동으로 다운로드됩니다 (`~/.cache/ultralytics/`).

```bash
# 네트워크 불안정 시 사전 다운로드
python -m ultralytics.nn.tasks import AutoBackend
from ultralytics import YOLO
YOLO("yolov8n.pt")
```

### 임베딩 API 타임아웃

`.env` 설정 및 네트워크 확인:
```bash
# 임베딩 서버 접근 가능한지 확인
curl http://192.168.0.100:7997/health
```

### Ruff 포맷 자동화

VS Code 설정:
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

---

## 참고 자료

- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [uv 패키지 매니저](https://docs.astral.sh/uv/)
