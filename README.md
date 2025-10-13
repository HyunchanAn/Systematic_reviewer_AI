## 1. 개요

이 프로젝트는 체계적 문헌고찰(Systematic Review) 논문 작성 과정의 일부를 자동화하여 연구자의 부담을 경감시키는 AI 보조 파이프라인을 구축하는 것을 목표로 합니다. 로컬에서 구동되는 Gemma 3 언어 모델을 기반으로, 문헌 검색, 스크리닝, 데이터 추출 등의 작업을 효율화합니다.

## 2. 주요 기능 및 구성 요소

-   문헌 검색 및 수집 (Ingestion): PubMed API를 활용하여 키워드 기반으로 관련 논문의 메타데이터를 수집합니다.
-   PDF 파싱 (Parsing): GROBID를 이용해 PDF 논문을 구조화된 TEI/XML 형식으로 변환하여 텍스트, 저자, 초록, 참고문헌 등을 분리합니다.
-   LLM 기반 보조 (LLM Assistance): 로컬 `llamafile`로 실행되는 Gemma 3 모델을 통해 논문 내용 요약, PICO 프레임워크 기반 정보 추출 등을 보조합니다.
-   스크리닝 (Screening): ASReview의 액티브 러닝(Active Learning) 기술을 연동하여, 최소한의 라벨링으로 대규모 문헌을 효율적으로 스크리닝하는 것을 목표로 합니다.
-   RoB 평가 보조 (Risk of Bias): RobotReviewer를 보조 도구로 활용하여 편향 위험 평가의 초안을 생성합니다.

## 3. 프로젝트 구조

```
.
├── data/             # 데이터 (raw, tei, tables)
├── models/           # LLM 모델 파일(.llamafile) 저장 위치
├── notebooks/        # 실험 및 테스트용 Jupyter 노트북
├── src/              # 메인 소스 코드
│   ├── ingest/       # 데이터 수집 모듈
│   ├── parse/        # PDF 파싱 모듈
│   ├── screen/       # 스크리닝 보조 모듈
│   ├── llm/          # LLM 클라이언트
│   ├── extract/      # 정보 추출 모듈
│   ├── rob/          # RoB 보조 모듈
│   └── report/       # 보고서 생성 모듈
├── tools/            # 외부 오픈소스 도구 (ASReview, GROBID, RobotReviewer)
├── picos_config.yaml # PICOS 연구 질문 설정 파일
├── start_services.bat# 핵심 서비스(GROBID, LLM 서버) 시작 스크립트 (Windows용)
├── main.py           # 메인 실행 스크립트
├── requirements.txt  # Python 의존성 목록
└── reference_materials/ # 개발 로그, 메모, 예제 파일 등 보조 자료
```

## 4. 설치 및 환경 설정

1.  **사전 요구사항**
    -   Git
    -   Python 3.9 이상
    -   Docker Desktop

2.  **외부 도구 및 모델 준비**
    -   이 프로젝트는 `git clone` 시 `tools` 디렉터리에 필요한 오픈소스 도구(ASReview, GROBID 등)를 함께 다운로드합니다.
    -   Hugging Face 등에서 `google_gemma-3-12b-it-Q4_K_M.llamafile`과 같은 Gemma 3 모델을 다운로드합니다.
    -   **다운로드한 모델 파일을 이 프로젝트의 `models/` 디렉터리 안으로 이동시킵니다.**

3.  **Python 의존성 설치**
    -   프로젝트 루트에서 가상 환경을 생성하고 활성화하는 것을 권장합니다.
    -   다음 명령어를 실행하여 필요한 라이브러리를 설치합니다.
        ```bash
        pip install -r requirements.txt
        ```

## 5. 사용법

### 5.1. 서비스 시작

1.  **핵심 서비스 실행 (GROBID, LLM 서버)**
    -   프로젝트 루트에 있는 **`start_services.bat` 파일을 더블클릭하여 실행**합니다.
    -   이 스크립트는 백그라운드에서 GROBID Docker 컨테이너를 시작하고, 새 터미널 창에서 Gemma 3 LLM 서버를 실행합니다.
    -   **참고**: `start_services.bat` 파일 내의 `LLM_PATH` 변수를 자신의 `llamafile` 모델 경로에 맞게 수정해야 할 수 있습니다.

### 5.2. 파이프라인 실행

1.  **연구 질문(PICOS) 설정**
    -   프로젝트 루트에 있는 `picos_config.yaml` 파일을 열어 자신의 연구 주제에 맞는 PICOS 질문을 입력하고 저장합니다.
    -   **팁**: `main.py` 실행 시 `picos_config.yaml`이 존재하면 해당 설정을 사용할지 묻고, 없거나 사용하지 않겠다고 하면 대화형으로 입력받을 수 있습니다.

2.  **메인 파이프라인 실행**
    -   모든 서비스가 실행 중인 상태에서, 터미널을 열고 프로젝트 루트에서 다음 명령어로 메인 스크립트를 실행합니다.
        ```bash
        python main.py
        ```
    -   스크립트는 설정된 PICOS를 기반으로 PubMed 검색을 수행하고, 결과를 `data/` 폴더에 저장합니다.

### 5.3. 재사용 워크플로우 (새로운 연구 주제 시작 시)

이 깃허브 저장소는 파이프라인 '템플릿'으로 사용됩니다. 새로운 연구 주제로 작업을 시작할 때는 다음 절차를 따르세요.

1.  **새로운 프로젝트 폴더 생성**: 컴퓨터에 새로운 폴더를 만듭니다. (예: `C:\My_Reviews\New_Research_Topic_SR`)
2.  **템플릿 복사**: 깃허브에서 클론(clone)해 둔 이 파이프라인 코드 전체를 새로 만든 폴더에 복사합니다.
3.  **독립적인 작업**: 복사된 새 폴더 안에서 `picos_config.yaml`을 수정하고 `main.py`를 실행하는 등 모든 작업을 진행합니다. 이렇게 하면 각 연구의 데이터가 서로 섞이지 않고 독립적으로 관리됩니다.

## 6. 개발 로그

-   프로젝트의 상세한 진행 과정과 계획은 `reference_materials/Development_log.txt` 파일에 기록되어 있습니다.