#!/bin/bash
# Hockey Music Controller - Project Cleanup Script
# This script organizes the project structure and removes unnecessary files

echo "=========================================="
echo "Hockey Music Controller - Project Cleanup"
echo "=========================================="
echo ""

# Get the project root directory
PROJECT_ROOT="$(pwd)"

echo "Cleaning up project in: $PROJECT_ROOT"
echo ""

# Create docs directory if it doesn't exist
if [ ! -d "docs" ]; then
    echo "Creating docs/ directory..."
    mkdir -p docs
fi

# Move documentation files to docs/
echo "Organizing documentation..."
if [ -f "HUME_VOICE_SETUP.md" ]; then
    mv HUME_VOICE_SETUP.md docs/ 2>/dev/null
fi
if [ -f "FINAL_SCORE_FEATURE_GUIDE.md" ]; then
    mv FINAL_SCORE_FEATURE_GUIDE.md docs/ 2>/dev/null
fi
if [ -f "FINAL_SCORE_QUICK_START.md" ]; then
    mv FINAL_SCORE_QUICK_START.md docs/ 2>/dev/null
fi

# Remove backup files
echo "Removing backup files..."
rm -f *.backup
rm -f *.bak
rm -f *_backup.py
rm -f hockey_music_controller.py.backup

# Remove generated/enhanced versions (keep only the main file)
echo "Removing generated files..."
rm -f hockey_music_controller_enhanced.py
rm -f hockey_music_controller_patched.py
rm -f add_final_score_feature.py

# Keep the v2 patch script
if [ -f "add_final_score_feature_v2.py" ]; then
    echo "✓ Keeping add_final_score_feature_v2.py"
fi

# Remove Python cache
echo "Removing Python cache..."
rm -rf __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null

# Remove macOS files
echo "Removing macOS system files..."
find . -name ".DS_Store" -delete 2>/dev/null
find . -name "._*" -delete 2>/dev/null

# Ensure .env is not tracked (but keep .env.example)
if [ -f ".env" ]; then
    echo "✓ .env file exists (will be ignored by git)"
fi

# List what's left
echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Project structure:"
ls -lh | grep -v "^total"
echo ""
if [ -d "docs" ]; then
    echo "Documentation:"
    ls -lh docs/ | grep -v "^total"
    echo ""
fi

echo "Ready for git!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Add files: git add ."
echo "  3. Commit: git commit -m 'Clean up project structure'"
echo "  4. Push: git push origin main"
echo ""
