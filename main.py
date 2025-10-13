import os
import pandas as pd
import yaml
from src.ingest import pubmed
from src.llm import client as llm_client

# Define file paths
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
TABLES_DIR = os.path.join(DATA_DIR, "tables")
CONFIG_PATH = "picos_config.yaml"

def load_or_create_picos_config():
    """
    Loads PICOS configuration from picos_config.yaml.
    If the file exists, asks the user if they want to use it.
    If not, or if the user chooses not to use the existing file,
    it prompts the user to create a new one interactively.
    """
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
    if picos.get('population'):
        query_parts.append(f"('{picos['population']}':ti,ab)")
    if picos.get('intervention'):
        query_parts.append(f"('{picos['intervention']}':ti,ab)")
    if picos.get('comparison'):
        query_parts.append(f"('{picos['comparison']}':ti,ab)")
    if picos.get('outcome'):
        query_parts.append(f"('{picos['outcome']}':ti,ab)")
    if picos.get('study_design'):
        query_parts.append(f"'{picos['study_design']}':ti,ab")

    return " AND ".join(query_parts)

def setup_directories():
    """Ensures that the necessary data directories exist."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(TABLES_DIR, exist_ok=True)

def main():
    """
    Main function to orchestrate the systematic review pipeline.
    This script serves as a high-level coordinator for the different modules.
    """
    print("--- Starting Systematic Review AI Pipeline ---")
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

    pmids = pubmed.fetch_pmids(search_query, max_ret=20) # Limit to 20 for this example
    
    if not pmids:
        print("No articles found. Exiting pipeline.")
        return

    # Save the list of PMIDs
    pmids_df = pd.DataFrame(pmids, columns=["pmid"])
    pmids_path = os.path.join(TABLES_DIR, "retrieved_pmids.csv")
    pmids_df.to_csv(pmids_path, index=False)
    print(f"Saved {len(pmids)} PMIDs to {pmids_path}")

    # Fetch abstracts
    articles_xml = pubmed.fetch_abstracts(pmids)
    if articles_xml:
        xml_path = os.path.join(RAW_DATA_DIR, "articles.xml")
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(articles_xml)
        print(f"Saved article XML to {xml_path}")

    # --- 3. Screening (Placeholder) --- #
    print("\nStep 3: Screening (Placeholder)")
    print("This step would involve using ASReview. See `tools/asreview`.")

    # --- 4. Data Extraction & LLM Summarization (Placeholder) --- #
    print("\nStep 4: Data Extraction and Summarization (Placeholder)")
    print("This step requires downloading PDFs, parsing with GROBID, and using the LLM.")
    
    llm = llm_client.LLMClient()
    if llm.get_completion([{"role": "system", "content": "Respond with OK if you are ready."}, {"role": "user", "content": "Are you ready?"}]):
        print("LLM client is connected and ready.")
    else:
        print("LLM client is not connected. Skipping summarization.")

    print("\n--- Pipeline Scaffolding Complete ---")

if __name__ == "__main__":
    main()
