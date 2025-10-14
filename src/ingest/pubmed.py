
import requests
import time

# Base URL for PubMed E-utilities
EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def fetch_pmids(query, max_ret=100, api_key=None, sort='pub_date', mindate=None, maxdate=None):
    """
    Fetches a list of PubMed IDs (PMIDs) for a given search query.

    Args:
        query (str): The search query string.
        max_ret (int): The maximum number of PMIDs to retrieve.
        api_key (str, optional): Your NCBI API key.
        sort (str, optional): The sort order. Defaults to 'pub_date' for newest first.
        mindate (str, optional): Start date in YYYY/MM/DD format.
        maxdate (str, optional): End date in YYYY/MM/DD format.

    Returns:
        list: A list of PMID strings, or an empty list if the search fails.
    """
    print(f"Searching PubMed for query: {query}")
    search_url = f"{EUTILS_BASE_URL}esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_ret,
        'retmode': 'json',
        'sort': sort,
    }
    if api_key:
        params['api_key'] = api_key
    
    # Add date range parameters if provided
    if mindate and maxdate:
        params['datetype'] = 'pdat' # Use publication date
        params['mindate'] = mindate
        params['maxdate'] = maxdate

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        pmids = data.get('esearchresult', {}).get('idlist', [])
        print(f"Found {len(pmids)} PMIDs.")
        return pmids
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during PubMed search: {e}")
        return []

def fetch_abstracts(pmids, api_key=None):
    """
    Fetches abstracts and other metadata for a list of PMIDs.

    Args:
        pmids (list): A list of PubMed IDs.
        api_key (str, optional): Your NCBI API key. Defaults to None.

    Returns:
        dict: A dictionary where keys are PMIDs and values are article metadata.
    """
    if not pmids:
        return {}

    print(f"Fetching details for {len(pmids)} PMIDs...")
    fetch_url = f"{EUTILS_BASE_URL}efetch.fcgi"
    # Join PMIDs into a comma-separated string
    id_string = ",".join(pmids)
    
    params = {
        'db': 'pubmed',
        'id': id_string,
        'retmode': 'xml', # XML is often more detailed than JSON for abstracts
    }
    if api_key:
        params['api_key'] = api_key

    try:
        response = requests.post(fetch_url, data=params) # Use POST for long lists of IDs
        response.raise_for_status()
        # Basic XML parsing can be done here, but for robustness, a library like BeautifulSoup or lxml is recommended.
        # For this initial scaffold, we'll just return the raw XML content.
        print("Successfully fetched article details.")
        return response.text # In a real implementation, parse this XML
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during PubMed fetch: {e}")
        return None

if __name__ == '__main__':
    # Example usage of the pubmed module
    # This is the example query from Example001.csv
    EXAMPLE_QUERY = "('polycystic ovary syndrome':ti,ab OR 'pcos':ti,ab) AND ('herbal':ti,ab OR 'chinese med*':ti,ab) AND 'rando*':ti,ab"
    
    # 1. Fetch PMIDs
    retrieved_pmids = fetch_pmids(EXAMPLE_QUERY, max_ret=5)
    
    # 2. Fetch abstracts for the retrieved PMIDs
    if retrieved_pmids:
        article_data_xml = fetch_abstracts(retrieved_pmids)
        if article_data_xml:
            print("\n--- Raw XML Output (first 500 chars) ---")
            print(article_data_xml[:500] + "...")
            print("----------------------------------------\n")
            print("Note: In a full implementation, this XML would be parsed to extract Title, Abstract, Authors, etc.")
