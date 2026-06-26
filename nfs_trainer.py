#!/usr/bin/env python3
"""
================================================================================
  NFS The Run v1.1.0.0 - Trainer v2.0 (FIXED)
  Style: LinGon +10 trainer
  Works on: Steam, Origin, Cracked, Repack (any version)

  v2.0 Improvements:
    - Better value-change detection (compares addresses before/after action)
    - Manual value input fallback (works when auto-detection fails)
    - Shows exact addresses being tested
    - Prints progress during narrowing
    - Lower memory scan threshold (more candidates initially)
================================================================================
"""

import ctypes
import ctypes.wintypes
import struct
import time
import threading
import sys
import os

# Try to import pymem (preferred) or fallback to ctypes
try:
    import pymem
    import pymem.process
    HAS_PYMEM = True
except ImportError:
    HAS_PYMEM = False

# Try to import keyboard for hotkeys
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# Constants
PROCESS_NAMES = ["Need For Speed The Run.exe", "NeedForSpeedTheRun.exe"]

# Console colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'

if os.name == 'nt':
    try:
        ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def color_print(text, color):
    """Print colored text"""
    try:
        print(f"{color}{text}{Colors.ENDC}")
    except Exception:
        print(text)


def banner():
    print("=" * 70)
    color_print("  NFS THE RUN v1.1.0.0 - TRAINER v2.0 (FIXED)", Colors.HEADER + Colors.BOLD)
    color_print("  LinGon-Style Auto-Scanner Trainer", Colors.BLUE)
    color_print("  Works on ALL versions (Cracked/Repack/Steam/Origin)", Colors.GREEN)
    print("=" * 70)


