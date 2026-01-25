import streamlit as st
import os
import pandas as pd
import yaml
import shutil
import time
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# Import existing modules
# We need to add the project root to sys.path if it's not already there for imports to work
import sys
sys.path.append(os.getcwd())

from src.ingest import pubmed, downloader
from src.parse import pubmed_parser, grobid_client, tei_parser
from src.screen import screener
from src.rob import assessor
from src.report import generator
from src.llm import client as llm_client
from src.utils import data_manager

# --- Configuration & Setup ---
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
TABLES_DIR = os.path.join(DATA_DIR, "tables")
TEI_DIR = os.path.join(DATA_DIR, "tei")
PDF_DIR = os.path.join(DATA_DIR, "pdf")
CONFIG_PATH = "picos_config.yaml"

# Ensure directories exist
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)
os.makedirs(TEI_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

st.set_page_config(page_title="Systematic Reviewer AI", layout="wide")

# --- Helper Functions ---
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f).get('picos', {})
    return {}

def save_config(picos_data):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump({'picos': picos_data}, f, allow_unicode=True, sort_keys=False)

def construct_search_query(picos):
    query_parts = []
    def format_part(term, field_tag="[tiab]"):
        if not term: return None
        if ' ' in term: return f'"{term}"{field_tag}'
        return f'{term}{field_tag}'

    query_parts.append(format_part(picos.get('population')))
    query_parts.append(format_part(picos.get('intervention')))
    query_parts.append(format_part(picos.get('comparison')))
    query_parts.append(format_part(picos.get('outcome')))
    query_parts.append(format_part(picos.get('study_design'), "[pt]"))
    return " AND ".join(filter(None, query_parts))

# --- Translations ---
TRANSLATIONS = {
    "EN": {
        "title": "🤖 Systematic Reviewer AI",
        "subtitle": "Automate your systematic review pipeline with local AI.",
        "project_data": "Project & Data",
        "reset_data": "🗑️ Reset All Data",
        "reset_success": "Data cleared!",
        "current_config": "Current Config",
        "language": "Language",
        "tabs": ["🔍 1. Search (PICO)", "👀 2. Screening", "⚙️ 3. Analysis Pipeline", "📊 4. Report"],
        "step1_header": "Step 1: Scoping and Search Strategy",
        "save_config": "💾 Save Configuration & Generate Query",
        "config_saved": "Configuration saved!",
        "generated_query": "Generated PubMed Query",
        "max_articles": "Max Articles to Retrieve",
        "search_button": "🚀 Search PubMed",
        "searching": "Searching PubMed...",
        "total_found": "Total articles found: {count}. Retrieving top {max}...",
        "retrieval_success": "Successfully retrieved and parsed {count} articles!",
        "no_articles": "No articles found matching the criteria.",
        "search_first": "No articles found. Please run the search in Step 1 first.",
        "step2_header": "Step 2: Automated Screening",
        "start_screening": "🤖 Start Automated Screening",
        "screening_progress": "AI is screening titles and abstracts...",
        "screening_results": "Screening Results",
        "inclusion_rate": "Inclusion Rate",
        "step3_header": "Step 3: Processing Pipeline",
        "step3_desc": "This step will perform PDF Download, Parsing, RoB Assessment, and Data Extraction.",
        "screen_first_warning": "Please complete screening in Step 2 first.",
        "no_included": "No included articles to process.",
        "run_pipeline": "▶️ Run Analysis Pipeline",
        "downloading_pdfs": "Downloading PDFs...",
        "parsing_pdfs": "Parsing PDFs with GROBID...",
        "assessing_rob": "Assessing Risk of Bias...",
        "extracting_data": "Extracting PICO Data...",
        "pipeline_complete": "Pipeline Completed!",
        "analysis_complete": "Analysis complete.",
        "step4_header": "Step 4: Final Report",
        "generate_report": "📄 Generate Report",
        "report_generated": "Report generated!",
        "download_report": "Download Report (MD)",
        "population": "Population",
        "intervention": "Intervention",
        "comparison": "Comparison",
        "outcome": "Outcome",
        "study_design": "Study Design"
    },
    "KO": {
        "title": "🤖 체계적 문헌고찰 AI",
        "subtitle": "로컬 AI로 체계적 문헌고찰 파이프라인을 자동화하세요.",
        "project_data": "프로젝트 및 데이터",
        "reset_data": "🗑️ 모든 데이터 초기화",
        "reset_success": "데이터가 초기화되었습니다!",
        "current_config": "현재 설정",
        "language": "언어 / Language",
        "tabs": ["🔍 1. 검색 (PICO)", "👀 2. 스크리닝", "⚙️ 3. 분석 파이프라인", "📊 4. 보고서"],
        "step1_header": "1단계: 범위 설정 및 검색 전략",
        "save_config": "💾 설정 저장 및 쿼리 생성",
        "config_saved": "설정이 저장되었습니다!",
        "generated_query": "생성된 PubMed 쿼리",
        "max_articles": "가져올 최대 논문 수",
        "search_button": "🚀 PubMed 검색",
        "searching": "PubMed 검색 중...",
        "total_found": "총 {count}개의 논문 발견. 상위 {max}개 가져오는 중...",
        "retrieval_success": "{count}개의 논문을 성공적으로 가져오고 파싱했습니다!",
        "no_articles": "조건에 맞는 논문을 찾을 수 없습니다.",
        "search_first": "논문이 없습니다. 1단계에서 검색을 먼저 실행해주세요.",
        "step2_header": "2단계: 자동 스크리닝",
        "start_screening": "🤖 자동 스크리닝 시작",
        "screening_progress": "AI가 제목과 초록을 스크리닝하고 있습니다...",
        "screening_results": "스크리닝 결과",
        "inclusion_rate": "포함 비율",
        "step3_header": "3단계: 처리 파이프라인",
        "step3_desc": "이 단계에서는 PDF 다운로드, 파싱, 비뚤림 위험(RoB) 평가, 데이터 추출을 수행합니다.",
        "screen_first_warning": "2단계에서 스크리닝을 먼저 완료해주세요.",
        "no_included": "처리를 진행할 포함된 논문이 없습니다.",
        "run_pipeline": "▶️ 분석 파이프라인 실행",
        "downloading_pdfs": "PDF 다운로드 중...",
        "parsing_pdfs": "GROBID로 PDF 파싱 중...",
        "assessing_rob": "비뚤림 위험(RoB) 평가 중...",
        "extracting_data": "PICO 데이터 추출 중...",
        "pipeline_complete": "파이프라인 완료!",
        "analysis_complete": "분석이 완료되었습니다.",
        "step4_header": "4단계: 최종 보고서",
        "generate_report": "📄 보고서 생성",
        "report_generated": "보고서가 생성되었습니다!",
        "download_report": "보고서 다운로드 (MD)",
        "population": "연구 대상(Population)",
        "intervention": "중재(Intervention)",
        "comparison": "비교(Comparison)",
        "outcome": "결과(Outcome)",
        "study_design": "연구 설계(Study Design)"
    }
}

