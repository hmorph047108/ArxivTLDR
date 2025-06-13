#!/usr/bin/env python3
"""
Daily ArXiv Digest - Automated Script
Run this script daily via cron job or CI/CD for automated digest delivery.

Usage:
    python daily_digest.py --email your@email.com
    python daily_digest.py --config config.json
    
Example cron job (daily at 8 AM):
    0 8 * * * cd /path/to/arxiv-digest && python daily_digest.py --config config.json
"""

import argparse
import json
import os
import sys
from datetime import date
from typing import List

# Import functions from main app
from streamlit_arxiv_digest import (
    fetch_papers, summarise_abstract, send_email, format_paper_html
)

def load_config(config_path: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in config file: {config_path}")
        sys.exit(1)

def generate_daily_digest(
    email: str,
    keywords: str = "artificial intelligence, machine learning, computer vision, NLP",
    categories: List[str] = None,
    max_papers: int = 20,
    days_back: int = 7,
    sort_by_relevance: bool = True,
    priority_sources: str = "google, openai, anthropic, deepmind"
) -> bool:
    """Generate and send daily digest."""
    
    print(f"🔍 Searching for papers...")
    print(f"   Keywords: {keywords}")
    print(f"   Categories: {categories or 'All CS'}")
    print(f"   Max papers: {max_papers}")
    print(f"   Days back: {days_back}")
    
    # Fetch papers
    papers = fetch_papers(
        keywords=keywords,
        max_papers=max_papers,
        days_back=days_back,
        categories=categories,
        sort_by_relevance=sort_by_relevance,
        priority_sources=priority_sources
    )
    
    if not papers:
        print("⚠️ No papers found matching criteria")
        return False
    
    print(f"📚 Found {len(papers)} papers")
    
    # Generate summaries
    digests = []
    for i, paper in enumerate(papers, 1):
        print(f"🤖 Generating summary {i}/{len(papers)}: {paper.title[:50]}...")
        summary = summarise_abstract(paper.summary)
        
        if summary.startswith("❌"):
            print(f"   Warning: {summary}")
            summary = "Summary generation failed - see original abstract"
        
        digests.append((paper, summary))
    
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
            Generated by ArXiv Digest App (Automated) • Powered by Google Gemini via OpenRouter
        </p>
        </div>
    """)
    
    html_body = "\n".join(html_parts)
    
    # Send email
    print(f"📧 Sending digest to {email}...")
    success = send_email(
        to_email=email,
        subject=f"ArXiv Daily Digest – {date.today().strftime('%B %d, %Y')}",
        html_body=html_body,
        verbose=True  # Enable detailed logging for CLI usage
    )
    
    if success:
        print("✅ Digest sent successfully!")
        return True
    else:
        print("❌ Failed to send digest")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate daily ArXiv digest")
    parser.add_argument("--email", help="Email address to send digest to")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--keywords", default="artificial intelligence, machine learning, computer vision, NLP")
    parser.add_argument("--categories", help="Comma-separated list of categories (e.g., cs.AI,cs.LG)")
    parser.add_argument("--max-papers", type=int, default=20, help="Maximum number of papers")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back for papers")
    parser.add_argument("--priority-sources", default="google, openai, anthropic, deepmind")
    parser.add_argument("--no-relevance-sort", action="store_true", help="Disable relevance sorting")
    
    args = parser.parse_args()
    
    # Load config if provided
    if args.config:
        config = load_config(args.config)
        # Use config values with command line overrides
        email = args.email or config.get("email")
        keywords = args.keywords if args.keywords != parser.get_default("keywords") else config.get("keywords", args.keywords)
        categories = config.get("categories", None)
        max_papers = args.max_papers if args.max_papers != parser.get_default("max_papers") else config.get("max_papers", args.max_papers)
        days_back = args.days_back if args.days_back != parser.get_default("days_back") else config.get("days_back", args.days_back)
        priority_sources = args.priority_sources if args.priority_sources != parser.get_default("priority_sources") else config.get("priority_sources", args.priority_sources)
        sort_by_relevance = config.get("sort_by_relevance", not args.no_relevance_sort)
    else:
        email = args.email
        keywords = args.keywords
        categories = args.categories.split(",") if args.categories else None
        max_papers = args.max_papers
        days_back = args.days_back
        priority_sources = args.priority_sources
        sort_by_relevance = not args.no_relevance_sort
    
    # Validate email is provided
    if not email:
        print("❌ Email address is required")
        print("💡 Provide --email argument or set 'email' in config file")
        sys.exit(1)
    
    # Check required environment variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)
    
    if not os.getenv("SENDGRID_API_KEY"):
        print("⚠️ SENDGRID_API_KEY not set - email sending may fail")
    
    print("🚀 Starting daily ArXiv digest generation...")
    print(f"📧 Target email: {email}")
    
    success = generate_daily_digest(
        email=email,
        keywords=keywords,
        categories=categories,
        max_papers=max_papers,
        days_back=days_back,
        sort_by_relevance=sort_by_relevance,
        priority_sources=priority_sources
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()