# Streamlit ArXiv Digest App – MVP
"""
A minimal Streamlit application that
1. Takes a list of keywords (default AI/CS), user email, and number of papers.
2. Queries arXiv for today's papers in Computer Science (cs.*) matching the keywords.
3. Uses Google Gemini Flash 2.0 to summarise each abstract into a crisp TL;DR.
4. Displays the summaries on‑screen and emails them via SendGrid.

Environment variables required:
  OPENROUTER_API_KEY – OpenRouter API key for Gemini Flash access
  SENDGRID_API_KEY   – SendGrid credentials (optional)
  OPENROUTER_SITE_URL – Your site URL (optional, for rankings)
  OPENROUTER_SITE_NAME – Your site name (optional, for rankings)

Run with:  streamlit run streamlit_arxiv_digest.py
"""

from __future__ import annotations

import os
import textwrap
from datetime import date, datetime, timedelta
from typing import List, Tuple

import arxiv  # pip install arxiv
import requests  # pip install requests
import json
import streamlit as st  # pip install streamlit
from dotenv import load_dotenv  # pip install python-dotenv
from sendgrid import SendGridAPIClient  # pip install sendgrid
from sendgrid.helpers.mail import Mail

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GEMINI_MODEL = "google/gemini-2.0-flash-001"  # OpenRouter Gemini Flash 2.0
DEFAULT_KEYWORDS = "artificial intelligence, machine learning, computer vision, NLP"
MAX_RESULTS = 20  # safety cap
DEFAULT_FROM_EMAIL = "digest@artefact.ai"

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "ArXiv Daily Digest")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", DEFAULT_FROM_EMAIL)


def summarise_abstract(abstract: str) -> str:
    """Call Google Gemini via OpenRouter to compress an abstract into <=120 words consultancy‑style."""
    if not OPENROUTER_API_KEY:
        return "⚠️ OpenRouter API key not configured. Please set OPENROUTER_API_KEY in your environment."
    
    try:
        prompt = f"""You are an expert ML analyst. Summarise the following research abstract in <=120 words, 
        bullet style, focusing on contribution and why it matters. Avoid jargon and make it accessible.

        Abstract: {abstract}

        Format your response as concise bullet points highlighting:
        • Key contribution/innovation
        • Why it matters/potential impact
        • Technical approach (simplified)"""
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # Add optional headers if configured
        if OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = OPENROUTER_SITE_URL
        if OPENROUTER_SITE_NAME:
            headers["X-Title"] = OPENROUTER_SITE_NAME
        
        data = {
            "model": GEMINI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 200,
        }
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=30
        )
        
        if response.status_code != 200:
            return f"❌ API Error {response.status_code}: {response.text}"
        
        response_data = response.json()
        
        if "error" in response_data:
            return f"❌ OpenRouter Error: {response_data['error'].get('message', 'Unknown error')}"
        
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"].strip()
        else:
            return "❌ No response content received from OpenRouter API"
            
    except requests.exceptions.Timeout:
        return "❌ Request timeout - try again later"
    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {str(e)}"
    except Exception as e:
        return f"❌ Error generating summary: {str(e)}"


