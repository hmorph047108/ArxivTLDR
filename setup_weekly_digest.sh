#!/bin/bash
"""
Weekly ArXiv Digest Setup Script
This script sets up automated weekly delivery of ArXiv digest emails.
"""

echo "🚀 Setting up Weekly ArXiv Digest Automation"
echo "=============================================="

# Get the current directory (where the script is located)
SCRIPT_DIR="/Users/harrymorphakis/Desktop/ArxivTLDR"
PYTHON_PATH=$(which python3)

echo "📁 Script directory: $SCRIPT_DIR"
echo "🐍 Python path: $PYTHON_PATH"

# Create the cron job command
CRON_COMMAND="0 8 * * 1 cd $SCRIPT_DIR && $PYTHON_PATH daily_digest.py --config weekly_config.json >> $SCRIPT_DIR/weekly_digest.log 2>&1"

echo ""
echo "📋 Cron job command:"
echo "$CRON_COMMAND"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "weekly_config.json"; then
    echo ""
    echo "⚠️  Weekly digest cron job already exists!"
    echo "Current crontab:"
    crontab -l | grep weekly_config.json
else
    echo ""
    echo "📅 Adding weekly cron job..."
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
    
    if [ $? -eq 0 ]; then
        echo "✅ Weekly digest cron job added successfully!"
        echo ""
        echo "📧 You will now receive weekly ArXiv digests every Monday at 8 AM"
        echo "📝 Logs will be saved to: $SCRIPT_DIR/weekly_digest.log"
    else
        echo "❌ Failed to add cron job"
        echo "💡 You can add it manually with: crontab -e"
    fi
fi

echo ""
echo "🔧 Current crontab entries:"
crontab -l

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Summary:"
echo "• Weekly digest configured for: harrymorphakis@gmail.com"
echo "• Delivery schedule: Every Monday at 8:00 AM"
echo "• Papers included: 15 from the last 7 days"
echo "• Categories: AI, ML, Computer Vision, NLP, Robotics"
echo "• Log file: weekly_digest.log"
echo ""
echo "💡 To test manually: python3 daily_digest.py --config weekly_config.json"
echo "💡 To view logs: tail -f weekly_digest.log"
echo "💡 To remove: crontab -e (and delete the line)"