import xml.etree.ElementTree as ET
import pandas as pd

def parse_and_save_articles_csv(xml_string, output_path):
    """
    Parses the XML content from PubMed and saves the key information into a CSV file.

    Args:
        xml_string (str): The raw XML string fetched from PubMed.
        output_path (str): The path to save the output CSV file.
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML string. {e}")
        return

    articles_list = []
    for article in root.findall(".//PubmedArticle"):
        article_data = {}

        # Extract PMID
        pmid_node = article.find(".//PMID")
        article_data['pmid'] = pmid_node.text if pmid_node is not None else ''

        # Extract DOI
        doi_node = article.find(".//ArticleId[@IdType='doi']")
        article_data['doi'] = doi_node.text if doi_node is not None else ''

        # Extract Title
        title_node = article.find(".//ArticleTitle")
        article_data['title'] = title_node.text if title_node is not None else ''

        # Extract Journal Title
        journal_title_node = article.find(".//Journal/Title")
        article_data['journal'] = journal_title_node.text if journal_title_node is not None else ''

        # Extract Publication Year
        pub_year_node = article.find(".//PubDate/Year")
        article_data['pub_year'] = pub_year_node.text if pub_year_node is not None else ''

        # Extract Abstract
        abstract_nodes = article.findall(".//Abstract/AbstractText")
        abstract_text = ' '.join([node.text for node in abstract_nodes if node.text])
        article_data['abstract'] = abstract_text

        articles_list.append(article_data)

    if not articles_list:
        print("No articles found in the XML to process.")
        return

    # Create DataFrame and save to CSV
    df = pd.DataFrame(articles_list)
    # Use utf-8-sig for better compatibility with Excel
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Successfully parsed and saved {len(articles_list)} articles to {output_path}")
