#!/usr/bin/env python3
"""
Gmail SMTP Email Alternative
Simple email sending using Gmail's SMTP server - no API keys required!

Setup:
1. Enable 2-factor authentication on your Gmail account
2. Generate an "App Password" in your Google Account settings
3. Use your Gmail address and app password

Much easier than SendGrid!
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_email_gmail(to_email: str, subject: str, html_body: str, verbose: bool = False) -> bool:
    """Send email using Gmail SMTP - much easier than SendGrid!"""
    
    # Get Gmail credentials from environment
    gmail_user = os.getenv("GMAIL_USER")  # your.email@gmail.com
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # app password, not regular password
    
    if not gmail_user or not gmail_password:
        if verbose:
            print("❌ Gmail credentials not found")
            print("💡 Add GMAIL_USER and GMAIL_APP_PASSWORD to your .env file")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = gmail_user
        message["To"] = to_email
        
        # Add HTML content
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Create secure connection and send email
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, message.as_string())
        
        if verbose:
            print("✅ Email sent successfully via Gmail!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if verbose:
            if "authentication failed" in error_msg.lower():
                print("❌ Gmail authentication failed")
                print("💡 Make sure you're using an App Password, not your regular password")
                print("💡 Enable 2FA and create App Password: https://support.google.com/accounts/answer/185833")
            else:
                print(f"❌ Gmail SMTP error: {error_msg}")
        return False

if __name__ == "__main__":
    # Test Gmail email
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Gmail SMTP email")
    parser.add_argument("--to", required=True, help="Email to send to")
    args = parser.parse_args()
    
    test_html = """
    <h2>🧪 Gmail SMTP Test</h2>
    <p>If you're reading this, Gmail SMTP is working perfectly!</p>
    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px;">
        <h3>✅ Gmail Setup Successful!</h3>
        <ul>
            <li>No API keys needed</li>
            <li>No SSL certificate issues</li>
            <li>Free and reliable</li>
            <li>Ready for daily ArXiv digest!</li>
        </ul>
    </div>
    """
    
    print("🧪 Testing Gmail SMTP...")
    success = send_email_gmail(
        to_email=args.to,
        subject="ArXiv Digest - Gmail SMTP Test",
        html_body=test_html,
        verbose=True
    )
    
    if success:
        print("🎉 Gmail SMTP working perfectly!")
    else:
        print("❌ Gmail SMTP failed - check your credentials")