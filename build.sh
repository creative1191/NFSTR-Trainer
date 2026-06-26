#!/bin/bash
# Build script for Linux/macOS
# Builds NFSTR_Trainer binary using PyInstaller

echo "============================================================"
echo "  NFS The Run Trainer - Building Binary"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found!"
    echo "Install: sudo apt install python3 python3-pip   (Debian/Ubuntu)"
    echo "         brew install python3                    (macOS)"
    exit 1
fi

echo "[OK] Python found:"
python3 --version
echo ""

# Install dependencies
echo "[*] Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller
echo "[OK] Dependencies installed."
echo ""

# Build
echo "[*] Building NFSTR_Trainer..."
pyinstaller --onefile --console \
    --name "NFSTR_Trainer" \
    --hidden-import pymem \
    --hidden-import pymem.process \
    --hidden-import pymem.pattern \
    --collect-all pymem \
    --collect-all keyboard \
    nfs_trainer.py

if [ -f "dist/NFSTR_Trainer" ] || [ -f "dist/NFSTR_Trainer.exe" ]; then
    echo ""
    echo "============================================================"
    echo "  SUCCESS!"
    echo "  Binary ready in: dist/"
    echo "============================================================"
else
    echo ""
    echo "[ERROR] Build failed."
    exit 1
fi