def fetch_papers(keywords: str, max_papers: int, days_back: int = 1) -> List[arxiv.Result]:
    """Search arXiv Computer Science papers from recent days using keyword query."""
    # Create date filter for recent papers
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Build query with category filter and keywords
    query_parts = []
    if keywords.strip():
        # Split keywords and create OR query
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        keyword_query = ' OR '.join(f'"{kw}"' for kw in keyword_list)
        query_parts.append(f"({keyword_query})")
    
    # Add Computer Science category filter
    query_parts.append("cat:cs.*")
    
    query = " AND ".join(query_parts)
    
    search = arxiv.Search(
        query=query,
        max_results=max_papers,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    
    # Filter papers by submission date
    papers = []
    for paper in search.results():
        if paper.published.replace(tzinfo=None) >= cutoff_date:
            papers.append(paper)
        if len(papers) >= max_papers:
            break
    
    return papers


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via SendGrid. Returns True if successful."""
    if not SENDGRID_API_KEY:
        st.error("SENDGRID_API_KEY not set – skipping email")
        return False
    
    try:
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        mail = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_body,
        )
        response = sg.send(mail)
        return response.status_code == 202
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False


def format_paper_html(paper: arxiv.Result, summary: str) -> str:
    """Format a single paper for HTML email."""
    authors = ", ".join([author.name for author in paper.authors[:3]])
    if len(paper.authors) > 3:
        authors += " et al."
    
    return f"""
    <div style="margin-bottom: 30px; padding: 20px; border-left: 4px solid #4285f4; background-color: #f8f9fa;">
        <h3 style="margin-top: 0; color: #1a73e8;">{paper.title}</h3>
        <p style="color: #5f6368; margin: 5px 0;"><strong>Authors:</strong> {authors}</p>
        <p style="color: #5f6368; margin: 5px 0;"><strong>Published:</strong> {paper.published.strftime('%Y-%m-%d')}</p>
        <div style="margin: 15px 0;">
            {summary.replace('\n', '<br>')}
        </div>
        <p style="margin-top: 15px;">
            <a href="{paper.pdf_url}" style="color: #1a73e8; text-decoration: none; margin-right: 15px;">📄 PDF</a>
            <a href="{paper.entry_id}" style="color: #1a73e8; text-decoration: none;">🔗 arXiv</a>
        </p>
    </div>
    """


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ArXiv Daily Digest", 
    page_icon="📚",
    layout="wide"
)

st.title("📚 ArXiv Daily Digest – AI & CS")
st.markdown("*Get personalized summaries of the latest Computer Science research papers*")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key status
    if OPENROUTER_API_KEY:
        st.success("✅ OpenRouter API configured")
        st.info(f"Using model: {GEMINI_MODEL}")
    else:
        st.error("❌ OpenRouter API key missing")
        st.info("Set OPENROUTER_API_KEY in your .env file")
    
    if SENDGRID_API_KEY:
        st.success("✅ SendGrid configured")
    else:
        st.warning("⚠️ SendGrid not configured")
        st.info("Email delivery disabled")

# Main form
col1, col2 = st.columns([2, 1])

with col1:
    email = st.text_input(
        "📧 Your email address", 
        placeholder="you@company.com",
        help="Where to send the digest"
    )
    
    keywords = st.text_input(
        "🔍 Keywords to watch", 
        value=DEFAULT_KEYWORDS,
        help="Comma-separated keywords for paper search"
    )

with col2:
    max_papers = st.slider(
        "📊 Number of papers", 
        min_value=1, 
        max_value=MAX_RESULTS, 
        value=5,
        help="Maximum papers to include"
    )
    
    days_back = st.selectbox(
        "📅 Search papers from",
        options=[1, 2, 3, 7],
        index=0,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}",
        help="How far back to search for papers"
    )

# Generate button
generate = st.button("🚀 Generate & Send Digest", type="primary", use_container_width=True)

if generate:
    if not email:
        st.error("Please enter a valid email address.")
        st.stop()
    
    if not OPENROUTER_API_KEY:
        st.error("OpenRouter API key not configured. Please set OPENROUTER_API_KEY in your environment.")
        st.stop()

    # Search for papers
    with st.spinner("🔎 Searching arXiv for recent papers..."):
        papers = fetch_papers(keywords, max_papers, days_back)
    
    if not papers:
        st.warning(f"No matching papers found in the last {days_back} day(s). Try adjusting your keywords or extending the search period.")
        st.stop()

    st.success(f"Found {len(papers)} papers matching your criteria!")
    
    # Generate summaries and display
    st.header(f"📋 Papers Summary ({len(papers)} papers)")
    
    digests = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, paper in enumerate(papers):
        # Update progress
        progress = (i + 1) / len(papers)
        progress_bar.progress(progress)
        status_text.text(f"Processing paper {i + 1}/{len(papers)}: {paper.title[:50]}...")
        
        # Display paper
        with st.expander(f"📄 {paper.title}", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Generate summary
                with st.spinner("Generating AI summary..."):
                    summary = summarise_abstract(paper.summary)
                
                st.markdown("**🤖 AI Summary:**")
                st.markdown(summary)
                
                # Show authors and date
                authors = ", ".join([author.name for author in paper.authors[:3]])
                if len(paper.authors) > 3:
                    authors += " et al."
                st.caption(f"**Authors:** {authors}")
                st.caption(f"**Published:** {paper.published.strftime('%Y-%m-%d')}")
            
            with col2:
                st.markdown("**🔗 Links:**")
                st.markdown(f"[📄 PDF]({paper.pdf_url})")
                st.markdown(f"[🔗 arXiv]({paper.entry_id})")
        
        digests.append((paper, summary))
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Send email if configured
    if SENDGRID_API_KEY and email:
        with st.spinner("📧 Sending email digest..."):
            # Build email HTML
            html_parts = [
                f"""
                <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                    <h1 style="color: #1a73e8; text-align: center;">📚 ArXiv Daily Digest</h1>
                    <h2 style="color: #5f6368; text-align: center;">{len(digests)} AI/CS Papers for {date.today().strftime('%B %d, %Y')}</h2>
                    <p style="text-align: center; color: #5f6368;">Keywords: {keywords}</p>
                    <hr style="border: 1px solid #e0e0e0; margin: 30px 0;">
                """
            ]
            
            for paper, summary in digests:
                html_parts.append(format_paper_html(paper, summary))
            
            html_parts.append("""
                <hr style="border: 1px solid #e0e0e0; margin: 30px 0;">
                <p style="text-align: center; color: #9aa0a6; font-size: 12px;">
                    Generated by ArXiv Digest App • Powered by Google Gemini via OpenRouter
                </p>
                </div>
            """)
            
            html_body = "\n".join(html_parts)
            
            success = send_email(
                to_email=email,
                subject=f"ArXiv Digest – {date.today().strftime('%B %d, %Y')}",
                html_body=html_body,
            )
            
            if success:
                st.success("📧 Digest sent successfully! Check your inbox.")
            else:
                st.error("❌ Failed to send email. Please check your SendGrid configuration.")
    else:
        if not SENDGRID_API_KEY:
            st.info("📧 Email not sent - SendGrid not configured")
        else:
            st.info("📧 Ready to send - click the button above to include email delivery")

    # Download option
    if digests:
        st.header("💾 Download Options")
        
        # Create downloadable text version
        text_content = f"ArXiv Digest - {date.today().strftime('%B %d, %Y')}\n"
        text_content += f"Keywords: {keywords}\n"
        text_content += "=" * 60 + "\n\n"
        
        for paper, summary in digests:
            text_content += f"Title: {paper.title}\n"
            text_content += f"Authors: {', '.join([author.name for author in paper.authors[:3]])}\n"
            text_content += f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
            text_content += f"PDF: {paper.pdf_url}\n"
            text_content += f"arXiv: {paper.entry_id}\n\n"
            text_content += "Summary:\n" + summary + "\n\n"
            text_content += "-" * 60 + "\n\n"
        
        st.download_button(
            label="📄 Download as Text",
            data=text_content,
            file_name=f"arxiv_digest_{date.today().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )