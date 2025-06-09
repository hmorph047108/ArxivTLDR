#!/bin/bash

# macOS LaunchAgent Setup for Weekly ArXiv Digest
echo "🚀 Setting up macOS LaunchAgent for Weekly ArXiv Digest"
echo "====================================================="

# Create LaunchAgents directory if it doesn't exist
LAUNCH_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_DIR"

# Create the launch agent plist file
PLIST_FILE="$LAUNCH_DIR/com.arxiv.digest.weekly.plist"

cat > "$PLIST_FILE" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.arxiv.digest.weekly</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/harrymorphakis/Desktop/ArxivTLDR/daily_digest.py</string>
        <string>--config</string>
        <string>weekly_config.json</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/harrymorphakis/Desktop/ArxivTLDR</string>
    <key>StandardOutPath</key>
    <string>/Users/harrymorphakis/Desktop/ArxivTLDR/weekly_digest.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/harrymorphakis/Desktop/ArxivTLDR/weekly_digest_error.log</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "📝 Created launch agent: $PLIST_FILE"

# Load the launch agent
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Launch agent loaded successfully!"
    echo ""
    echo "📧 Weekly digest will run every Monday at 8:00 AM"
    echo "📝 Logs: weekly_digest.log"
    echo "❌ Errors: weekly_digest_error.log"
    echo ""
    echo "🔧 Management commands:"
    echo "• Check status: launchctl list | grep com.arxiv.digest"
    echo "• Unload: launchctl unload ~/Library/LaunchAgents/com.arxiv.digest.weekly.plist"
    echo "• Test now: launchctl start com.arxiv.digest.weekly"
else
    echo "❌ Failed to load launch agent"
    echo "💡 You may need to grant Terminal full disk access in System Preferences > Security & Privacy"
fi

# Test the configuration
echo ""
echo "🧪 Testing configuration..."
python3 daily_digest.py --config weekly_config.json --dry-run 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Configuration test passed"
else
    echo "⚠️ Configuration test failed - check your .env file"
fi