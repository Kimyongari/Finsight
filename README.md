# Finsight: AI 금융 분석 어시스턴트
Track1: AI Agent 개발 <K intelligence 해커톤 2025> 수상작 (3위)
## 1. 프로젝트 소개

FinSight는 포괄적인 금융 정보와 분석을 제공하기 위해 설계된 AI 기반 금융 어시스턴트입니다. 사용자의 질문에 통찰력 있는 답변을 제공하기 위해 다양한 데이터 소스와 AI 기술을 통합합니다.

주요 기능은 다음과 같습니다:
- **기업 재무 분석**: DART(전자공시시스템) 데이터를 사용하여 기업의 재무제표를 추출하고 분석합니다.
- **RAG 기반 Q&A**: 검색 증강 생성(RAG) 기술을 사용하여 금융 규정 및 문서 등 사전 구축된 지식 베이스를 기반으로 사용자의 질문에 답변합니다.
- **리포트 자동 생성**: 특정 기업에 대한 심층 분석 리포트를 자동으로 생성합니다.
- **웹 검색 통합**: 웹 검색 에이전트를 활용하여 실시간 또는 일반 상식 질문에 대한 답변을 찾습니다.

백엔드는 **FastAPI**로 구축되었으며, RAG 파이프라인의 효율적인 유사도 검색을 위해 **Weaviate**를 벡터 데이터베이스로 사용합니다.

#### 시연 영상
- [Report Agent](https://www.youtube.com/watch?v=xQm8__sc2js)
- [RAG Agent](https://www.youtube.com/watch?v=BaZBrlYc3Uc)

## 2. 프로젝트 구조

프로젝트는 백엔드와 프론트엔드 구조로 구성되어 있습니다. 핵심 로직은 `backends` 디렉토리에 있습니다.

```
Finsight/
├───backends/
│   ├───main.py                # FastAPI 애플리케이션 진입점
│   ├───app/
│   │   ├───core/                # 핵심 비즈니스 로직 (DART 추출기, LLM, RAG, VDB)
│   │   ├───routers/             # API 엔드포인트 정의
│   │   ├───schemas/             # Pydantic 요청/응답 모델
│   │   └───services/            # 각 라우터의 비즈니스 로직
│   └───...
├───docker-compose.yml         # 서비스용 Docker 설정 (예: Weaviate)
├───requirements.txt           # Python 의존성 파일
└───...
```

## 3. 엔드포인트

API는 각각 특정 도메인을 처리하는 여러 라우터로 나뉘며, 각 라우터에는 접두사(prefix)가 적용되어 있습니다.

### `/financial`
- **`GET /financial/health`**: financial 라우터의 상태를 확인합니다.
- **`POST /financial/statement`**: 주어진 회사 코드에 대한 재무제표를 가져옵니다.
  - **Request Body**: `{"company_code": "005930"}`

### `/rag`
- **`GET /rag/health`**: RAG 라우터의 상태를 확인합니다.
- **`POST /rag/query`**: 사용자의 질문을 받아 RAG 파이프라인을 통해 생성된 답변을 반환합니다.
  - **Request Body**: `{"query": "전자금융거래법의 주요 내용은 무엇인가요?"}`

### `/report`
- **`GET /report/{stock_code}`**: 지정된 종목 코드에 대한 상세 기업 분석 리포트를 마크다운 형식으로 생성합니다.
  - **Path Parameter**: `stock_code` (예: 삼성전자 - `005930`).

### `/web-agent`
- **`POST /web-agent/agent/web-search`**: 사용자의 질문으로 웹 검색 에이전트를 실행하고 최종 답변을 반환합니다.
  - **Request Body**: `{"question": "2008년 금융 위기의 주요 원인은 무엇이었나요?"}`

## 4. 시작하기

### 사전 요구사항
- Python 3.11
- Node.js 20+
- Docker 및 Docker Compose
- `backends/.env` 구성:
```
OPENDART_API_KEY=            # DART OpenAPI 키
SEARCHAPI_KEY=               # searchapi.io 키 (웹 검색)
OPENROUTER_KEY=              # OpenRouter 키 (LLM + 임베딩 공용)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MODEL=google/gemini-3.5-flash-lite   # 생성 모델
EMBEDDING_MODEL_NAME=baai/bge-m3     # 임베딩 모델 (1024차원)
WEAVIATE_URL=http://localhost:8090   # 로컬 실행 시. 컨테이너에서는 compose가 덮어씀
```

> 임베딩은 OpenRouter의 `baai/bge-m3`(1024차원)를 사용합니다.
> LLM과 임베딩이 같은 키/엔드포인트를 쓰므로 별도 임베딩 제공자 설정이 필요 없습니다.

### 설치 및 설정

1.  **Repository Clone**
    ```bash
    git clone https://github.com/Kimyongari/Finsight.git
    cd Finsight
    ```

2.  **전체 스택을 Docker로 실행**
    ```bash
    docker compose up -d --build
    ```
    - Weaviate: http://localhost:8090
    - 백엔드: http://localhost:8000 (API 문서 http://localhost:8000/docs)
    - 프론트엔드: http://localhost:5173

3.  **로컬에서 개별 실행 (개발용)**
    ```bash
    # 벡터 DB만 컨테이너로
    docker compose up -d weaviate

    # 백엔드
    cd backends
    python3.11 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python -m uvicorn main:app --port 8000

    # 프론트엔드 (별도 터미널)
    cd frontends/corp-advisor--app
    npm install
    npm run dev     # VITE_API_URL 은 .env 로 주입 (기본 http://localhost:8000)
    ```

4.  **법령 문서 적재 (최초 1회)**
    `backends/pdfs/` 의 PDF를 청크로 나눠 임베딩 후 Weaviate에 적재합니다.
    ```bash
    curl http://localhost:8000/rag/initialize
    ```
    적재 현황 확인:
    ```bash
    curl http://localhost:8000/rag/show_files_in_collection
    ```