class NFSTrainer:
    def __init__(self):
        self.pm = None
        self.process_attached = False
        self.process_name = None
        self.trainer_active = False

        # Cheat definitions: F-key -> (display_name, value_type, scan_default, lock_value, max_value)
        self.cheats = {
            'f2':  ('Stage Timer',         'float', 0.0,    9999.0,   9999.0),
            'f3':  ('Super Speed',         'float', 0.0,    350.0,    500.0),
            'f4':  ('Super Brakes',        'float', 0.0,    9999.0,   9999.0),
            'f5':  ('Freeze AI Cars',      'float', 0.0,    0.0,      100.0),
            'f6':  ('Infinite Resets',     'int',   3,      99,       99),
            'f7':  ('Challenge Time',      'float', 0.0,    9999.0,   9999.0),
            'f8':  ('10x XP',              'int',   0,      99999999, 99999999),
            'f9':  ('Infinite Nitro',      'float', 0.0,    5.0,      5.0),
            'f10': ('Race Time',           'float', 0.0,    9999.0,   9999.0),
            'f11': ('Checkpoint Time',     'float', 0.0,    9999.0,   9999.0),
        }

        # State tracking
        self.addresses = {}
        self.first_scan_addresses = {}
        self.cheat_states = {}

        # Initialize states
        for key in self.cheats:
            self.cheat_states[key] = False

        # Background freeze thread
        self.freeze_running = False

    def find_and_attach(self):
        if not HAS_PYMEM:
            color_print("[!] pymem not available. Install with: pip install pymem", Colors.RED)
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

    def read_float(self, address):
        try:
            return self.pm.read_float(address)
        except Exception:
            return None

    def read_int(self, address):
        try:
            return self.pm.read_int(address)
        except Exception:
            return None

    def write_float(self, address, value):
        try:
            self.pm.write_float(address, value)
            return True
        except Exception:
            return False

    def write_int(self, address, value):
        try:
            self.pm.write_int(address, value)
            return True
        except Exception:
            return False

    def scan_for_value(self, value, value_type='float', max_results=5000):
        """Scan all process memory for a value, return list of addresses"""
        byte_pattern = struct.pack('<f', value) if value_type == 'float' else struct.pack('<i', value)
        try:
            results = self.pm.pattern_scan_all(byte_pattern, return_multiple=True)
            if isinstance(results, list):
                return results[:max_results]
            elif results:
                return [results]
            else:
                return []
        except Exception as e:
            color_print(f"[!] Scan error: {e}", Colors.RED)
            return []

    def toggle_cheat(self, cheat_key):
        if not self.trainer_active:
            return

        if not self.process_attached:
            if not self.find_and_attach():
                return

        name, vtype, default, lock_val, max_val = self.cheats[cheat_key]

        # If already active, disable
        if self.cheat_states.get(cheat_key, False):
            self.cheat_states[cheat_key] = False
            color_print(f"[-] {name}: DISABLED", Colors.YELLOW)
            return

        # If we already have the address, just activate
        if cheat_key in self.addresses and self.addresses[cheat_key] is not None:
            addr = self.addresses[cheat_key]
            if vtype == 'float':
                self.write_float(addr, lock_val)
            else:
                self.write_int(addr, lock_val)
            self.cheat_states[cheat_key] = True
            color_print(f"[+] {name}: ACTIVATED at {hex(addr)} (locked to {lock_val})", Colors.GREEN)
            return

        # First scan if not done
        if cheat_key not in self.first_scan_addresses:
            color_print(f"[?] {name}: First scan for value {default}...", Colors.CYAN)
            results = self.scan_for_value(default, vtype, max_results=5000)
            if not results:
                color_print(f"[!] {name}: NO candidates found. Make sure you're in a race!", Colors.RED)
                return
            self.first_scan_addresses[cheat_key] = results
            color_print(f"[?] {name}: Found {len(results)} addresses with value {default}", Colors.CYAN)
            color_print(f"    >>> DO THE ACTION IN-GAME NOW <<<", Colors.YELLOW + Colors.BOLD)
            color_print(f"    >>> Then press {cheat_key.upper()} again <<<", Colors.YELLOW + Colors.BOLD)
            if name == 'Infinite Nitro':
                color_print(f"    (Press SHIFT in-game for nitro)", Colors.GRAY)
            return

        # Second press - narrow down using CHANGE detection
        first_addrs = set(self.first_scan_addresses.get(cheat_key, []))
        color_print(f"[?] {name}: Re-scanning current addresses (this finds ones that CHANGED)...", Colors.CYAN)

        # Read current value at each first-scan address
        changed = []
        unchanged = 0
        for i, addr in enumerate(self.first_scan_addresses[cheat_key]):
            if vtype == 'float':
                current = self.read_float(addr)
            else:
                current = self.read_int(addr)

            if current is None:
                continue

            # Did it change from the default value?
            if vtype == 'float':
                if abs(current - default) > 0.001:
                    changed.append((addr, current))
            else:
                if current != default:
                    changed.append((addr, current))
            else:
                unchanged += 1

        color_print(f"[?] {name}: {len(changed)} addresses CHANGED, {unchanged} unchanged", Colors.CYAN)

        if not changed:
            color_print(f"[!] {name}: Nothing changed! You didn't do the action in-game?", Colors.RED)
            color_print(f"    OR the value at those addresses is stored differently.", Colors.RED)
            color_print(f"    Press {cheat_key.upper()} once more to RETRY first scan.", Colors.YELLOW)
            self.first_scan_addresses.pop(cheat_key, None)
            return

        # Filter changed addresses by reasonable range for this cheat
        # For nitro: 0 < value < 6
        # For timers: 0 < value < 9999
        # For setbacks: 0 <= value <= 99
        # For XP: 0 <= value < 99999999
        valid = []
        for addr, val in changed:
            if vtype == 'float':
                if 0.0 < val <= max_val:
                    valid.append((addr, val))
            else:
                if 0 <= val <= max_val:
                    valid.append((addr, val))

        color_print(f"[?] {name}: {len(valid)} candidates in valid range", Colors.CYAN)

        if len(valid) == 1:
            addr, val = valid[0]
            self.addresses[cheat_key] = addr
            if vtype == 'float':
                self.write_float(addr, lock_val)
            else:
                self.write_int(addr, lock_val)
            self.cheat_states[cheat_key] = True
            color_print(f"[+] {name}: LOCKED at {hex(addr)} (value was {val}, now {lock_val})", Colors.GREEN + Colors.BOLD)
            color_print(f"    Press {cheat_key.upper()} to toggle off.", Colors.GREEN)
            return

        if len(valid) <= 10:
            color_print(f"[?] {name}: Testing each of {len(valid)} candidates...", Colors.YELLOW)
            for addr, val in valid:
                color_print(f"    Testing {hex(addr)} (current={val})...", Colors.GRAY)
                if vtype == 'float':
                    self.write_float(addr, lock_val)
                else:
                    self.write_int(addr, lock_val)
                time.sleep(0.15)
                # Check if value sticks (write again and read back)
                if vtype == 'float':
                    self.write_float(addr, lock_val)
                    check = self.read_float(addr)
                else:
                    self.write_int(addr, lock_val)
                    check = self.read_int(addr)

                if check is not None and abs(check - lock_val) < 0.01:
                    self.addresses[cheat_key] = addr
                    self.cheat_states[cheat_key] = True
                    color_print(f"[+] {name}: LOCKED at {hex(addr)} (current={val})", Colors.GREEN + Colors.BOLD)
                    return

            color_print(f"[!] {name}: No candidate responded to write. Try again.", Colors.RED)
            self.first_scan_addresses.pop(cheat_key, None)
            return

        # Too many candidates - ask user for manual help
        color_print(f"[!] {name}: {len(valid)} candidates found - too many to test blindly.", Colors.RED)
        color_print(f"", Colors.ENDC)
        color_print(f"    MANUAL FIX:", Colors.CYAN + Colors.BOLD)
        color_print(f"    1. Do the action in-game AGAIN (nitro/whatever)", Colors.CYAN)
        color_print(f"    2. Look at the VALUE that appears", Colors.CYAN)
        color_print(f"    3. Press {cheat_key.upper()} a 3rd time, then type the value you saw", Colors.CYAN)
        self.first_scan_addresses[cheat_key] = valid  # Store valid ones for next pass
        self.cheat_states['_manual_pending'] = cheat_key

    def manual_scan(self, cheat_key, new_value):
        """Third press - user typed the value they saw"""
        if cheat_key not in self.first_scan_addresses:
            return

        name, vtype, default, lock_val, max_val = self.cheats[cheat_key]
        candidates = self.first_scan_addresses[cheat_key]

        if not isinstance(candidates, list) or not candidates:
            return

        # candidates might be [(addr, val), ...] or [addr, ...]
        if isinstance(candidates[0], tuple):
            addresses = [c[0] for c in candidates]
        else:
            addresses = candidates

        color_print(f"[?] {name}: Looking for value {new_value} among {len(addresses)} candidates...", Colors.CYAN)

        matches = []
        for addr in addresses:
            if vtype == 'float':
                current = self.read_float(addr)
            else:
                current = self.read_int(addr)
            if current is not None and abs(current - float(new_value)) < 0.01:
                matches.append(addr)

        if len(matches) == 1:
            addr = matches[0]
            self.addresses[cheat_key] = addr
            if vtype == 'float':
                self.write_float(addr, lock_val)
            else:
                self.write_int(addr, lock_val)
            self.cheat_states[cheat_key] = True
            color_print(f"[+] {name}: LOCKED at {hex(addr)} (value={new_value}, now {lock_val})", Colors.GREEN + Colors.BOLD)
        elif len(matches) > 1:
            color_print(f"[!] {name}: {len(matches)} addresses match value {new_value}. Still ambiguous.", Colors.RED)
            color_print(f"    Try with a more specific value.", Colors.RED)
            for m in matches[:5]:
                color_print(f"    - {hex(m)}", Colors.GRAY)
        else:
            color_print(f"[!] {name}: No addresses match value {new_value}. Wrong value typed?", Colors.RED)

    def disable_all(self):
        for key in list(self.cheat_states.keys()):
            if key != '_manual_pending':
                self.cheat_states[key] = False
        color_print("[-] ALL CHEATS DISABLED", Colors.YELLOW)

    def start_freeze_thread(self):
        self.freeze_running = True
        self.freeze_thread = threading.Thread(target=self._freeze_loop, daemon=True)
        self.freeze_thread.start()

    def stop_freeze_thread(self):
        self.freeze_running = False

    def _freeze_loop(self):
        while self.freeze_running:
            if not self.process_attached or not self.trainer_active:
                time.sleep(0.5)
                continue

            for cheat_key, active in self.cheat_states.items():
                if not active or cheat_key == '_manual_pending':
                    continue
                if cheat_key not in self.addresses:
                    continue

                addr = self.addresses[cheat_key]
                lock_val = self.cheats[cheat_key][3]
                vtype = self.cheats[cheat_key][1]

                try:
                    if vtype == 'float':
                        self.write_float(addr, lock_val)
                    else:
                        self.write_int(addr, lock_val)
                except Exception:
                    pass

            time.sleep(0.05)

    def print_status(self):
        print()
        color_print("=" * 70, Colors.BLUE)
        color_print("  TRAINER STATUS v2.0", Colors.BOLD)
        color_print("=" * 70, Colors.BLUE)
        print(f"  Process: {self.process_name or 'Not Attached'}")
        print(f"  Trainer: {'ACTIVE' if self.trainer_active else 'INACTIVE'} (INSERT to toggle)")
        print()
        for key, (name, vtype, default, lock_val, _) in self.cheats.items():
            state = self.cheat_states.get(key, False)
            addr = self.addresses.get(key)
            state_str = "[ON]" if state else "[OFF]"
            color = Colors.GREEN if state else Colors.RED
            addr_str = hex(addr) if addr else "(scan needed)"
            color_print(f"  {key.upper():4} {state_str:5} {name:22} {addr_str:18} -> {lock_val}", color)
        print()
        color_print("=" * 70, Colors.BLUE)


