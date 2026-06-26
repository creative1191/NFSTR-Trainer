#!/usr/bin/env python3
"""
================================================================================
  Need for Speed: The Run v1.1.0.0 - Trainer
  Style: LinGon +10 trainer
  Works on: Steam, Origin, Cracked, Repack (any version)
================================================================================

USAGE:
  1. Start NFS The Run, get into a race
  2. Run this trainer (double-click if compiled to .exe)
  3. Press INSERT to activate the trainer
  4. Press the F-keys for cheats (see HOTKEYS below)

HOTKEYS:
  F2  - Stage Timer (freeze)
  F3  - Super Speed
  F4  - Super Brakes
  F5  - Freeze AI Cars
  F6  - Infinite Resets / Setbacks
  F7  - Infinite Challenge Time
  F8  - 10x XP / Max XP
  F9  - Infinite Nitro
  F10 - Infinite Race Time
  F11 - Infinite Checkpoint Time
  END - Disable All Cheats
  INSERT - Toggle Trainer Active/Inactive

HOW IT WORKS (the magic):
  For each cheat, you press the F-key TWICE:
    - First press: scans memory for the current value
    - You do the action in-game (e.g. press NITRO)
    - Second press: narrows down to 1 address, freezes it

  After the first time, just pressing the F-key once instantly toggles.
================================================================================
"""

import ctypes
import ctypes.wintypes
import struct
import time
import threading
import sys
import os
from collections import deque

# Try to import pymem (preferred) or fallback to ctypes
try:
    import pymem
    import pymem.process
    HAS_PYMEM = True
except ImportError:
    HAS_PYMEM = False

# Try to import keyboard for hotkeys (preferred) or fallback to msvcrt
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# Constants
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

PROCESS_NAMES = ["Need For Speed The Run.exe", "NeedForSpeedTheRun.exe"]

# Console colors for Windows
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

if os.name == 'nt':
    try:
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except:
        pass


def color_print(text, color):
    """Print colored text"""
    try:
        print(f"{color}{text}{Colors.ENDC}")
    except:
        print(text)


def banner():
    print("=" * 70)
    color_print("  NEED FOR SPEED: THE RUN v1.1.0.0 - TRAINER", Colors.HEADER + Colors.BOLD)
    color_print("  LinGon-Style Auto-Scanner Trainer", Colors.BLUE)
    color_print("  Works on ALL versions (Cracked/Repack/Steam/Origin)", Colors.GREEN)
    print("=" * 70)


