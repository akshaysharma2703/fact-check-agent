import json
import logging
import os
import google.generativeai as genai
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def configure_gemini(api_key: str = None):
    """
    Configures the Google Generative AI API client.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Google Gemini API Key is missing. "
            "Please set the GEMINI_API_KEY environment variable or supply it in the app settings."
        )
    genai.configure(api_key=key)

def extract_claims(pages_content: List[Dict], api_key: str = None, provider: str = "Gemini") -> List[Dict]:
    """
    Analyzes the extracted PDF text to identify and extract verify-worthy claims.
    Supports Google Gemini, Groq, and OpenAI.
    
    Args:
        pages_content: List of dictionaries with 'page' and 'text'.
        api_key: The API key for the chosen provider.
        provider: 'Gemini', 'Groq', or 'OpenAI'.
        
    Returns:
        A list of extracted claim dicts: [{
            'claim': ..., 
            'category': ..., 
            'original_context': ..., 
            'page_number': ..., 
            'suggested_search_query': ...
        }]
    """
    if not pages_content:
        return []
        
    # Auto-detect provider based on key prefix
    target_key = api_key
    if target_key:
        if target_key.strip().startswith("sk-"):
            provider = "OpenAI"
            logger.info("Auto-detected OpenAI API Key format. Switching provider to OpenAI.")
        elif target_key.strip().startswith("gsk_"):
            provider = "Groq"
            logger.info("Auto-detected Groq API Key format. Switching provider to Groq.")
    else:
        # Load from environment variables based on chosen provider
        if provider == "OpenAI":
            target_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "Groq":
            target_key = os.environ.get("GROQ_API_KEY")
        else:
            target_key = os.environ.get("GEMINI_API_KEY")

    # Merge pages into a single annotated string
    formatted_document = []
    for page in pages_content:
        formatted_document.append(
            f"[START PAGE {page['page']}]\n{page['text']}\n[END PAGE {page['page']}]"
        )
    combined_text = "\n\n".join(formatted_document)
    
    prompt = """
    You are an elite research analyst and forensic fact-checker. 
    Your mission is to read the following document content and extract specific, verify-worthy claims.
    
    Focus ONLY on objective claims that can be proven or disproven using data, records, or live web search.
    Do NOT extract subjective opinions, promotional adjectives ("world-class", "industry-leading"), or general fluffy statements.
    
    Identify claims belonging to these categories:
    - "Percentage" (e.g., "customer retention increased by 45%")
    - "Statistic" (e.g., "7 out of 10 users prefer our layout")
    - "Date" (e.g., "founded in 2012", "acquisition finalized on March 4, 2021")
    - "Market Size" (e.g., "the global market size reached $50 Billion in 2023")
    - "Financial" (e.g., "revenue grew by 24% CAGR", "ARR stands at $12M")
    - "Technical" (e.g., "reduced page response time to 15 milliseconds", "handles 100k requests/sec")
    
    For each extracted claim, formulate a highly objective and neutral search query suitable for a search engine to confirm the truthfulness of the statement.
    
    You must output a JSON object containing a "claims" array of objects. Do not wrap the JSON in markdown code blocks or add any trailing comments.
    The response must follow this exact JSON schema:
    {
      "claims": [
        {
          "claim": "A concise, clear summary of the factual claim (include relevant metrics, dates, and names)",
          "category": "One of: Percentage, Statistic, Date, Market Size, Financial, Technical",
          "original_context": "The exact sentence or passage containing the claim",
          "page_number": 1,
          "suggested_search_query": "Neutral search query targeting industry research, government databases, or reputable news reports (e.g., 'global CRM market size Gartner 2023')"
        }
      ]
    }
    """
    
    if provider == "OpenAI":
        try:
            logger.info("Initializing OpenAI client for claim extraction")
            from openai import OpenAI
            client = OpenAI(api_key=target_key)
            
            logger.info("Sending document context to OpenAI API for processing")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nDOCUMENT TEXT:\n{combined_text}"
                    }
                ],
                model="gpt-4o-mini",
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            logger.info("Received claim extraction response from OpenAI")
            
            data = json.loads(response_text)
            claims = data.get("claims", [])
            logger.info(f"Successfully extracted {len(claims)} claims via OpenAI.")
            return claims
        except Exception as e:
            logger.error(f"Error extracting claims via OpenAI: {str(e)}")
            raise e
            
    elif provider == "Groq":
        try:
            logger.info("Initializing Groq client for claim extraction")
            import groq
            client = groq.Groq(api_key=target_key)
            
            logger.info("Sending document context to Groq API for processing")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nDOCUMENT TEXT:\n{combined_text}"
                    }
                ],
                model="llama3-70b-8192",
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            logger.info("Received claim extraction response from Groq")
            
            data = json.loads(response_text)
            claims = data.get("claims", [])
            logger.info(f"Successfully extracted {len(claims)} claims via Groq.")
            return claims
        except Exception as e:
            logger.error(f"Error extracting claims via Groq: {str(e)}")
            raise e
            
    else:
        # Default: Gemini
        configure_gemini(target_key)
        try:
            logger.info("Initializing Gemini model for claim extraction")
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            logger.info("Sending document context to Gemini API for processing")
            response = model.generate_content(
                contents=[prompt, f"DOCUMENT TEXT:\n{combined_text}"],
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text.strip()
            logger.info("Received claim extraction response from Gemini")
            
            data = json.loads(response_text)
            claims = data.get("claims", [])
            logger.info(f"Successfully extracted {len(claims)} claims via Gemini.")
            return claims
            
        except Exception as e:
            logger.error(f"Error extracting claims via Gemini API: {str(e)}")
            raise e
