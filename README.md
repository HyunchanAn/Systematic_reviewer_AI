# Systematic Reviewer AI (SR-Gemma2)

## 1. 개요

이 프로젝트는 체계적 문헌고찰(Systematic Review) 논문 작성 과정의 일부를 자동화하여 연구자의 부담을 경감시키는 AI 보조 파이프라인을 구축하는 것을 목표로 합니다. 로컬에서 구동되는 Ollama 기반의 Gemma 2 언어 모델을 기반으로, 문헌 검색, 스크리닝, 데이터 추출, 비뚤림 위험 평가, 보고서 생성 등의 작업을 효율화합니다.

최신 버전에서는 Streamlit 기반의 웹 UI를 제공하여 별도의 코드 수정 없이 직관적으로 파이프라인을 제어할 수 있습니다.

## 2. 주요 기능 및 구성 요소

-   문헌 검색 및 수집 (Ingestion): PubMed API를 활용하여 PICO 질문에 기반한 검색 쿼리를 자동 생성하고 문헌 메타데이터를 수집합니다. 미래 출판 예정 논문은 자동으로 필터링됩니다.
-   자동 스크리닝 (Automated Screening): LLM을 활용하여 수집된 논문의 제목과 초록을 분석하고, 사전에 정의된 PICO 기준에 따라 포함/제외 여부를 자동으로 판별합니다.
-   PDF 다운로드 (PDF Download): Unpaywall 및 PubMed Central(PMC)을 통해 오픈 액세스 PDF를 자동으로 다운로드합니다.
-   PDF 파싱 (Parsing): GROBID를 이용해 PDF를 구조화된 TEI/XML로 변환하여 본문을 추출합니다.
-   비뚤림 위험 평가 (RoB Assessment): LLM을 활용하여 전체 텍스트(Full Text)에서 5가지 영역(무작위 배정, 중재 이탈, 결측치, 결과 측정, 보고 비뚤림)에 대한 비뚤림 위험을 자동으로 평가합니다.
-   데이터 추출 (Extraction): PICO 프레임워크 기반의 핵심 정보를 추출하여 CSV로 저장합니다.
-   자동 보고서 생성 (Automated Reporting): 분석된 통계와 추출 결과를 바탕으로 PRISMA 흐름도가 포함된 마크다운(Markdown) 보고서를 생성합니다. 한국어 및 영어 보고서를 지원합니다.
-   웹 인터페이스 (Web UI): Streamlit 기반의 대시보드를 통해 검색부터 보고서 생성까지의 전 과정을 시각적으로 관리할 수 있습니다.

## 3. 프로젝트 구조

```
.
├── data/             # 파이프라인 실행 중 생성되는 모든 데이터를 저장하는 폴더.
├── models/           # 대규모 언어 모델 파일 저장 (Ollama 사용 시 불필요하나 구조 유지).
├── src/              # 파이프라인의 핵심 로직을 담고 있는 소스 코드 디렉터리.
│   ├── ingest/       # PubMed 검색 및 PDF 다운로드 모듈.
│   ├── parse/        # GROBID 파싱 및 텍스트 추출 모듈.
│   ├── screen/       # LLM 기반 자동 스크리닝 모듈.
│   ├── rob/          # 비뚤림 위험(RoB) 평가 모듈.
│   ├── llm/          # Ollama 클라이언트.
│   ├── extract/      # 데이터 추출 모듈.
│   ├── report/       # 보고서 생성 모듈.
│   └── utils/        # 공통 유틸리티 함수.
├── picos_config.yaml # PICO 연구 질문 설정 파일.
├── app.py            # Streamlit 웹 애플리케이션 실행 파일.
├── main.py           # CLI 기반 메인 실행 스크립트.
├── requirements.txt  # Python 라이브러리 의존성 목록.
└── reference_materials/ # 개발 로그 및 참고 자료.
```

## 4. 설치 및 환경 설정

1.  사전 요구사항
    -   Git
    -   Python 3.9 이상
    -   Docker Desktop (GROBID 실행용)
    -   Ollama (LLM 실행용)

2.  LLM 및 도구 준비
    -   Ollama 설치 후 gemma2:9b-instruct 모델 다운로드: `ollama pull gemma2`
    -   Docker Desktop 실행 및 GROBID 서비스 시작 (제공된 `start_services.bat` 관리자 권한 실행 권장)

3.  Python 의존성 설치
    ```bash
    pip install -r requirements.txt
    ```

## 5. 사용법 (Web UI)

가장 권장되는 실행 방식입니다.

1.  앱 실행
    터미널에서 다음 명령어를 입력합니다. (포트 충돌 방지를 위해 8502 포트 사용 권장)
    ```bash
    python -m streamlit run app.py --server.port 8502
    ```

2.  웹 브라우저 접속
    브라우저가 자동으로 열리거나, `http://localhost:8502`로 접속합니다.

3.  주요 탭 기능
    -   1. Search (PICO): 연구 질문(PICO) 입력, 검색 쿼리 생성 및 PubMed 검색 실행.
    -   2. Screening: 검색된 논문을 확인하고 AI 자동 스크리닝 실행.
    -   3. Analysis Pipeline: PDF 다운로드 -> 파싱 -> RoB 평가 -> 데이터 추출 과정을 순차적으로 실행.
    -   4. Report: 최종 보고서(PRISMA 다이어그램 포함) 생성 및 다운로드. 한글/영어 토글 지원.

## 6. 사용법 (CLI)

기존의 터미널 기반 실행 방식입니다.

```bash
python main.py
```
`picos_config.yaml` 설정을 기반으로 전체 파이프라인을 순차적으로 수행합니다.

## 7. 수동 PDF 추가

자동 다운로드에 실패한 논문은 수동으로 추가하여 처리할 수 있습니다.
1. PDF 직접 다운로드.
2. 파일명을 `{PMID}.pdf`로 변경 (예: 12345678.pdf).
3. `data/pdf/` 폴더로 이동.
4. 앱 또는 스크립트 재실행 (이미 처리된 단계는 건너뛰고 진행).

## 8. 개발 로그

프로젝트의 상세한 개발 과정은 `reference_materials/Development_log.txt`에 기록되어 있습니다.