#!/usr/bin/env python3
"""
SSL Certificate Fix for macOS
This script fixes SSL certificate issues on macOS Python installations.
"""

import ssl
import os
import subprocess
import sys

def fix_certificates():
    """Fix SSL certificates for Python on macOS."""
    print("🔧 Fixing SSL Certificates for macOS...")
    print("=" * 50)
    
    try:
        # Method 1: Set environment variables
        import certifi
        cert_path = certifi.where()
        os.environ['SSL_CERT_FILE'] = cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        print(f"✅ Set SSL_CERT_FILE to: {cert_path}")
        
        # Method 2: Update certificates
        print("📦 Updating certifi...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "certifi"], 
                      capture_output=True, check=True)
        print("✅ Certifi updated")
        
        # Method 3: Test SSL connection
        print("🧪 Testing SSL connection...")
        context = ssl.create_default_context()
        context.load_verify_locations(cert_path)
        
        import socket
        with socket.create_connection(("smtp.gmail.com", 465), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname="smtp.gmail.com") as ssock:
                print(f"✅ SSL connection to Gmail successful!")
                print(f"   SSL version: {ssock.version()}")
                print(f"   Cipher: {ssock.cipher()[0]}")
        
        print("=" * 50)
        print("🎉 SSL certificates fixed!")
        print("💡 You can now run: python gmail_email.py --to your@email.com")
        return True
        
    except Exception as e:
        print(f"❌ Certificate fix failed: {e}")
        print("💡 Try running: /Applications/Python\\ 3.13/Install\\ Certificates.command")
        return False

if __name__ == "__main__":
    fix_certificates()