import fitz  # PyMuPDF
import logging
from typing import List, Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_source: Union[str, bytes]) -> List[Dict]:
    """
    Extracts text page-by-page from a PDF file path or raw bytes.
    
    Args:
        pdf_source: A string file path, or bytes containing PDF data.
        
    Returns:
        A list of dictionaries containing 'page' number (1-indexed) and its 'text'.
    """
    pages_content = []
    try:
        if isinstance(pdf_source, str):
            logger.info(f"Opening PDF file from path: {pdf_source}")
            doc = fitz.open(pdf_source)
        elif isinstance(pdf_source, bytes):
            logger.info("Opening PDF file from raw bytes stream")
            doc = fitz.open(stream=pdf_source, filetype="pdf")
        else:
            raise ValueError("pdf_source must be a file path string or bytes.")

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            pages_content.append({
                "page": page_num + 1,
                "text": text.strip()
            })
        
        doc.close()
        logger.info(f"Successfully extracted {len(pages_content)} pages from PDF.")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise e

    return pages_content

def truncate_text(text: str, max_words: int = 200) -> str:
    """
    Truncates a text block to a maximum number of words, appending '...' if truncated.
    """
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text
