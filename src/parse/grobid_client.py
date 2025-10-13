
import requests

class GrobidClient:
    """
    A client to interact with a running GROBID service.
    Assumes GROBID is running in a Docker container and accessible at the given host.
    """
    def __init__(self, host="http://localhost:8070"):
        """
        Initializes the GROBID client.
        Args:
            host (str): The address of the GROBID service.
        """
        self.host = host
        self.api_url = f"{host}/api/processFulltextDocument"

    def check_server(self):
        """Checks if the GROBID server is running and accessible."""
        try:
            response = requests.get(f"{self.host}/api/isalive")
            if response.status_code == 200 and response.text == "true":
                print("GROBID server is alive and running.")
                return True
            else:
                print(f"GROBID server responded with status {response.status_code}.")
                return False
        except requests.ConnectionError:
            print("Failed to connect to GROBID server. Please ensure it is running.")
            return False

    def process_pdf(self, pdf_path):
        """
        Processes a PDF file to extract structured TEI XML.

        Args:
            pdf_path (str): The local path to the PDF file.

        Returns:
            str: The TEI XML as a string, or None if processing fails.
        """
        print(f"Processing PDF: {pdf_path}")
        try:
            with open(pdf_path, 'rb') as f:
                files = {'input': f}
                # Other parameters can be added, e.g., 'consolidateHeader': '1'
                response = requests.post(self.api_url, files=files)
                response.raise_for_status()
                print("Successfully processed PDF and received TEI XML.")
                return response.text
        except FileNotFoundError:
            print(f"Error: The file was not found at {pdf_path}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while processing the PDF with GROBID: {e}")
            return None

if __name__ == '__main__':
    # Example of how to use the GrobidClient
    # This requires a running GROBID Docker container.
    # It also requires a PDF file to test with.
    
    print("Initializing GROBID client...")
    grobid_client = GrobidClient()
    
    # 1. Check if the server is running
    if grobid_client.check_server():
        # 2. Create a dummy PDF file for testing purposes, as we can't assume one exists.
        # In a real scenario, this path would come from the downloaded articles.
        dummy_pdf_path = "dummy_example.pdf"
        try:
            # A minimal valid PDF content
            pdf_content = b'%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF'
            with open(dummy_pdf_path, 'wb') as f:
                f.write(pdf_content)
            print(f"Created a dummy PDF for testing: {dummy_pdf_path}")

            # 3. Process the dummy PDF
            tei_xml = grobid_client.process_pdf(dummy_pdf_path)
            if tei_xml:
                print("\n--- Received TEI XML (first 500 chars) ---")
                print(tei_xml[:500] + "...")
                print("-----------------------------------------")
        finally:
            # 4. Clean up the dummy file
            import os
            if os.path.exists(dummy_pdf_path):
                os.remove(dummy_pdf_path)
                print(f"Cleaned up dummy PDF: {dummy_pdf_path}")
