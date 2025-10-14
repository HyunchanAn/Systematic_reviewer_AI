이 디렉터리는 Systematic Reviewer AI 파이프라인의 모든 데이터 산출물을 저장합니다.
각 하위 폴더의 역할은 다음과 같습니다.

1. raw/
   - 역할: 외부 소스(예: PubMed)에서 수집한 원본 데이터를 그대로 저장하는 곳입니다.
   - 주요 파일:
     - articles.xml: PubMed에서 검색된 논문들의 서지 정보와 초록이 담긴 원본 XML 파일입니다.

2. tables/
   - 역할: 파이프라인을 거치며 추출되고 정제된 데이터를 표(테이블) 형태로 저장하는 곳입니다. 주로 CSV 파일 형식을 사용합니다.
   - 주요 파일:
     - retrieved_pmids.csv: PubMed 검색을 통해 수집된 논문들의 고유 ID(PMID) 목록입니다.
     - (향후) screening_results.csv: 스크리닝 후 포함/제외된 논문 목록이 저장됩니다.
     - (향후) extracted_data.csv: LLM이 각 논문에서 추출한 PICO, 결과 등의 데이터가 저장됩니다.

3. tei/
   - 역할: (향후 사용될 폴더) GROBID 도구를 사용하여 PDF 원문 파일을 파싱한 결과물인 TEI/XML 파일이 저장될 예정입니다. 이 구조화된 데이터를 바탕으로 LLM이 정보를 추출하게 됩니다.
