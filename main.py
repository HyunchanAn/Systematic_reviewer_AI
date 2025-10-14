import os
import pandas as pd
import yaml
import shutil
from datetime import datetime, timedelta
from src.ingest import pubmed, downloader
from src.parse import pubmed_parser
from src.llm import client as llm_client
from src.utils import data_manager

# Define file paths
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
TABLES_DIR = os.path.join(DATA_DIR, "tables")
CONFIG_PATH = "picos_config.yaml"

def check_and_clear_previous_run():
    """Checks for specific data files from a previous run and asks the user if they want to clear them."""
    previous_run_indicator = os.path.join(RAW_DATA_DIR, "articles.xml")
    
    if os.path.exists(previous_run_indicator):
        print("\n--- 경고: 이전 작업 데이터가 'data' 폴더에 남아있습니다. ---")
        choice = input("새로운 검색을 시작하면 이전 데이터(raw, tables, pdf의 내용)가 삭제됩니다. 계속하시겠습니까? [y/n]: ").lower()
        if choice == 'y':
            data_manager.clear_generated_data_files() # Call the new utility function
            return True
        else:
            print("작업을 중단합니다.")
            return False
    return True  # No previous data, proceed.

def load_or_create_picos_config():
    """Loads PICOS configuration from picos_config.yaml or creates it interactively."""
    picos_data = None
    use_existing_file = False

    if os.path.exists(CONFIG_PATH):
        print(f"--- Found existing configuration file: {CONFIG_PATH} ---")
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            existing_config = yaml.safe_load(f)
        
        print("--- Existing PICOS Configuration ---")
        for key, value in existing_config.get('picos', {}).items():
            if value:
                print(f"- {key.capitalize()}: {value}")

        choice = input(f"\n이 설정 파일을 사용하시겠습니까? [Y/n]: ").lower()
        if choice == '' or choice == 'y':
            use_existing_file = True
            picos_data = existing_config['picos']

    if not use_existing_file:
        if os.path.exists(CONFIG_PATH):
            print("\n--- Creating new PICOS configuration. ---")
        else:
            print("--- PICOS configuration file not found. Starting interactive setup. ---")
        
        picos = {}
        picos['population'] = input("> Population을 입력하세요: ")
        picos['intervention'] = input("> Intervention을 입력하세요: ")
        picos['comparison'] = input("> Comparison을 입력하세요: ")
        picos['outcome'] = input("> Outcome을 입력하세요: ")
        picos['study_design'] = input("> (선택) Study Design을 입력하세요 (없으면 Enter): ")

        save_choice = input(f"\n입력하신 내용으로 {CONFIG_PATH} 파일을 생성/덮어쓰시겠습니까? (y/n): ").lower()
        if save_choice == 'y':
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                yaml.dump({'picos': picos}, f, allow_unicode=True, sort_keys=False)
            print(f"--- Configuration saved to {CONFIG_PATH} ---")
        
        picos_data = picos

    return picos_data

def construct_search_query(picos):
    """Constructs a PubMed search query from the PICOS elements."""
    query_parts = []
    
    def format_part(term, field_tag="[tiab]"):
        if not term:
            return None
        if ' ' in term:
            return f'"{term}"{field_tag}'
        return f'{term}{field_tag}'

    query_parts.append(format_part(picos.get('population')))
    query_parts.append(format_part(picos.get('intervention')))
    query_parts.append(format_part(picos.get('comparison')))
    query_parts.append(format_part(picos.get('outcome')))
    query_parts.append(format_part(picos.get('study_design'), "[pt]"))

    return " AND ".join(filter(None, query_parts))

def setup_directories():
    """Ensures that the necessary data directories exist."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)

def main():
    """
    Main function to orchestrate the systematic review pipeline.
    """
    print("--- Starting Systematic Review AI Pipeline ---")
    
    if not check_and_clear_previous_run():
        return

    setup_directories()

    # --- 1. Scoping & Search --- #
    print("\nStep 1: Scoping and Searching")
    picos_config = load_or_create_picos_config()
    
    print("\n--- Using the following PICOS Configuration for the search ---")
    for key, value in picos_config.items():
        if value:
            print(f"- {key.capitalize()}: {value}")
    
    search_query = construct_search_query(picos_config)
    print(f"\nConstructed PubMed Query: {search_query}")

    # --- 2. Data Ingestion --- #
    print("\nStep 2: Ingesting data from PubMed")
    proceed = input("Proceed with this query? (y/n): ").lower()
    if proceed != 'y':
        print("Pipeline stopped by user.")
        return

    today = datetime.now()
    end_date = today.strftime("%Y/%m/%d")
    start_date = (today - timedelta(days=20*365)).strftime("%Y/%m/%d")
    
    print(f"Searching for articles published between {start_date} and {end_date}.")
    pmids = pubmed.fetch_pmids(
        search_query, 
        max_ret=20,
        mindate=start_date,
        maxdate=end_date
    )
    if not pmids:
        print("No articles found. Exiting pipeline.")
        return

    pmids_df = pd.DataFrame(pmids, columns=["pmid"])
    pmids_path = os.path.join(TABLES_DIR, "retrieved_pmids.csv")
    pmids_df.to_csv(pmids_path, index=False)
    print(f"Saved {len(pmids)} PMIDs to {pmids_path}")

    articles_xml = pubmed.fetch_abstracts(pmids)
    if articles_xml:
        # Save the raw XML
        xml_path = os.path.join(RAW_DATA_DIR, "articles.xml")
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(articles_xml)
        print(f"Saved article XML to {xml_path}")

        # Parse XML and save as CSV
        print("\nParsing XML and creating articles.csv...")
        csv_path = os.path.join(TABLES_DIR, "articles.csv")
        pubmed_parser.parse_and_save_articles_csv(articles_xml, csv_path)

        # --- 3. PDF Downloading ---
        print("\nStep 3: Downloading PDFs")
        pdf_dir = os.path.join(DATA_DIR, "pdf")
        downloader.download_pdfs_from_xml(xml_path, pdf_dir)

    # --- 4. Screening (Placeholder) --- #
    print("\nStep 4: Screening (Placeholder)")
    print("This step would involve using ASReview. See `tools/asreview`.")

    # --- 5. Data Extraction & LLM Summarization (Placeholder) --- #
    print("\nStep 5: Data Extraction and Summarization (Placeholder)")
    print("This step requires downloading PDFs, parsing with GROBID, and using the LLM.")
    
    llm = llm_client.LLMClient()
    if llm.get_completion([{"role": "system", "content": "Respond with OK if you are ready."}, {"role": "user", "content": "Are you ready?"}]):
        print("LLM client is connected and ready.")
    else:
        print("LLM client is not connected. Skipping summarization.")

    print("\n--- Pipeline Scaffolding Complete ---")

if __name__ == "__main__":
    main()
