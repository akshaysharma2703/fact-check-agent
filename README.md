# 🛡️ TruthLayer: Multi-LLM Fact-Checking AI Agent & Live Verification Engine

TruthLayer is a production-ready, AI-driven fact-checking application designed to act as an auditing layer for marketing publications, investment pitches, presentations, and documents. By processing uploaded PDFs, extracting structured claims, executing real-time web searches, and analyzing sources, TruthLayer separates verified data from hallucinations, outdated numbers, and unsupported assertions.

---

## 🎯 Features

- **Automated Claim Extraction**: Parses PDFs page-by-page using PyMuPDF and utilizes the selected LLM provider to isolate percentages, statistics, dates, market size claims, financial figures, and technical metrics.
- **Multi-LLM Provider Engine**:
  - **Google Gemini**: Uses `gemini-1.5-flash` for token-efficient extraction and verification.
  - **Groq**: Uses `llama3-70b-8192` for ultra-fast, low-latency evaluations.
  - **OpenAI**: Uses `gpt-4o-mini` for highly reliable reasoning and parsing compliance.
- **Intelligent API Auto-Detection**:
  * Automatically detects key formats: keys starting with `gsk_` route to **Groq**, keys starting with `sk-` route to **OpenAI**, and others route to **Google Gemini**.
- **Live Search & Scrape Layer**: Formulates neutralized queries, runs live searches on DuckDuckGo Search, and crawls the top destination pages using BeautifulSoup to extract evidence.
- **Audit Verification Ledger**: Interactive Streamlit dashboard showing statistics, filtered reports, confidence gauges, corrected assertions, and clickable source links.
- **Audit Exports**: Download generated verification reports as structured CSV or JSON files.

---

## 🏗️ Architecture Diagrams

### 1. System Architecture
```mermaid
graph TD
    User([User]) -->|Upload PDF / Use Sample| StreamlitUI[Streamlit App - app.py]
    StreamlitUI -->|Raw Bytes / Path| PDFParser[PDF Parser - utils.py]
    PDFParser -->|Extracted Page Content| ClaimExtractor[Claim Extractor - extractor.py]
    
    subgraph LLM Providers
        ClaimExtractor -->|Auto-detected / Selected Key| Gemini[Gemini API - gemini-1.5-flash]
        ClaimExtractor -->|Auto-detected / Selected Key| Groq[Groq API - llama3-70b-8192]
        ClaimExtractor -->|Auto-detected / Selected Key| OpenAI[OpenAI API - gpt-4o-mini]
    end

    Gemini & Groq & OpenAI -->|Structured JSON Claims| StreamlitUI
    StreamlitUI -->|Suggested Query| SearchEngine[Web Search Engine - search.py]
    SearchEngine -->|Search Queries| DDGS[DuckDuckGo Search API]
    SearchEngine -->|Scrapes Webpages| Scraper[Web Scraper - BeautifulSoup]
    Scraper -->|Full Web Content & Snippets| ClaimVerifier[Claim Verifier - verifier.py]
    
    subgraph LLM Verifiers
        ClaimVerifier -->|Evaluate Evidence| GeminiV[Gemini API]
        ClaimVerifier -->|Evaluate Evidence| GroqV[Groq API]
        ClaimVerifier -->|Evaluate Evidence| OpenAIV[OpenAI API]
    end
    
    GeminiV & GroqV & OpenAIV -->|Structured Verification Report| StreamlitUI
    StreamlitUI -->|Renders UI Report| User
```

### 2. Data Flow Diagram
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as Streamlit Dashboard
    participant Util as PDF Parser (utils.py)
    participant Extractor as Extractor (extractor.py)
    participant Search as Search Layer (search.py)
    participant Verifier as Verifier (verifier.py)
    participant LLM as Selected API (Gemini/Groq/OpenAI)

    User->>App: Uploads marketing PDF & selects Provider
    App->>Util: Send PDF bytes
    Util-->>App: Return page texts list
    App->>Extractor: Send page texts + selected provider
    Extractor->>Extractor: Check key format (Auto-detect)
    Extractor->>LLM: Prompt + text (request JSON)
    LLM-->>Extractor: Return list of claims JSON
    Extractor-->>App: Return claims list
    loop For each claim
        App->>Search: Send suggested search query
        Search->>Search: Run search + crawl top URLs
        Search-->>App: Return scraped page contents
        App->>Verifier: Send claim + context + web evidence
        Verifier->>LLM: Prompt + claim + evidence (verify)
        LLM-->>Verifier: Return verification JSON
        Verifier-->>App: Return report item
    end
    App->>User: Render report UI & enable download links
```

### 3. Component Diagram
```mermaid
classDiagram
    class AppConfig {
        +provider: str
        +api_key: str
        +search_depth: int
    }
    class utils {
        +extract_text_from_pdf(source: Union[str, bytes]) List[Dict]
        +truncate_text(text: str, max_words: int) str
    }
    class extractor {
        +configure_gemini(api_key: str)
        +extract_claims(pages_content: List[Dict], api_key: str, provider: str) List[Dict]
    }
    class search {
        +perform_search(query: str, max_results: int) List[Dict]
        +scrape_url(url: str, timeout: int) str
        +search_and_retrieve_context(query: str, max_results: int) List[Dict]
    }
    class verifier {
        +verify_claim(claim: str, original_context: str, search_results: List[Dict], api_key: str, provider: str) Dict
    }
    
    AppConfig ..> extractor : Configures
    AppConfig ..> verifier : Configures
    utils --> extractor : Feeds text
    search --> verifier : Feeds web evidence
    extractor --> verifier : Feeds claims
    verifier --> AppConfig : Yields reports
```

---

## ⚙️ Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/akshaysharma2703/fact-check-agent.git
   cd fact-check-agent
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Keys**:
   Create a `.env` file in the root directory:
   ```env
   # Add the keys you plan to use
   GROQ_API_KEY=gsk_your_groq_api_key
   OPENAI_API_KEY=sk-your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```
   *Note: If these keys are in your `.env` or system environment, the Streamlit app will load them automatically in the sidebar.*

5. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

---

## 🧪 Testing Instructions

To validate the fact-checking engine against fake statistics, use the programmatically compiled PDF:

1. Run the generator script:
   ```bash
   python generate_trap_pdf.py
   ```
2. Upload the newly generated `trap_marketing_report.pdf` into the app.
3. Observe how the system reacts:
   - **Verified**: "Python released in 1991" / "Earth orbit completes in 365.25 days".
   - **False/Inaccurate**: "Paris population exactly 140 million" / "Eiffel Tower stands 3,000 meters tall in Rome".


---

## 🔮 Future Improvements

- **Async Multi-threading**: Run web searches and verifications for all extracted claims concurrently to reduce total evaluation latency.
- **Reference Document Uploader**: Allow users to upload their own internal reference database (PDFs, spreadsheets) to verify statements against corporate files rather than public search engines.
- **API integrations**: Connect to Slack, Google Drive, and HubSpot to automate compliance review of outgoing sales collateral.
