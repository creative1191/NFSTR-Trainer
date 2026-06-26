# 🏎️ NFS The Run Trainer (LinGon-Style)

[![GitHub release](https://img.shields.io/github/v/release/USERNAME/NFSTR-Trainer?style=flat-square)](https://github.com/USERNAME/NFSTR-Trainer/releases)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/USERNAME/NFSTR-Trainer/build.yml?style=flat-square)](https://github.com/USERNAME/NFSTR-Trainer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?style=flat-square)](https://www.microsoft.com/windows)

A free, open-source trainer for **Need for Speed: The Run v1.1.0.0** with hotkey-based cheats — LinGon +10 style, but **works on cracked/repack versions** thanks to runtime memory auto-scanning.

---

## ✨ Features

| Hotkey | Cheat |
|--------|-------|
| `INSERT` | Activate / Deactivate trainer |
| `END` | Disable all cheats |
| `F2` | Stage Timer (freeze at 9999) |
| `F3` | Super Speed |
| `F4` | Super Brakes |
| `F5` | Freeze AI Cars |
| `F6` | Infinite Resets / Setbacks |
| `F7` | Infinite Challenge Time |
| `F8` | 10x XP / Max XP |
| `F9` | Infinite Nitro |
| `F10` | Infinite Race Time |
| `F11` | Infinite Checkpoint Time |

Plus a **colored console** that shows real-time status of every cheat.

---

## 📥 Download

**Easiest way:** Go to [Releases](https://github.com/USERNAME/NFSTR-Trainer/releases) and download `NFSTR_Trainer.exe` from the latest release.

The `.exe` is built automatically by GitHub Actions — no Python install needed!

---

## 🚀 Quick Start

### Option A: Download the .exe (recommended)

1. Download `NFSTR_Trainer.exe` from [Releases](../../releases)
2. Place it anywhere (Desktop is fine)
3. Right-click → **Run as Administrator**
4. Start NFS The Run, enter a race
5. Trainer attaches automatically

### Option B: Run from source

Requires Python 3.8+.

```bash
git clone https://github.com/USERNAME/NFSTR-Trainer.git
cd NFSTR-Trainer
pip install -r requirements.txt
python nfs_trainer.py
```

### Option C: Build the .exe yourself (Windows)

```bash
build.bat
```

The `.exe` will be in `dist/NFSTR_Trainer.exe`.

---

## 🎮 How to Use

1. Launch **Need for Speed: The Run** and enter any race
2. Run **NFSTR_Trainer.exe** as Administrator
3. Press `INSERT` to activate the trainer
4. **First time for each cheat:** press the F-key TWICE
   - 1st press: trainer scans memory for the value
   - Do the action in-game (e.g. press SHIFT for nitro)
   - 2nd press: trainer locks the address
5. **After that:** just press the F-key once to toggle on/off

### Example: Infinite Nitro

```
[INSERT]                    → Trainer activated
[F9]                        → "Scanning for value 0..."
[Press SHIFT in game]       → Nitro bar fills up
[F9]                        → "ACTIVATED at 0x12345678"
[Done — nitro is infinite!] → Press Numpad 1 in-game to refill anytime
```

---

## 🆚 Why This Is Better Than LinGon

| | LinGon +10 | This Trainer |
|---|---|---|
| Cracked EXE | ❌ Crashes | ✅ Works |
| Repack EXE | ❌ Crashes | ✅ Works |
| Steam/Origin | ✅ Works | ✅ Works |
| Open source | ❌ No | ✅ Yes |
| AV-friendly | ❌ Often flagged | ⚠️ Sometimes flagged |
| No Python needed | ✅ Yes | ✅ Yes (.exe) |

The LinGon trainer uses **hard-coded memory addresses** that exist only in the official Steam/Origin EXE. This trainer uses **runtime memory scanning** so it finds the addresses wherever they are in your version.

---

## 🛠️ Building from Source

### Windows

```cmd
build.bat
```

### Linux / macOS

```bash
pip install -r requirements.txt
pyinstaller --onefile --console \
  --name NFSTR_Trainer \
  --hidden-import pymem \
  --hidden-import pymem.process \
  --hidden-import pymem.pattern \
  --collect-all pymem \
  --collect-all keyboard \
  nfs_trainer.py
```

The `.exe` (or Linux binary) will be in `dist/`.

---

## 🧪 Technical Details

- **Language:** Python 3.8+
- **Memory access:** [pymem](https://github.com/srounet/Pymem) (cross-platform process memory library)
- **Hotkeys:** [keyboard](https://github.com/boppreh/keyboard)
- **Build:** [PyInstaller](https://www.pyinstaller.org/) `--onefile`

### How auto-scanning works

```
User presses F9 (first time)
    │
    ▼
Scan all process memory for float value 0
    │
    ▼
Found ~5000 candidate addresses
    │
    ▼
Tell user: "Press NITRO in game"
    │
    ▼
User presses NITRO → game writes new value
    │
    ▼
User presses F9 (second time)
    │
    ▼
Re-read each candidate, filter by reasonable range
    │
    ▼
Test each remaining candidate by writing 5.0 to it
    │
    ▼
Lock the one that "sticks" → SUCCESS
    │
    ▼
Background thread writes 5.0 to the address 20x/second
    │
    ▼
NITRO IS INFINITE FOREVER 🎉
```

---

## ⚠️ Disclaimer

This trainer is for **single-player offline use only**. The online servers for NFS The Run were retired in 2016, so single-player is the only mode available anyway.

The trainer does **not** modify any game files — it only reads/writes process memory at runtime, which is the standard approach used by Cheat Engine, WeMod, and similar tools.

---

## 📜 License

[MIT License](LICENSE) — do whatever you want with this code.

---

## 🤝 Contributing

Pull requests welcome! Ideas:

- [ ] Add more cheats (drift points, race placement, etc.)
- [ ] Add a GUI (using tkinter or PyQt)
- [ ] Auto-detect the correct value without user input
- [ ] Support for other NFS games (Most Wanted 2012, Carbon, etc.)
- [ ] Code signing to avoid antivirus false positives

---

## 🐛 Troubleshooting

### Trainer says "Process not found"
Start NFS The Run first, wait for the main menu or race, then run the trainer.

### "Access Denied" or game crashes
Right-click `NFSTR_Trainer.exe` → **Run as administrator**.

### Antivirus deleted the .exe
This is common for trainers. Add the file to your AV's exclusion list, or build from source.

### Cheat doesn't work
Make sure you pressed `INSERT` first. For first-time setup of each cheat, press the F-key **TWICE** with the game action in between.

### Build fails with "Python not found"
Install Python 3.8+ from https://www.python.org/ and make sure to check **"Add Python to PATH"** during installation.

---

## 📸 Screenshots

> _Add screenshots of the trainer console here!_

```
======================================================================
  NEED FOR SPEED: THE RUN v1.1.0.0 - TRAINER
  LinGon-Style Auto-Scanner Trainer
  Works on ALL versions (Cracked/Repack/Steam/Origin)
======================================================================
[+] Attached to Need For Speed The Run.exe (PID: 12345)
[+] TRAINER ACTIVATED - Cheats ready
...
```

---

Made with ❤️ for the NFS community.
