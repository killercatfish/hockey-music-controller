#!/bin/bash
# Create a native macOS .app bundle (no PyInstaller needed!)

echo "🏒 Creating Hockey Music Controller.app..."
echo ""

APP_NAME="Hockey Music Controller"
APP_DIR="${APP_NAME}.app/Contents"

# Clean previous build
rm -rf "${APP_NAME}.app"

# Create app bundle structure
echo "📁 Creating app bundle structure..."
mkdir -p "${APP_DIR}/MacOS"
mkdir -p "${APP_DIR}/Resources"

# Create launcher script
echo "📝 Creating launcher..."
cat > "${APP_DIR}/MacOS/launch" << 'EOF'
#!/bin/bash
# Launcher for Hockey Music Controller

# Get the Resources directory where the Python script lives
SCRIPT_DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is required but not installed.\n\nPlease install Python 3 from python.org" buttons {"Open Website", "Cancel"} default button "Open Website"' -e 'if button returned of result is "Open Website" then open location "https://www.python.org/downloads/"'
    exit 1
fi

# Check if required packages are installed, install if needed
python3 -c "import tkinter, hume, dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    # Show progress dialog while installing
    osascript -e 'display dialog "Installing required packages...\n\nThis only happens on first run." buttons {"OK"} default button "OK" giving up after 3'
    python3 -m pip install --user hume python-dotenv 2>&1 | grep -v "Requirement already satisfied"
fi

# Run the Python script
python3 hockey_music_controller.py

# If there was an error, show it
if [ $? -ne 0 ]; then
    osascript -e 'display dialog "The app encountered an error.\n\nPlease check the Console app for details." buttons {"OK"} default button "OK" with icon stop'
fi
EOF

chmod +x "${APP_DIR}/MacOS/launch"

# Copy Python script
echo "📋 Copying Python script..."
cp hockey_music_controller.py "${APP_DIR}/Resources/"

# Create Info.plist
echo "⚙️  Creating Info.plist..."
cat > "${APP_DIR}/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIdentifier</key>
    <string>com.killercatfish.hockeymusiccontroller</string>
    <key>CFBundleName</key>
    <string>Hockey Music Controller</string>
    <key>CFBundleDisplayName</key>
    <string>Hockey Music Controller</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo ""
echo "✅ Created ${APP_NAME}.app"
echo ""
echo "🚀 To test:"
echo "   open '${APP_NAME}.app'"
echo ""
echo "📤 To distribute:"
echo "   zip -r '${APP_NAME}.zip' '${APP_NAME}.app'"
echo ""
echo "💡 This app requires Python 3 to be installed on the user's Mac"
echo ""
