import os
import fitz # PyMuPDF

PDF_DOWNLOAD_PATH = ""
EXTRACTED_TEXT_PATH = ""


def extract_text_from_pdf(pdf_filepath):
    """
    Extracts text content from a local PDF file using PyMuPDF (fitz).

    Args:
        pdf_filepath (str): The absolute path to the local PDF file.

    Returns:
        str: The extracted text content, or None if an error occurs.
    """
    try:
        print(f"--- Running PDF Text Extractor (PyMuPDF) on: {pdf_filepath} ---")
        if not os.path.exists(pdf_filepath):
            print(f"Error: PDF file not found at {pdf_filepath}")
            return None

        doc = fitz.open(pdf_filepath)
        full_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += page.get_text()
        
        doc.close()
        
        if not full_text:
            print("Warning: No text could be extracted from the PDF (might be image-based or empty).")
            # Return empty string instead of None if extraction worked but found no text
            return "" 
            
        print(f"Text extracted successfully using PyMuPDF (Length: {len(full_text)}).")
        return full_text

    except Exception as e:
        print(f"Error extracting text from PDF using PyMuPDF: {e}")
        # Log full traceback for detailed debugging if needed
        # import traceback
        # traceback.print_exc()
        return None

# Example usage (for testing with a local PDF)
if __name__ == "__main__":
    # Create a dummy PDF path for testing structure (replace with a real path if needed)
    test_pdf_path = "/home/ubuntu/opin_slack_bot/dummy_test.pdf" 
    # You would need to place a real PDF file there for this test to extract text
    if os.path.exists(test_pdf_path):
        print(f"--- Testing PDF Processor (PyMuPDF) with: {test_pdf_path} ---")
        text = extract_text_from_pdf(test_pdf_path)
        if text is not None:
            print("\n--- Extracted Text (First 500 chars) ---")
            print(text[:500])
            print("...")
        else:
            print("\n--- Text extraction failed. ---")
    else:
        print(f"--- Test PDF not found at {test_pdf_path}. Skipping extraction test. ---")

