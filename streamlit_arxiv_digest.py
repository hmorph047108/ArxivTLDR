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
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", GMAIL_USER or DEFAULT_FROM_EMAIL)


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


def calculate_paper_score(paper: arxiv.Result, priority_keywords: List[str], 
                         priority_sources: List[str] = None) -> float:
    """Calculate a relevance score for paper prioritization."""
    score = 0.0
    
    # Base score from recency (newer = higher score)
    days_old = (datetime.now().replace(tzinfo=None) - paper.published.replace(tzinfo=None)).days
    recency_score = max(0, 7 - days_old) / 7  # Higher score for papers within 7 days
    score += recency_score * 2
    
    # Keyword relevance in title (higher weight)
    title_lower = paper.title.lower()
    for keyword in priority_keywords:
        if keyword.lower() in title_lower:
            score += 3
    
    # Keyword relevance in abstract
    abstract_lower = paper.summary.lower()
    for keyword in priority_keywords:
        if keyword.lower() in abstract_lower:
            score += 1
    
    # Author count as proxy for collaboration/institution backing
    author_score = min(len(paper.authors) / 10, 1.0)  # Cap at 1.0
    score += author_score
    
    # Prefer papers from priority sources
    if priority_sources:
        sources = priority_sources
    else:
        sources = ['google', 'openai', 'microsoft', 'meta', 'deepmind', 'anthropic', 
                  'stanford', 'mit', 'berkeley', 'cmu', 'oxford', 'cambridge']
    
    author_text = ' '.join([author.name.lower() for author in paper.authors])
    for source in sources:
        if source.lower().strip() in author_text:
            score += 2  # Higher boost for priority sources
            break
    
    return score


def fetch_papers(keywords: str, max_papers: int, days_back: int = 1, 
                categories: List[str] = None, sort_by_relevance: bool = True,
                priority_sources: str = "") -> List[arxiv.Result]:
    """Search arXiv Computer Science papers with smart filtering and ranking."""
    # Create date filter for recent papers
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Default to key CS categories if none specified
    if not categories:
        categories = [
            "cs.AI",    # Artificial Intelligence
            "cs.LG",    # Machine Learning  
            "cs.CV",    # Computer Vision
            "cs.CL",    # Computation and Language (NLP)
            "cs.RO",    # Robotics
            "cs.CR",    # Cryptography and Security
            "cs.HC",    # Human-Computer Interaction
            "cs.IR",    # Information Retrieval
        ]
    
    # Build query with category filter and keywords
    query_parts = []
    
    # Add category filter
    if categories:
        category_query = " OR ".join([f"cat:{cat}" for cat in categories])
        query_parts.append(f"({category_query})")
    else:
        query_parts.append("cat:cs.*")
    
    # Add keyword filter if provided
    if keywords.strip():
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        keyword_query = ' OR '.join(f'"{kw}"' for kw in keyword_list)
        query_parts.append(f"({keyword_query})")
    
    query = " AND ".join(query_parts)
    
    # Fetch more papers than needed for filtering
    search_limit = max_papers * 3  # Get 3x more for better filtering
    
    search = arxiv.Search(
        query=query,
        max_results=search_limit,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    
    # Filter papers by submission date and calculate scores
    papers_with_scores = []
    priority_keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()] if keywords.strip() else []
    priority_source_list = [src.strip() for src in priority_sources.split(',') if src.strip()] if priority_sources else None
    
    for paper in search.results():
        if paper.published.replace(tzinfo=None) >= cutoff_date:
            if sort_by_relevance:
                score = calculate_paper_score(paper, priority_keywords, priority_source_list)
                papers_with_scores.append((paper, score))
            else:
                papers_with_scores.append((paper, 0))
        
        if len(papers_with_scores) >= search_limit:
            break
    
    # Sort by relevance score if enabled
    if sort_by_relevance:
        papers_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return top papers
    return [paper for paper, score in papers_with_scores[:max_papers]]