def manual_value_prompt(trainer):
    """Listen for manual value input from user"""
    import select
    print()
    color_print("[*] Manual mode active. Press F-key again and type the value.", Colors.CYAN)
    while True:
        try:
            line = input("Value (or 'q' to quit): ").strip()
            if line.lower() == 'q':
                break
            if trainer.cheat_states.get('_manual_pending'):
                cheat_key = trainer.cheat_states['_manual_pending']
                trainer.manual_scan(cheat_key, line)
                trainer.cheat_states['_manual_pending'] = None
                break
        except EOFError:
            break


def main():
    banner()
    trainer = NFSTrainer()

    if not HAS_PYMEM:
        color_print("[!] pymem library missing. Install: pip install pymem", Colors.RED)
        return

    if not HAS_KEYBOARD:
        color_print("[!] keyboard library missing. Install: pip install keyboard", Colors.RED)
        return

    color_print("[*] Waiting for NFS The Run...", Colors.YELLOW)
    color_print("    Start the game and get into a race.", Colors.YELLOW)

    trainer.find_and_attach()
    trainer.print_status()
    trainer.start_freeze_thread()

    color_print("[*] Hotkeys ready. Press INSERT to activate trainer.", Colors.GREEN)

    try:
        keyboard.add_hotkey('insert', lambda: toggle_trainer(trainer))
        keyboard.add_hotkey('end', lambda: trainer.disable_all())

        for fkey in trainer.cheats.keys():
            keyboard.add_hotkey(fkey, lambda k=fkey: trainer.handle_keypress(k))

        color_print("\n[*] Trainer running. Press Ctrl+C to exit.\n", Colors.GREEN)

        # Watch for process
        while True:
            time.sleep(1)
            if not trainer.process_attached:
                time.sleep(4)
                trainer.find_and_attach()

    except KeyboardInterrupt:
        color_print("\n[*] Shutting down trainer...", Colors.YELLOW)
        trainer.stop_freeze_thread()
        if trainer.process_attached and trainer.pm:
            try:
                trainer.pm.close_process()
            except Exception:
                pass
        color_print("[*] Trainer stopped. Goodbye!", Colors.GREEN)


def toggle_trainer(trainer):
    trainer.trainer_active = not trainer.trainer_active
    if trainer.trainer_active:
        color_print("\n[+] TRAINER ACTIVATED - Cheats ready", Colors.GREEN + Colors.BOLD)
        if not trainer.process_attached:
            trainer.find_and_attach()
    else:
        color_print("\n[-] TRAINER DEACTIVATED - All cheats paused", Colors.YELLOW + Colors.BOLD)
        trainer.disable_all()
    trainer.print_status()


# Patch the trainer class to add handle_keypress method that handles manual mode
def handle_keypress(self, cheat_key):
    """Handle F-key press, including manual mode fallback"""
    pending = self.cheat_states.get('_manual_pending')
    if pending == cheat_key:
        # Manual mode - ask for value
        self.cheat_states['_manual_pending'] = None
        try:
            new_val = input(f"Type the value you saw in-game for {self.cheats[cheat_key][0]}: ").strip()
            self.manual_scan(cheat_key, new_val)
        except EOFError:
            pass
        return

    self.toggle_cheat(cheat_key)

NFSTrainer.handle_keypress = handle_keypress


if __name__ == "__main__":
    main()