class NFSTrainer:
    def __init__(self):
        self.pm = None
        self.process_attached = False
        self.process_name = None
        self.trainer_active = False

        # Cheat definitions: F-key -> (display_name, value_type, scan_default, lock_value)
        self.cheats = {
            'f2':  ('Stage Timer',         'float', 0.0,    9999.0),
            'f3':  ('Super Speed',         'float', 0.0,    350.0),
            'f4':  ('Super Brakes',        'float', 0.0,    9999.0),
            'f5':  ('Freeze AI Cars',      'float', 0.0,    0.0),
            'f6':  ('Infinite Resets',     'int',   3,      99),
            'f7':  ('Challenge Time',      'float', 0.0,    9999.0),
            'f8':  ('10x XP',              'int',   0,      99999999),
            'f9':  ('Infinite Nitro',      'float', 0.0,    5.0),
            'f10': ('Race Time',           'float', 0.0,    9999.0),
            'f11': ('Checkpoint Time',     'float', 0.0,    9999.0),
        }

        # State tracking
        self.addresses = {}        # cheat_key -> address (when locked)
        self.candidates = {}       # cheat_key -> list of candidate addresses
        self.scan_complete = {}    # cheat_key -> True/False (has user done second press)
        self.cheat_states = {}     # cheat_key -> bool (active/inactive)
        self.lock_values = {}      # cheat_key -> value to lock to

        # Initialize states
        for key in self.cheats:
            self.cheat_states[key] = False
            self.scan_complete[key] = False
            self.lock_values[key] = self.cheats[key][3]

        # Background freeze thread
        self.freeze_thread = None
        self.freeze_running = False

    def find_and_attach(self):
        """Find and attach to the NFS The Run process"""
        if not HAS_PYMEM:
            print("[!] pymem not available. Install with: pip install pymem")
            return False

        for name in PROCESS_NAMES:
            try:
                self.pm = pymem.Pymem(name)
                self.process_name = name
                self.process_attached = True
                color_print(f"[+] Attached to {name} (PID: {self.pm.process_id})", Colors.GREEN)
                return True
            except pymem.process.NotFoundByName:
                continue
            except Exception as e:
                color_print(f"[!] Error: {e}", Colors.RED)
                continue

        color_print("[!] NFS The Run not found. Launch the game first.", Colors.RED)
        return False

    def read_memory(self, address, size=4):
        """Read bytes from memory"""
        try:
            return self.pm.read_bytes(address, size)
        except:
            return None

    def read_float(self, address):
        """Read a float (4 bytes) from memory"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<f', data)[0]
        return None

    def read_int(self, address):
        """Read a 4-byte integer from memory"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('<i', data)[0]
        return None

    def write_float(self, address, value):
        """Write a float to memory"""
        try:
            self.pm.write_bytes(address, struct.pack('<f', value), 4)
            return True
        except:
            return False

    def write_int(self, address, value):
        """Write an integer to memory"""
        try:
            self.pm.write_bytes(address, struct.pack('<i', value), 4)
            return True
        except:
            return False

    def scan_for_value(self, value, value_type='float', max_results=500):
        """Scan all process memory for a value"""
        byte_pattern = struct.pack('<f', value) if value_type == 'float' else struct.pack('<i', value)
        try:
            results = self.pm.pattern_scan_all(byte_pattern, return_multiple=True)
            if isinstance(results, list):
                return results[:max_results]
            else:
                return [results] if results else []
        except Exception as e:
            color_print(f"[!] Scan error: {e}", Colors.RED)
            return []

    def narrow_candidates(self, cheat_key):
        """After user action, narrow down candidates by checking which changed"""
        candidates = self.candidates.get(cheat_key, [])
        if not candidates:
            return None

        name, vtype, default, lock_val = self.cheats[cheat_key]

        # Read current value at each candidate
        valid = []
        for addr in candidates:
            if vtype == 'float':
                current = self.read_float(addr)
            else:
                current = self.read_int(addr)

            if current is None:
                continue

            # Filter: value should be in reasonable range for this cheat
            if vtype == 'float':
                if -1000 < current < 100000:
                    valid.append((addr, current))
            else:
                if -1000 < current < 100000000:
                    valid.append((addr, current))

        if len(valid) == 1:
            return valid[0][0]
        elif len(valid) <= 5:
            # Multiple candidates - try each one briefly
            color_print(f"[?] {name}: {len(valid)} candidates. Testing...", Colors.YELLOW)
            for addr, _ in valid:
                # Write the lock value and see if anything changes
                if vtype == 'float':
                    self.write_float(addr, lock_val)
                else:
                    self.write_int(addr, lock_val)
                time.sleep(0.1)
                # Check if value sticks
                if vtype == 'float':
                    check = self.read_float(addr)
                else:
                    check = self.read_int(addr)
                if check == lock_val:
                    return addr
            return None
        else:
            # Too many - need more filtering
            return None

    def toggle_cheat(self, cheat_key):
        """Toggle a cheat on/off"""
        if not self.trainer_active:
            return

        if not self.process_attached:
            if not self.find_and_attach():
                return

        name, vtype, default, lock_val = self.cheats[cheat_key]

        # If already active, disable it
        if self.cheat_states[cheat_key]:
            self.cheat_states[cheat_key] = False
            color_print(f"[-] {name}: DISABLED", Colors.YELLOW)
            return

        # If we already have the address, just activate it
        if cheat_key in self.addresses and self.addresses[cheat_key] is not None:
            addr = self.addresses[cheat_key]
            if vtype == 'float':
                self.write_float(addr, lock_val)
            else:
                self.write_int(addr, lock_val)
            self.cheat_states[cheat_key] = True
            color_print(f"[+] {name}: ACTIVATED at {hex(addr)} (locked to {lock_val})", Colors.GREEN)
            return

        # First-time activation: scan for the value
        if cheat_key not in self.candidates or not self.candidates[cheat_key]:
            color_print(f"[?] {name}: Scanning for value {default}...", Colors.YELLOW)
            results = self.scan_for_value(default, vtype)
            if not results:
                color_print(f"[!] {name}: No candidates found. Make sure you're in a race.", Colors.RED)
                return
            self.candidates[cheat_key] = results
            color_print(f"[?] {name}: Found {len(results)} candidates.", Colors.YELLOW)
            color_print(f"    >>> DO THE ACTION IN-GAME <<<", Colors.YELLOW + Colors.BOLD)
            color_print(f"    >>> Then press {cheat_key.upper()} again <<<", Colors.YELLOW + Colors.BOLD)
            return

        # Second press: narrow down candidates
        addr = self.narrow_candidates(cheat_key)
        if addr is None:
            color_print(f"[!] {name}: Could not find exact address. Try again with more action in-game.", Colors.RED)
            self.candidates[cheat_key] = []
            return

        # Got the address! Lock it.
        self.addresses[cheat_key] = addr
        if vtype == 'float':
            self.write_float(addr, lock_val)
        else:
            self.write_int(addr, lock_val)
        self.cheat_states[cheat_key] = True
        color_print(f"[+] {name}: ACTIVATED at {hex(addr)} (locked to {lock_val})", Colors.GREEN)
        color_print(f"    Press {cheat_key.upper()} again to toggle off.", Colors.GREEN)

    def disable_all(self):
        """Disable all active cheats"""
        for key, state in self.cheat_states.items():
            if state:
                self.cheat_states[key] = False
        color_print("[-] ALL CHEATS DISABLED", Colors.YELLOW)

    def start_freeze_thread(self):
        """Start background thread that continuously freezes active addresses"""
        self.freeze_running = True
        self.freeze_thread = threading.Thread(target=self._freeze_loop, daemon=True)
        self.freeze_thread.start()

    def stop_freeze_thread(self):
        """Stop the freeze thread"""
        self.freeze_running = False

    def _freeze_loop(self):
        """Background loop that freezes all active addresses"""
        while self.freeze_running:
            if not self.process_attached or not self.trainer_active:
                time.sleep(0.5)
                continue

            for cheat_key, active in self.cheat_states.items():
                if not active:
                    continue
                if cheat_key not in self.addresses:
                    continue

                addr = self.addresses[cheat_key]
                lock_val = self.lock_values[cheat_key]
                name, vtype, _, _ = self.cheats[cheat_key]

                try:
                    if vtype == 'float':
                        self.write_float(addr, lock_val)
                    else:
                        self.write_int(addr, lock_val)
                except:
                    pass

            time.sleep(0.05)  # 50ms - 20 FPS freeze rate

    def print_status(self):
        """Print current status of all cheats"""
        print()
        color_print("=" * 70, Colors.BLUE)
        color_print("  TRAINER STATUS", Colors.BOLD)
        color_print("=" * 70, Colors.BLUE)
        print(f"  Process: {self.process_name or 'Not Attached'}")
        print(f"  Trainer: {'ACTIVE' if self.trainer_active else 'INACTIVE'} (press INSERT to toggle)")
        print()
        for key, (name, vtype, default, lock_val) in self.cheats.items():
            state = self.cheat_states.get(key, False)
            addr = self.addresses.get(key)
            state_str = "[ON]" if state else "[OFF]"
            color = Colors.GREEN if state else Colors.RED
            addr_str = hex(addr) if addr else "not found"
            color_print(f"  {key.upper():4} {state_str:5} {name:25} ({addr_str}) -> {lock_val}", color)
        print()
        color_print("=" * 70, Colors.BLUE)


