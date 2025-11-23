#!/bin/bash

echo "==========================================="
echo "🧹 Hockey Music Controller - Cleanup"
echo "==========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "hockey_music_controller.py" ]; then
    echo "❌ Error: hockey_music_controller.py not found"
    echo "   Please run this script from the project root directory"
    exit 1
fi

echo "This will remove:"
echo "  • Virtual environment (hockey_venv/)"
echo "  • Build artifacts (build/, *.app)"
echo "  • Python cache (__pycache__/)"
echo "  • Backup files (*.backup*)"
echo "  • Testing directory"
echo "  • Temporary files"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "🗑️  Removing virtual environment..."
rm -rf hockey_venv/

echo "🗑️  Removing build artifacts..."
rm -rf build/
rm -rf "Hockey Music Controller.app"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "🗑️  Removing backup files..."
rm -f *.backup*
rm -rf testing/

echo "🗑️  Removing temporary files..."
rm -f structure.txt
rm -f check_spotify_credentials.py
rm -f spotify_start_time_finder.py
rm -f diagnose.sh

echo "🗑️  Cleaning docs directory..."
rm -f docs/hockey_music_controller.py

echo ""
echo "📝 Fixing .gitignore..."
if [ -f "gitignore" ]; then
    mv gitignore .gitignore
    echo "   ✅ Renamed gitignore → .gitignore"
fi

if [ ! -f ".gitignore" ]; then
    echo "   ⚠️  Warning: .gitignore not found!"
    echo "   Download .gitignore from the release preparation package"
fi

echo ""
echo "==========================================="
echo "✅ Cleanup complete!"
echo "==========================================="
echo ""

# Show what's left
echo "📊 Remaining files:"
echo ""
find . -maxdepth 1 -type f | sort

echo ""
echo "📁 Remaining directories:"
echo ""
find . -maxdepth 1 -type d ! -path . ! -path "*/\.*" | sort

echo ""
echo "📦 Project size:"
du -sh .

echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Add files: git add ."
echo "3. Commit: git commit -m 'v2.1 - Roster Integration + Cleanup'"
echo "4. Push: git push origin main"
echo ""