def send_email_gmail(to_email: str, subject: str, html_body: str, verbose: bool = False) -> bool:
    """Send email using Gmail SMTP with SSL certificate fix for macOS."""
    import smtplib
    import ssl
    import os
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        if verbose:
            print("❌ Gmail credentials not found")
            print("💡 Add GMAIL_USER and GMAIL_APP_PASSWORD to your .env file")
        else:
            st.error("Gmail credentials not configured")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = GMAIL_USER
        message["To"] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Create SSL context with certificate fix for macOS
        context = ssl.create_default_context()
        
        # Try to use certifi certificates
        try:
            import certifi
            context.load_verify_locations(certifi.where())
            if verbose:
                print(f"📋 Using certifi certificates: {certifi.where()}")
        except ImportError:
            if verbose:
                print("⚠️ Certifi not available, using default certificates")
        
        # Set SSL environment variables for this session
        os.environ['SSL_CERT_FILE'] = certifi.where() if 'certifi' in locals() else ''
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where() if 'certifi' in locals() else ''
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, message.as_string())
        
        if verbose:
            print("✅ Email sent successfully via Gmail!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if verbose:
            if "authentication failed" in error_msg.lower():
                print("❌ Gmail authentication failed")
                print("💡 Make sure you're using an App Password, not your regular password")
            else:
                print(f"❌ Gmail SMTP error: {error_msg}")
        else:
            if "authentication failed" in error_msg.lower():
                st.error("Gmail authentication failed. Use App Password, not regular password.")
            else:
                st.error(f"Gmail error: {error_msg}")
        return False


def send_email(to_email: str, subject: str, html_body: str, verbose: bool = False) -> bool:
    """Send email via Gmail (preferred) or SendGrid fallback."""
    
    # Try Gmail first (easier setup, no SSL issues)
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        if verbose:
            print("📧 Using Gmail SMTP...")
        return send_email_gmail(to_email, subject, html_body, verbose)
    
    # Fallback to SendGrid
    elif SENDGRID_API_KEY:
        if verbose:
            print("📧 Using SendGrid API...")
        return send_email_sendgrid(to_email, subject, html_body, verbose)
    
    # No email service configured
    else:
        if verbose:
            print("❌ No email service configured")
            print("💡 Set up Gmail (easier) or SendGrid in your .env file")
        else:
            st.error("No email service configured. Set up Gmail or SendGrid in .env file.")
        return False


def send_email_sendgrid(to_email: str, subject: str, html_body: str, verbose: bool = False) -> bool:
    """Send email via SendGrid with comprehensive error handling and logging."""
    if not SENDGRID_API_KEY:
        if verbose:
            print("❌ SENDGRID_API_KEY not set")
        else:
            st.error("SENDGRID_API_KEY not set")
        return False
    
    try:
        # Create SendGrid client with SSL handling for macOS certificate issues
        import ssl
        import urllib3
        
        # Disable SSL warnings for certificate issues
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Try to create a permissive SSL context for macOS certificate issues
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        except Exception:
            pass  # Fall back to default behavior
        
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
        # Create mail object
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )
        
        # Send email
        response = sg.send(message)
        
        # Log response details
        if verbose:
            print(f"📧 SendGrid Response Status: {response.status_code}")
            if response.status_code == 202:
                print("✅ Email sent successfully!")
            else:
                print(f"⚠️ Unexpected status code: {response.status_code}")
                print(f"Response body: {response.body}")
                print(f"Response headers: {response.headers}")
        
        # Check if successful (202 is SendGrid's success code)
        if response.status_code == 202:
            return True
        else:
            if not verbose:
                st.error(f"SendGrid returned status code {response.status_code}")
            return False
            
    except Exception as e:
        # Enhanced error handling
        error_msg = str(e)
        
        # Check for common SendGrid errors
        if "API key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            detailed_error = "Invalid SendGrid API key. Please check your SENDGRID_API_KEY."
        elif "forbidden" in error_msg.lower():
            detailed_error = "SendGrid API access forbidden. Check your API key permissions."
        elif "bad request" in error_msg.lower():
            detailed_error = "Invalid email format or content. Check sender/recipient emails."
        elif "rate limit" in error_msg.lower():
            detailed_error = "SendGrid rate limit exceeded. Try again later."
        elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
            detailed_error = "SendGrid quota exceeded or billing issue. Check your account."
        else:
            detailed_error = f"SendGrid error: {error_msg}"
        
        if verbose:
            print(f"❌ Failed to send email: {detailed_error}")
        else:
            st.error(f"Failed to send email: {detailed_error}")
        
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
    
    # Email service status
    if GMAIL_USER and GMAIL_APP_PASSWORD:
        st.success("✅ Gmail SMTP configured")
        st.info("📧 Using Gmail for email delivery")
    elif SENDGRID_API_KEY:
        st.success("✅ SendGrid configured")
        st.info("📧 Using SendGrid for email delivery")
        
        # Test email functionality
        with st.expander("🧪 Test Email Configuration"):
            test_email = st.text_input("Test email address:", placeholder="your@email.com")
            if st.button("📧 Send Test Email") and test_email:
                with st.spinner("Sending test email..."):
                    from datetime import date
                    test_content = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #1a73e8;">🧪 ArXiv Digest - Email Test</h2>
                        <p>This is a test email to verify your SendGrid configuration.</p>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
                            <h3 style="color: #28a745; margin-top: 0;">✅ Configuration Test Successful!</h3>
                            <p>If you're reading this, your email setup is working correctly.</p>
                            <ul>
                                <li>SendGrid API connection verified</li>
                                <li>Email delivery working</li>
                                <li>Ready for daily digest automation!</li>
                            </ul>
                        </div>
                        <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                            Test sent on {date.today().strftime('%B %d, %Y')}
                        </p>
                    </div>
                    """
                    
                    success = send_email(
                        to_email=test_email,
                        subject="ArXiv Digest - Email Configuration Test",
                        html_body=test_content
                    )
                    
                    if success:
                        st.success("✅ Test email sent! Check your inbox.")
                    else:
                        st.error("❌ Test email failed. Check your SendGrid configuration.")
    else:
        st.warning("⚠️ SendGrid not configured")
        st.info("Email delivery disabled")
        
        with st.expander("🔧 SendGrid Setup Guide"):
            st.markdown("""
            **To enable email delivery:**
            1. Sign up at [SendGrid](https://sendgrid.com/)
            2. Verify your sender email address
            3. Create an API key with Mail Send permissions
            4. Add `SENDGRID_API_KEY=SG.your_key_here` to your `.env` file
            5. Restart the app and test email functionality
            """)
    
    st.markdown("---")
    
    # Daily Digest Targeting
    st.header("🎯 Daily Digest Settings")
    
    # Category selection
    st.subheader("📚 ArXiv Categories")
    category_options = {
        "cs.AI": "🤖 Artificial Intelligence",
        "cs.LG": "🧠 Machine Learning", 
        "cs.CV": "👁️ Computer Vision",
        "cs.CL": "🗣️ Natural Language Processing",
        "cs.RO": "🤖 Robotics",
        "cs.CR": "🔒 Cryptography & Security",
        "cs.HC": "👥 Human-Computer Interaction",
        "cs.IR": "🔍 Information Retrieval",
        "cs.NE": "🧬 Neural & Evolutionary Computing",
        "cs.DC": "💻 Distributed Computing",
    }
    
    selected_categories = st.multiselect(
        "Select categories to monitor:",
        options=list(category_options.keys()),
        default=["cs.AI", "cs.LG", "cs.CV", "cs.CL"],
        format_func=lambda x: category_options[x],
        help="Choose which ArXiv categories to include in your daily digest"
    )
    
    # Smart filtering options
    st.subheader("🧠 Smart Filtering")
    sort_by_relevance = st.checkbox(
        "Enable relevance scoring",
        value=True,
        help="Prioritize papers by keyword relevance, recency, and author reputation"
    )
    
    # Priority institutions/companies
    st.subheader("🏢 Priority Sources")
    priority_sources = st.text_input(
        "Priority institutions/companies:",
        value="google, openai, anthropic, deepmind",
        help="Comma-separated list of preferred authors/institutions (will boost paper scores)"
    )
    
    st.markdown("---")
    
    # Daily automation settings
    st.header("⏰ Daily Automation")
    st.info("💡 **Pro Tip**: For daily automation, save these settings and run via cron job or GitHub Actions")
    
    # Export configuration
    if st.button("📋 Export Config for Automation", help="Generate command for daily automation"):
        config = {
            "keywords": keywords if 'keywords' in locals() else DEFAULT_KEYWORDS,
            "categories": selected_categories,
            "max_papers": max_papers if 'max_papers' in locals() else 5,
            "days_back": days_back if 'days_back' in locals() else 1,
            "sort_by_relevance": sort_by_relevance,
            "priority_sources": priority_sources,
            "email": email if 'email' in locals() else ""
        }
        
        st.code(f"""
# Daily ArXiv Digest Automation Config
# Save this as config.json and use with automation script

{json.dumps(config, indent=2)}
        """, language="json")
        
        # Generate automation command
        automation_cmd = f"""
# Example cron job (runs daily at 8 AM):
# 0 8 * * * cd /path/to/arxiv-digest && python daily_digest.py

python daily_digest.py \\
  --keywords "{config['keywords']}" \\
  --categories "{','.join(config['categories'])}" \\
  --max-papers {config['max_papers']} \\
  --email "{config['email']}" \\
  --priority-sources "{config['priority_sources']}"
        """
        
        st.code(automation_cmd, language="bash")

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

    # Search for papers with smart filtering
    with st.spinner("🔎 Searching arXiv for recent papers..."):
        papers = fetch_papers(
            keywords=keywords, 
            max_papers=max_papers, 
            days_back=days_back,
            categories=selected_categories if selected_categories else None,
            sort_by_relevance=sort_by_relevance,
            priority_sources=priority_sources
        )
    
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