import streamlit as st
import os
import pandas as pd
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils import extract_text_from_pdf, truncate_text
from extractor import extract_claims
from search import search_and_retrieve_context
from verifier import verify_claim

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Streamlit Page Configuration
st.set_page_config(
    page_title="TruthLayer | Fact-Checking AI Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    /* Dark glassmorphism details */
    .stApp {
        background: #0d0f16;
        color: #f1f3f9;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #d1d5db !important;
        font-size: 1.1rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .claim-card {
        background: rgba(23, 28, 41, 0.85);
        border-radius: 10px;
        border-left: 5px solid #cccccc;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .verified-border { border-left-color: #10b981 !important; }
    .inaccurate-border { border-left-color: #f59e0b !important; }
    .false-border { border-left-color: #ef4444 !important; }
    .unverified-border { border-left-color: #8b5cf6 !important; }
    
    .status-tag {
        font-size: 0.85rem;
        font-weight: 700;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .tag-verified { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
    .tag-inaccurate { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .tag-false { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    .tag-unverified { background: rgba(139, 92, 246, 0.2); color: #8b5cf6; border: 1px solid #8b5cf6; }
</style>
""", unsafe_allow_html=True)

# Sample Document Data
SAMPLE_CONTENT = [
    {
        "page": 1,
        "text": """
        ACME CORPORATION - ANNUAL SHAREHOLDER REPORT (2025)
        
        Introduction:
        Our company, Acme Corporation, founded on March 15, 1999, has achieved major milestones.
        According to industry reports, the global market size for CRM software reached $750 Billion in 2023.
        We have captured a substantial market share, and Python, our core backend language (which was first released in 1991), 
        allows us to scale seamlessly.
        
        Key Achievements & Performance:
        1. Our team completed our core microservices migration on October 12, 2024.
        2. The population of the city of Paris in 2020 was exactly 140 million people, making it our largest market.
        3. According to global statistics databases, the Earth takes approximately 365.25 days to complete one orbit around the Sun.
        4. Global GDP in the year 2023 was estimated to be around $105 Trillion.
        """
    }
]

# Sidebar Configurations
st.sidebar.markdown("<h1 style='text-align: center; font-size: 5rem; margin-top: -1.5rem; margin-bottom: 0.5rem;'>🛡️</h1>", unsafe_allow_html=True)
st.sidebar.title("Configuration")

# Provider Selection
provider = st.sidebar.selectbox(
    "Inference Engine Provider",
    ["Groq", "Google Gemini", "OpenAI"],
    index=0 if os.environ.get("GROQ_API_KEY") else (2 if os.environ.get("OPENAI_API_KEY") else 1),
    help="Toggle between Groq (Ultra-fast Llama-3-70b-8192), Google Gemini (gemini-1.5-flash), and OpenAI (gpt-4o-mini)."
)

# Load values based on selection
if provider == "Groq":
    api_key = st.sidebar.text_input(
        "Groq API Key",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Input your Groq API key (starts with gsk_). Defaults to the saved credentials."
    )
elif provider == "OpenAI":
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Input your OpenAI API key (starts with sk-). Defaults to the environment configuration."
    )
else:
    api_key = st.sidebar.text_input(
        "Google Gemini API Key",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Input your Google Gemini API key. Defaults to the environment configuration."
    )

search_depth = st.sidebar.slider(
    "Search Depth (Sources per claim)",
    min_value=1,
    max_value=4,
    value=2,
    help="How many live web URLs GATM should crawl and parse for each claim."
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### How it works
1. **Upload PDF**: Submit your presentation deck, report, or copy.
2. **Extract Claims**: The LLM parses text and isolates statistics, percentages, dates, and metrics.
3. **Live Search**: The system runs targeted queries using DuckDuckGo Search.
4. **Crawl & Verify**: The top pages are scraped and checked against extracted facts using LLM reasoning.
5. **Score & Correct**: Results are classified with supporting evidence and corrected facts.
""")

# Main Title Header
st.markdown("""
<div class="main-header">
    <h1>🛡️ TruthLayer</h1>
    <p>Enterprise Fact-Checking AI Agent & Live Verification Engine</p>
</div>
""", unsafe_allow_html=True)

# Main UI Tabs
tab1, tab2 = st.tabs(["📄 Fact Checker", "📖 Information & Guide"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Source Data Input")
        upload_mode = st.radio("Choose Input Method:", ["Upload Marketing PDF", "Use Sample Marketing Stats"])
        
        pdf_pages = None
        
        if upload_mode == "Upload Marketing PDF":
            uploaded_file = st.file_uploader("Upload marketing PDF document:", type=["pdf"])
            if uploaded_file is not None:
                with st.spinner("Parsing PDF text content..."):
                    try:
                        pdf_bytes = uploaded_file.read()
                        pdf_pages = extract_text_from_pdf(pdf_bytes)
                        st.success(f"Successfully loaded PDF! Total pages: {len(pdf_pages)}")
                    except Exception as e:
                        st.error(f"Error reading PDF file: {str(e)}")
        else:
            st.info("The sample document contains a combination of accurate and false marketing claims for validation testing.")
            if st.checkbox("Preview Sample Document Text"):
                st.text_area("Sample Document Text", SAMPLE_CONTENT[0]["text"], height=200, disabled=True)
            pdf_pages = SAMPLE_CONTENT

        # Button to run check
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("🚀 Analyze & Verify Claims", use_container_width=True)

    with col2:
        st.subheader("2. Extracted Plain Text Summary")
        if pdf_pages:
            total_words = sum(len(p["text"].split()) for p in pdf_pages)
            st.metric("Total Pages Detected", len(pdf_pages))
            st.metric("Word Count", total_words)
            with st.expander("Show Extracted Plain Text"):
                for p in pdf_pages:
                    st.markdown(f"**Page {p['page']}**")
                    st.write(p["text"])
        else:
            st.write("No document loaded yet. Please upload a PDF or select the sample data.")

    # Execution Loop
    if run_btn:
        if not api_key:
            st.error(f"⚠️ {provider} API Key is missing. Please input your key in the sidebar configuration.")
        elif not pdf_pages:
            st.error("⚠️ No document text detected. Please upload a valid PDF or use the sample.")
        else:
            # 1. Extraction Phase
            progress_bar = st.progress(0, text="Initializing Claim Extraction...")
            
            try:
                # Save API key to environment temporarily so helper modules can fetch it
                if provider == "Groq":
                    os.environ["GROQ_API_KEY"] = api_key
                elif provider == "OpenAI":
                    os.environ["OPENAI_API_KEY"] = api_key
                else:
                    os.environ["GEMINI_API_KEY"] = api_key
                
                progress_bar.progress(15, text=f"Extracting key claims using {provider}...")
                claims = extract_claims(pdf_pages, api_key=api_key, provider=provider)
                
                if not claims:
                    st.warning("No verify-worthy factual claims (dates, metrics, sizes, growth figures) were detected in the text.")
                    progress_bar.empty()
                else:
                    st.success(f"Extracted {len(claims)} verify-worthy factual claims!")
                    
                    # Store claims in state
                    st.session_state["extracted_claims"] = claims
                    st.session_state["verification_reports"] = []
                    
                    # 2. Verification Phase
                    total_claims = len(claims)
                    for i, claim_item in enumerate(claims):
                        claim_txt = claim_item["claim"]
                        query = claim_item["suggested_search_query"]
                        page_num = claim_item["page_number"]
                        
                        step_percent = int(20 + (i / total_claims) * 75)
                        progress_bar.progress(
                            step_percent, 
                            text=f"Verifying claim {i+1}/{total_claims} ({provider}): '{truncate_text(claim_txt, 8)}'"
                        )
                        
                        # Live search & crawl
                        search_results = search_and_retrieve_context(query, max_results=search_depth)
                        
                        # Evaluate against crawled text
                        verification = verify_claim(
                            claim=claim_txt,
                            original_context=claim_item["original_context"],
                            search_results=search_results,
                            api_key=api_key,
                            provider=provider
                        )
                        
                        # Merge metadata
                        report_item = {
                            "claim": claim_txt,
                            "category": claim_item["category"],
                            "page_number": page_num,
                            "original_context": claim_item["original_context"],
                            "search_query": query,
                            "status": verification.get("status", "Unverified"),
                            "confidence_score": verification.get("confidence_score", 0.0),
                            "supporting_evidence": verification.get("supporting_evidence", "No evidence"),
                            "correct_fact": verification.get("correct_fact", "N/A"),
                            "source_url": verification.get("source_url", "")
                        }
                        st.session_state["verification_reports"].append(report_item)
                        
                    progress_bar.progress(100, text="All claims successfully verified!")
                    st.balloons()
                    
            except Exception as ex:
                st.error(f"Execution Error: {str(ex)}")
                logger.exception("An error occurred during verification execution loop")
            finally:
                # Clear progress bar
                progress_bar.empty()

    # Results Rendering
    if "verification_reports" in st.session_state and st.session_state["verification_reports"]:
        reports = st.session_state["verification_reports"]
        
        st.markdown("---")
        st.header("🛡️ Verification Analysis Report")
        
        # Calculate metric counts
        total = len(reports)
        verified = sum(1 for r in reports if r["status"] == "Verified")
        inaccurate = sum(1 for r in reports if r["status"] == "Inaccurate")
        false_count = sum(1 for r in reports if r["status"] == "False")
        unverified = sum(1 for r in reports if r["status"] == "Unverified")
        
        # Display KPI Metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"<div class='metric-card'><h3>🔍 Total</h3><h2>{total}</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-card' style='border-color: #10b981;'><h3 style='color: #10b981;'>✅ Verified</h3><h2>{verified}</h2></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-card' style='border-color: #f59e0b;'><h3 style='color: #f59e0b;'>⚠️ Inaccurate</h3><h2>{inaccurate}</h2></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='metric-card' style='border-color: #ef4444;'><h3 style='color: #ef4444;'>❌ False</h3><h2>{false_count}</h2></div>", unsafe_allow_html=True)
        with m5:
            st.markdown(f"<div class='metric-card' style='border-color: #8b5cf6;'><h3 style='color: #8b5cf6;'>❓ Unverified</h3><h2>{unverified}</h2></div>", unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Status Filter Row
        filter_status = st.selectbox(
            "Filter report by verification status:", 
            ["Show All Claims", "Verified Only", "Inaccurate Only", "False Only", "Unverified Only"]
        )
        
        filtered_reports = reports
        if filter_status == "Verified Only":
            filtered_reports = [r for r in reports if r["status"] == "Verified"]
        elif filter_status == "Inaccurate Only":
            filtered_reports = [r for r in reports if r["status"] == "Inaccurate"]
        elif filter_status == "False Only":
            filtered_reports = [r for r in reports if r["status"] == "False"]
        elif filter_status == "Unverified Only":
            filtered_reports = [r for r in reports if r["status"] == "Unverified"]
            
        # Draw filtered results
        for idx, r in enumerate(filtered_reports):
            status = r["status"]
            border_class = "unverified-border"
            tag_class = "tag-unverified"
            
            if status == "Verified":
                border_class = "verified-border"
                tag_class = "tag-verified"
            elif status == "Inaccurate":
                border_class = "inaccurate-border"
                tag_class = "tag-inaccurate"
            elif status == "False":
                border_class = "false-border"
                tag_class = "tag-false"
                
            st.markdown(f"""
            <div class="claim-card {border_class}">
                <span class="status-tag {tag_class}">{status}</span>
                <span style="float: right; color: #9ca3af; font-size: 0.9rem;">Page {r['page_number']} | Category: {r['category']}</span>
                <h3>{r['claim']}</h3>
                <p style="font-style: italic; color: #9ca3af; margin-top: 5px;">"Original Document Context: {r['original_context']}"</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Details Expander
            with st.expander(f"Inspect Verification Details (Claim #{idx+1})"):
                c_details, c_stats = st.columns([3, 1])
                with c_details:
                    st.write("**🔍 Search Query Formulated:**")
                    st.code(r["search_query"])
                    
                    st.write("**📚 Supporting Evidence Extracted:**")
                    st.info(r["supporting_evidence"])
                    
                    if status in ["Inaccurate", "False"]:
                        st.write("🤖 **Corrected Fact Claim:**")
                        st.success(r["correct_fact"])
                        
                    if r["source_url"]:
                        st.write("🌐 **Verification Source Link:**")
                        st.markdown(f"[{r['source_url']}]({r['source_url']})")
                    else:
                        st.write("🌐 **Verification Source:** None Found")
                        
                with c_stats:
                    st.write("**Confidence Score Meter:**")
                    conf = r["confidence_score"]
                    st.metric("Confidence Level", f"{int(conf * 100)}%")
                    st.progress(conf)
                    
        # Export Actions
        st.markdown("---")
        st.subheader("💾 Export Verification Ledger")
        
        col_dl1, col_dl2 = st.columns(2)
        
        # Construct exports
        df_export = pd.DataFrame(reports)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        json_data = json.dumps(reports, indent=2).encode('utf-8')
        
        with col_dl1:
            st.download_button(
                label="📥 Download CSV Report",
                data=csv_data,
                file_name="truthlayer_verification_report.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="📥 Download JSON Report",
                data=json_data,
                file_name="truthlayer_verification_report.json",
                mime="application/json",
                use_container_width=True
            )

with tab2:
    st.subheader("📖 Complete Deployment & Execution Guide")
    st.markdown("""
    ### System Architecture & Logic Flow
    This application acts as a real-time factual filter for marketing documentation, mapping source claims onto search vectors.
    
    * **Step 1: Upload & Extraction**: PyMuPDF reads the PDF raw stream. The text is packed with page location markers and evaluated by LLMs (Groq, OpenAI, or Google Gemini) using structured JSON formats to isolate dates, figures, and quantities.
    * **Step 2: Web Search**: DuckDuckGo text indices are queried with neutralized terms. The top destination URLs are downloaded, parsed, and parsed through BeautifulSoup.
    * **Step 3: Verification**: The scraped webpage blocks and snippets are compared with the claims. The selected LLM model makes classifications, extracts supporting quotes, and compiles correction reports.
    
    ### API & Environment Variables
    To run this application, make sure to configure either:
    * `GROQ_API_KEY`: Required for ultra-fast Llama-3-70b-8192 inference.
    * `OPENAI_API_KEY`: Required for GPT-4o-mini inference.
    * `GEMINI_API_KEY`: Required for Google Generative AI models.
    
    ### Running the Application Locally
    1. Clone this repository or open the project folder.
    2. Run a virtual environment setup:
       ```bash
       python -m venv venv
       source venv/bin/activate  # On Windows: venv\\Scripts\\activate
       ```
    3. Install dependencies:
       ```bash
       pip install -r requirements.txt
       ```
    4. Start the Streamlit application:
       ```bash
       streamlit run app.py
       ```
    """)