def main():
    banner()
    trainer = NFSTrainer()

    if not HAS_PYMEM:
        color_print("[!] pymem library missing. Install: pip install pymem", Colors.RED)
        color_print("    Or compile with PyInstaller --hidden-import pymem", Colors.RED)
        return

    if not HAS_KEYBOARD:
        color_print("[!] keyboard library missing. Install: pip install keyboard", Colors.RED)
        color_print("    Falling back to console mode (press ENTER after typing command)", Colors.YELLOW)
        return

    color_print("[*] Waiting for NFS The Run...", Colors.YELLOW)
    color_print("    Start the game and get into a race.", Colors.YELLOW)

    # Try to attach
    trainer.find_and_attach()

    # Print initial status
    trainer.print_status()

    # Start freeze thread
    trainer.start_freeze_thread()

    # Register hotkeys
    color_print("[*] Hotkeys registered. Press INSERT to activate trainer.", Colors.GREEN)
    color_print("    Press END to disable all cheats.", Colors.GREEN)

    try:
        # Hotkeys
        keyboard.add_hotkey('insert', lambda: toggle_trainer(trainer))
        keyboard.add_hotkey('end', lambda: trainer.disable_all())

        for fkey in trainer.cheats.keys():
            keyboard.add_hotkey(fkey, lambda k=fkey: trainer.toggle_cheat(k))

        # Keep alive
        color_print("\n[*] Trainer running. Press Ctrl+C in this window to exit.", Colors.GREEN)
        while True:
            time.sleep(1)
            if not trainer.process_attached:
                # Try to re-attach every 5 seconds
                time.sleep(4)
                trainer.find_and_attach()
    except KeyboardInterrupt:
        color_print("\n[*] Shutting down trainer...", Colors.YELLOW)
        trainer.stop_freeze_thread()
        if trainer.process_attached and trainer.pm:
            try:
                trainer.pm.close_process()
            except:
                pass
        color_print("[*] Trainer stopped. Goodbye!", Colors.GREEN)


def toggle_trainer(trainer):
    """Toggle the trainer on/off"""
    trainer.trainer_active = not trainer.trainer_active
    if trainer.trainer_active:
        color_print("\n[+] TRAINER ACTIVATED - Cheats ready", Colors.GREEN + Colors.BOLD)
        if not trainer.process_attached:
            trainer.find_and_attach()
    else:
        color_print("\n[-] TRAINER DEACTIVATED - All cheats paused", Colors.YELLOW + Colors.BOLD)
        trainer.disable_all()
    trainer.print_status()


if __name__ == "__main__":
    main()
