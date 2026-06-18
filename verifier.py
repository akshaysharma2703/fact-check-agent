import json
import logging
import os
import google.generativeai as genai
from typing import List, Dict
from extractor import configure_gemini

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def verify_claim(
    claim: str, 
    original_context: str, 
    search_results: List[Dict], 
    api_key: str = None,
    provider: str = "Gemini"
) -> Dict:
    """
    Verifies a claim against live search results and scrapes.
    Supports Google Gemini, Groq, and OpenAI.
    
    Args:
        claim: The factual statement to check.
        original_context: The surrounding context from the PDF.
        search_results: List of search results with 'title', 'url', 'snippet', 'content'.
        api_key: The API key for the chosen provider.
        provider: 'Gemini', 'Groq', or 'OpenAI'.
        
    Returns:
        A verification report dict: {
            'status': ..., 
            'confidence_score': ..., 
            'supporting_evidence': ..., 
            'correct_fact': ..., 
            'source_url': ...
        }
    """
    # Auto-detect provider based on key format or environment variables
    target_key = api_key
    if target_key:
        if target_key.strip().startswith("sk-"):
            provider = "OpenAI"
            logger.info("Auto-detected OpenAI API Key format in verifier. Switching provider to OpenAI.")
        elif target_key.strip().startswith("gsk_"):
            provider = "Groq"
            logger.info("Auto-detected Groq API Key format in verifier. Switching provider to Groq.")
    else:
        if provider == "OpenAI":
            target_key = os.environ.get("OPENAI_API_KEY")
        elif provider == "Groq":
            target_key = os.environ.get("GROQ_API_KEY")
        else:
            target_key = os.environ.get("GEMINI_API_KEY")

    # Format the evidence content to provide to the model
    evidence_list = []
    for i, result in enumerate(search_results):
        evidence_list.append(
            f"--- SOURCE {i+1} ---\n"
            f"Title: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Snippet: {result['snippet']}\n"
            f"Content Excerpt:\n{result['content'][:3500]}\n"
            f"--- END SOURCE {i+1} ---"
        )
    
    evidence_text = "\n\n".join(evidence_list) if evidence_list else "No live search results available."
    
    prompt = f"""
    You are an objective, rigorous, fact-checking agent. Your goal is to evaluate the accuracy of a given claim using the provided live search evidence.
    
    CLAIM TO VERIFY:
    "{claim}"
    
    ORIGINAL DOCUMENT CONTEXT:
    "{original_context}"
    
    LIVE SEARCH EVIDENCE:
    {evidence_text}
    
    ---
    FACT-CHECKING RULES:
    1. Read the claim and compare it strictly against the facts, statistics, numbers, and dates present in the live search evidence.
    2. Classify the claim into one of the following statuses:
       - "Verified": The claim is fully accurate and matches the search evidence (e.g., matching numbers, names, and dates).
       - "Inaccurate": The claim is partially correct, but contains errors like slightly wrong statistics, misaligned dates, or overstated growth rates.
       - "False": The claim is completely wrong, fabricated, or directly contradicted by the evidence.
       - "Unverified": There is not enough information in the search evidence to confirm or refute the claim.
    3. Calculate a "confidence_score" between 0.0 and 1.0:
       - 1.0 means highly reputable sources explicitly verify/refute the claim.
       - 0.5 means partial support or minor conflicts in sources.
       - 0.0 means complete lack of evidence.
    4. Provide "supporting_evidence": A concise explanation of what the search evidence says, quoting key metrics and naming the source.
    5. Provide "correct_fact": If status is Inaccurate or False, write out the corrected claim based on the evidence. If Verified, repeat the claim or state "Correct as stated".
    6. Provide "source_url": The specific URL of the search result that best supports your classification.
    
    You must output a JSON object only. Do not add markdown code blocks (like ```json) or explanation text outside the JSON.
    The response schema must be:
    {{
      "status": "Verified" | "Inaccurate" | "False" | "Unverified",
      "confidence_score": <float between 0.0 and 1.0>,
      "supporting_evidence": "Explanation of search findings citing specific numbers or facts.",
      "correct_fact": "The corrected statement or 'Correct as stated'.",
      "source_url": "The most relevant source URL from the search evidence"
    }}
    """
    
    if provider == "OpenAI":
        try:
            logger.info(f"Verifying claim via OpenAI: '{claim[:50]}...'")
            from openai import OpenAI
            client = OpenAI(api_key=target_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            result_json = json.loads(response_text)
            logger.info(f"Verification completed via OpenAI. Status: {result_json.get('status')}")
            return result_json
        except Exception as e:
            logger.error(f"Error during claim verification via OpenAI: {str(e)}")
            return {
                "status": "Unverified",
                "confidence_score": 0.0,
                "supporting_evidence": f"OpenAI verification error: {str(e)}",
                "correct_fact": "N/A",
                "source_url": ""
            }
            
    elif provider == "Groq":
        try:
            logger.info(f"Verifying claim via Groq: '{claim[:50]}...'")
            import groq
            client = groq.Groq(api_key=target_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-70b-8192",
                response_format={"type": "json_object"}
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            result_json = json.loads(response_text)
            logger.info(f"Verification completed via Groq. Status: {result_json.get('status')}")
            return result_json
        except Exception as e:
            logger.error(f"Error during claim verification via Groq: {str(e)}")
            return {
                "status": "Unverified",
                "confidence_score": 0.0,
                "supporting_evidence": f"Groq verification error: {str(e)}",
                "correct_fact": "N/A",
                "source_url": ""
            }
    else:
        # Default: Gemini
        configure_gemini(target_key)
        try:
            logger.info(f"Verifying claim via Gemini: '{claim[:50]}...'")
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            response = model.generate_content(
                contents=[prompt],
                generation_config={"response_mime_type": "application/json"}
            )
            
            response_text = response.text.strip()
            result_json = json.loads(response_text)
            logger.info(f"Verification completed via Gemini. Status: {result_json.get('status')}")
            return result_json
            
        except Exception as e:
            logger.error(f"Error during claim verification via Gemini: {str(e)}")
            return {
                "status": "Unverified",
                "confidence_score": 0.0,
                "supporting_evidence": f"Gemini verification error: {str(e)}",
                "correct_fact": "N/A",
                "source_url": ""
            }
