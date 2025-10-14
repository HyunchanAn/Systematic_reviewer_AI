import os
import requests
import xml.etree.ElementTree as ET
import time

# Unpaywall API requires an email address for their free tier
UNPAYWALL_EMAIL = "test@example.com"

def get_pdf_url_from_doi(doi):
    """
    Queries the Unpaywall API to find a direct PDF link for a given DOI.
    """
    if not doi:
        return None
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}"
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Check for the best open-access location provided by Unpaywall
        if data.get("best_oa_location") and data["best_oa_location"].get("url_for_pdf"):
            return data["best_oa_location"]["url_for_pdf"]
    except requests.exceptions.RequestException as e:
        print(f"  - Unpaywall API request failed for DOI {doi}: {e}")
    except Exception as e:
        print(f"  - An unexpected error occurred while processing DOI {doi}: {e}")
    return None

def download_pdf(pdf_url, output_path):
    """
    Downloads a PDF from a URL and saves it to the specified path.
    """
    try:
        response = requests.get(pdf_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"  - Failed to download PDF from {pdf_url}: {e}")
    return False

def download_pdfs_from_xml(xml_path, output_dir):
    """
    Parses a PubMed XML file, extracts DOIs, and attempts to download open-access PDFs.
    Returns a dictionary of PMID to download status.
    """
    os.makedirs(output_dir, exist_ok=True)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file at {xml_path}. {e}")
        return {}

    articles = root.findall(".//PubmedArticle")
    total_articles = len(articles)
    if total_articles == 0:
        return {}

    download_status = {}
    download_count = 0
    for i, article in enumerate(articles):
        pmid_node = article.find(".//PMID")
        pmid = pmid_node.text if pmid_node is not None else f"unknown_{i+1}"
        
        doi_node = article.find(".//ArticleId[@IdType='doi']")
        doi = doi_node.text if doi_node is not None else None
        
        if not doi:
            download_status[pmid] = "DOI Not Found"
            continue
        
        pdf_url = get_pdf_url_from_doi(doi)
        
        if not pdf_url:
            download_status[pmid] = "No OA PDF Link"
            continue

        output_filename = os.path.join(output_dir, f"{pmid}.pdf")

        if os.path.exists(output_filename):
            download_status[pmid] = "Already Downloaded"
            download_count += 1
            continue

        if download_pdf(pdf_url, output_filename):
            download_status[pmid] = "Downloaded"
            download_count += 1
        else:
            download_status[pmid] = "Download Failed"
        
        time.sleep(1)

    print(f"PDF 다운로드 시도 완료: 총 {total_articles}개 중 {download_count}개 성공 또는 이미 존재.")
    return download_status

if __name__ == '__main__':
    # This allows the script to be run directly for testing purposes.
    # It assumes the script is in src/ingest and the data is in data/
    current_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
    xml_file_path = os.path.join(project_root, 'data', 'raw', 'articles.xml')
    pdf_output_dir = os.path.join(project_root, 'data', 'pdf')
    
    if not os.path.exists(xml_file_path):
        print(f"Error: XML file not found at {xml_file_path}")
        print("Please run main.py first to generate the articles.xml file.")
    else:
        download_pdfs_from_xml(xml_file_path, pdf_output_dir)
