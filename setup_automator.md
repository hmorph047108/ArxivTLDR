# macOS Automator Setup for Weekly ArXiv Digest

## Method 1: Create Automator App

1. **Open Automator** (Applications > Automator)

2. **Choose "Application"** when prompted for document type

3. **Add "Run Shell Script" action**:
   - Search for "Run Shell Script" in the left panel
   - Drag it to the workflow area
   - Set Shell to: `/bin/bash`
   - Set Pass input to: `as arguments`

4. **Add this script**:
```bash
#!/bin/bash
cd "/Users/harrymorphakis/Desktop/ArxivTLDR"

# Load environment from .env file
export $(cat .env | xargs)

# Run the weekly digest
python3 daily_digest.py --config weekly_config.json >> weekly_digest.log 2>&1

# Show notification when done
osascript -e 'display notification "Weekly ArXiv digest sent successfully!" with title "ArXiv Digest"'
```

5. **Save the app** as "WeeklyArXivDigest.app" to Applications folder

6. **Test it** by double-clicking the app

## Method 2: Calendar Automation

1. **Open Calendar app**

2. **Create new event**:
   - Title: "Weekly ArXiv Digest"
   - Repeat: Weekly (Mondays at 8 AM)
   - Alert: Custom > Open file > Select your WeeklyArXivDigest.app

## Method 3: Using launchd (Advanced)

Create a launch agent for more reliable scheduling:

```bash
# Run this command to create the launch agent
./setup_launchd.sh
```

## Testing

Test manually first:
```bash
cd /Users/harrymorphakis/Desktop/ArxivTLDR
python3 daily_digest.py --config weekly_config.json
```

Check logs:
```bash
tail -f weekly_digest.log
```