def t(key, **kwargs):
    lang = st.session_state.get('lang', 'KO') # Default to Korean as requested
    text = TRANSLATIONS[lang].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def init_session_state():
    if 'stats' not in st.session_state:
        st.session_state['stats'] = {
            'total_found': 0, 'screened': 0, 'excluded': 0, 'included': 0, 'retrieved': 0
        }
    if 'picos' not in st.session_state:
        st.session_state['picos'] = load_config()
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'KO'

# --- Main App Interface ---
def main():
    init_session_state()
    
    # Language Selector in Sidebar (First item)
    with st.sidebar:
        st.session_state['lang'] = st.radio(
            "언어 / Language", 
            ["KO", "EN"], 
            index=0 if st.session_state['lang'] == 'KO' else 1,
            horizontal=True
        )
        st.divider()

    st.title(t("title"))
    st.markdown(t("subtitle"))

    # --- Sidebar Content ---
    with st.sidebar:
        st.header(t("project_data"))
        if st.button(t("reset_data"), type="primary"):
            data_manager.clear_generated_data_files()
            st.session_state['stats'] = {'total_found': 0, 'screened': 0, 'excluded': 0, 'included': 0, 'retrieved': 0}
            st.success(t("reset_success"))
            time.sleep(1)
            st.rerun()
        
        st.divider()
        st.subheader(t("current_config"))
        st.json(st.session_state['picos'])

    # --- Tabs ---
    tab1, tab2, tab3, tab4 = st.tabs(t("tabs"))

    # --- Tab 1: PICO & Search ---
    with tab1:
        st.header(t("step1_header"))
        
        col1, col2 = st.columns(2)
        with col1:
            population = st.text_input(t("population"), value=st.session_state['picos'].get('population', ''))
            intervention = st.text_input(t("intervention"), value=st.session_state['picos'].get('intervention', ''))
            comparison = st.text_input(t("comparison"), value=st.session_state['picos'].get('comparison', ''))
        with col2:
            outcome = st.text_input(t("outcome"), value=st.session_state['picos'].get('outcome', ''))
            study_design = st.text_input(t("study_design"), value=st.session_state['picos'].get('study_design', ''))
        
        if st.button(t("save_config")):
            new_picos = {
                'population': population, 'intervention': intervention, 
                'comparison': comparison, 'outcome': outcome, 'study_design': study_design
            }
            save_config(new_picos)
            st.session_state['picos'] = new_picos
            st.success(t("config_saved"))

        query = construct_search_query(st.session_state['picos'])
        st.text_area(t("generated_query"), value=query, height=100)

        st.divider()
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            max_ret = st.number_input(t("max_articles"), min_value=1, max_value=1000, value=20)
        with col_s2:
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
            if st.button(t("search_button")):
                with st.spinner(t("searching")):
                    today = datetime.now()
                    end_date = today.strftime("%Y/%m/%d")
                    start_date = (today - timedelta(days=20*365)).strftime("%Y/%m/%d")
                    
                    # 1. Get Count
                    _, total_count = pubmed.fetch_pmids(query, max_ret=1, mindate=start_date, maxdate=end_date, sort='relevance')
                    st.session_state['stats']['total_found'] = total_count
                    
                    if total_count > 0:
                        st.info(t("total_found", count=total_count, max=max_ret))
                        # 2. Get Data
                        pmids, _ = pubmed.fetch_pmids(query, max_ret=max_ret, mindate=start_date, maxdate=end_date, sort='relevance')
                        
                        # Save PMIDs
                        pd.DataFrame(pmids, columns=["pmid"]).to_csv(os.path.join(TABLES_DIR, "retrieved_pmids.csv"), index=False)
                        
                        # Fetch Abstracts
                        articles_xml = pubmed.fetch_abstracts(pmids)
                        
                        # Filter by Year
                        root = ET.fromstring(articles_xml)
                        filtered_articles_elements = []
                        current_year = datetime.now().year
                        for article in root.findall(".//PubmedArticle"):
                            pub_year_node = article.find(".//PubDate/Year")
                            pub_year = int(pub_year_node.text) if pub_year_node is not None and pub_year_node.text.isdigit() else current_year + 1
                            if pub_year <= current_year:
                                filtered_articles_elements.append(article)
                        
                        # Reconstruct XML
                        filtered_root = ET.Element("PubmedArticleSet")
                        for article_elem in filtered_articles_elements:
                            filtered_root.append(article_elem)
                        filtered_articles_xml = ET.tostring(filtered_root, encoding='unicode')
                        
                        # Save XML
                        with open(os.path.join(RAW_DATA_DIR, "articles.xml"), 'w', encoding='utf-8') as f:
                            f.write(filtered_articles_xml)
                        
                        # Parse to CSV
                        pubmed_parser.parse_and_save_articles_csv(filtered_articles_xml, os.path.join(TABLES_DIR, "articles.csv"))
                        st.success(t("retrieval_success", count=len(filtered_articles_elements)))
                    else:
                        st.warning(t("no_articles"))

    # --- Tab 2: Screening ---
    with tab2:
        st.header(t("step2_header"))
        csv_path = os.path.join(TABLES_DIR, "articles.csv")
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            st.dataframe(df[['pmid', 'title', 'journal', 'pub_year']], use_container_width=True)
            
            if st.button(t("start_screening")):
                with st.spinner(t("screening_progress")):
                    screened_df = screener.screen_abstracts(df, st.session_state['picos'])
                    
                    # Save results
                    screened_df.to_csv(os.path.join(TABLES_DIR, "screening_results.csv"), index=False, encoding='utf-8-sig')
                    # Update main csv
                    screened_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    
                    # Update stats
                    st.session_state['stats']['screened'] = len(screened_df)
                    st.session_state['stats']['included'] = len(screened_df[screened_df['screening_decision'] == 'Included'])
                    st.session_state['stats']['excluded'] = st.session_state['stats']['screened'] - st.session_state['stats']['included']
            
            # Show Screening Results if available
            if 'screening_decision' in df.columns:
                st.divider()
                st.subheader(t("screening_results"))
                st.metric(t("inclusion_rate"), f"{st.session_state['stats']['included']} / {st.session_state['stats']['screened']}")
                st.dataframe(df[['pmid', 'title', 'screening_decision', 'screening_reason']], use_container_width=True)
        else:
            st.info(t("search_first"))

    # --- Tab 3: Analysis Pipeline ---
    with tab3:
        st.header(t("step3_header"))
        st.markdown(t("step3_desc"))
        
        csv_path = os.path.join(TABLES_DIR, "articles.csv")
        if os.path.exists(csv_path):
             df = pd.read_csv(csv_path)
             if 'screening_decision' not in df.columns:
                 st.warning(t("screen_first_warning"))
             else:
                 included_df = df[df['screening_decision'] == 'Included']
                 included_pmids = included_df['pmid'].astype(str).tolist()
                 
                 if not included_pmids:
                     st.warning(t("no_included"))
                 else:
                     if st.button(t("run_pipeline")):
                         progress_bar = st.progress(0)
                         status_text = st.empty()
                         xml_path = os.path.join(RAW_DATA_DIR, "articles.xml")

                         # 1. Download PDFs
                         status_text.text(t("downloading_pdfs"))
                         pdf_download_status = downloader.download_pdfs_from_xml(xml_path, PDF_DIR, allowed_pmids=included_pmids)
                         df['pdf_download_status'] = df['pmid'].astype(str).map(pdf_download_status)
                         df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                         
                         downloaded_pdfs = [k for k, v in pdf_download_status.items() if "Downloaded" in v or "Already" in v]
                         st.session_state['stats']['retrieved'] = len(downloaded_pdfs)
                         progress_bar.progress(25)
                         
                         # 2. GROBID Parsing
                         status_text.text(t("parsing_pdfs"))
                         for pmid in downloaded_pdfs:
                             pdf_path = os.path.join(PDF_DIR, f"{pmid}.pdf")
                             if os.path.exists(pdf_path):
                                 tei_xml = grobid_client.process_pdf(pdf_path)
                                 if tei_xml:
                                     with open(os.path.join(TEI_DIR, f"{pmid}.xml"), 'w', encoding='utf-8') as f:
                                         f.write(tei_xml)
                         progress_bar.progress(50)

                         # 3. RoB Assessment
                         status_text.text(t("assessing_rob"))
                         if os.path.exists(TEI_DIR) and os.listdir(TEI_DIR):
                             assessor.batch_assess_rob(TEI_DIR, os.path.join(TABLES_DIR, "rob_assessment.csv"))
                         progress_bar.progress(75)

                         # 4. Data Extraction
                         status_text.text(t("extracting_data"))
                         llm = llm_client.LLMClient()
                         tei_files = [f for f in os.listdir(TEI_DIR) if f.endswith('.xml')]
                         extracted_data = []
                         
                         if tei_files:
                            for tei_file in tei_files:
                                pmid = tei_file.replace('.xml', '')
                                full_text = tei_parser.extract_text_from_tei(os.path.join(TEI_DIR, tei_file))
                                if full_text:
                                    text_snippet = (full_text[:8000] + '...') if len(full_text) > 8000 else full_text
                                    user_prompt = f"Extract PICO + Study Design in JSON with keys: population, intervention, comparison, outcome, study_design. Text: {text_snippet}"
                                    messages = [{"role": "system", "content": "You are a biomedical expert."}, {"role": "user", "content": user_prompt}]
                                    resp = llm.get_completion(messages)
                                    # Simple parsing attempt (reuse logic from main.py or make robust later)
                                    try:
                                        import re, json
                                        match = re.search(r"({[\s\S]*})", resp)
                                        if match:
                                            data = json.loads(match.group(1))
                                            data['pmid'] = pmid
                                            extracted_data.append(data)
                                    except: pass
                            
                            if extracted_data:
                                pd.DataFrame(extracted_data).to_csv(os.path.join(TABLES_DIR, "extracted_pico.csv"), index=False)
                         
                         progress_bar.progress(100)
                         status_text.text(t("pipeline_complete"))
                         st.success(t("analysis_complete"))

    # --- Tab 4: Reporting ---
    with tab4:
        st.header(t("step4_header"))
        
        current_lang = st.session_state['lang']
        report_filename = f"report_{current_lang}.md"
        report_path = os.path.join(DATA_DIR, report_filename)
        
        if st.button(t("generate_report")):
            generator.generate_report(
                st.session_state['stats'], 
                st.session_state['picos'], 
                os.path.join(TABLES_DIR, "extracted_pico.csv"), 
                os.path.join(TABLES_DIR, "rob_assessment.csv"), 
                report_path,
                lang=current_lang
            )
            st.success(t("report_generated"))
            
        # Display report if it exists for the current language
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()
                st.markdown(report_content)
                
                st.download_button(
                    label=t("download_report"),
                    data=report_content,
                    file_name=report_filename,
                    mime="text/markdown"
                )
        else:
            # If current language report doesn't exist but the OTHER one does?
            # Optional: Check for fallback. But for now, just strictly follow the toggle.
            pass

if __name__ == "__main__":
    main()
