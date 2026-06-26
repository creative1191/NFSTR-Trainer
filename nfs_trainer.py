#!/usr/bin/env python3
"""
NFS The Run Trainer - Clean Version 3.0
LinGon-style trainer that works on all game versions.

HOTKEYS:
  INSERT   - Activate/deactivate trainer
  END      - Disable all cheats
  F2-F11   - Cheats (matches LinGon exactly)

USAGE:
  1. Start NFS The Run, enter a race
  2. Run this trainer (or the compiled .exe)
  3. Press INSERT to activate
  4. Press F-key twice (first scan, then activate)
"""

import sys
import os
import time
import struct
import threading

try:
    import pymem
    import pymem.process
    HAS_PYMEM = True
except ImportError:
    HAS_PYMEM = False

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

PROCESS_NAMES = ["Need For Speed The Run.exe", "NeedForSpeedTheRun.exe"]

# ANSI color codes
class C:
    H = '\033[95m'
    B = '\033[94m'
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    C = '\033[96m'
    W = '\033[97m'
    E = '\033[0m'
    K = '\033[90m'

# Enable ANSI on Windows
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


def cp(text, color):
    """Print colored text"""
    print(color + text + C.E)


class NFSTrainer:
    def __init__(self):
        self.pm = None
        self.attached = False
        self.process_name = None
        self.active = False

        # cheat_key -> (name, type, default, lock_value, max_value)
        self.cheats = {
            'f2':  ('Stage Timer',     'float', 0.0, 9999.0,   9999.0),
            'f3':  ('Super Speed',     'float', 0.0, 350.0,    500.0),
            'f4':  ('Super Brakes',    'float', 0.0, 9999.0,   9999.0),
            'f5':  ('Freeze AI Cars',  'float', 0.0, 0.0,      100.0),
            'f6':  ('Infinite Resets', 'int',   3,   99,       99),
            'f7':  ('Challenge Time',  'float', 0.0, 9999.0,   9999.0),
            'f8':  ('10x XP',          'int',   0,   99999999, 99999999),
            'f9':  ('Infinite Nitro',  'float', 0.0, 5.0,      5.0),
            'f10': ('Race Time',       'float', 0.0, 9999.0,   9999.0),
            'f11': ('Checkpoint Time', 'float', 0.0, 9999.0,   9999.0),
        }

        self.addresses = {}    # cheat_key -> address
        self.first_scan = {}   # cheat_key -> [addresses]
        self.cheat_states = {}
        self.manual_pending = None

        for key in self.cheats:
            self.cheat_states[key] = False

        self.freeze_running = False

    def attach(self):
        if not HAS_PYMEM:
            cp('[!] pymem not available. Run: pip install pymem', C.R)
            return False

        for name in PROCESS_NAMES:
            try:
                self.pm = pymem.Pymem(name)
                self.process_name = name
                self.attached = True
                cp('[+] Attached to ' + name + ' (PID: ' + str(self.pm.process_id) + ')', C.G)
                return True
            except pymem.process.NotFoundByName:
                continue
            except Exception as e:
                cp('[!] Error: ' + str(e), C.R)

        cp('[!] NFS The Run not found. Start the game first.', C.R)
        return False

    def read_float(self, addr):
        try:
            return self.pm.read_float(addr)
        except Exception:
            return None

    def read_int(self, addr):
        try:
            return self.pm.read_int(addr)
        except Exception:
            return None

    def write_float(self, addr, val):
        try:
            self.pm.write_float(addr, val)
            return True
        except Exception:
            return False

    def write_int(self, addr, val):
        try:
            self.pm.write_int(addr, val)
            return True
        except Exception:
            return False

    def scan(self, value, vtype):
        pattern = struct.pack('<f', value) if vtype == 'float' else struct.pack('<i', value)
        try:
            results = self.pm.pattern_scan_all(pattern, return_multiple=True)
            if isinstance(results, list):
                return results
            elif results:
                return [results]
            return []
        except Exception as e:
            cp('[!] Scan error: ' + str(e), C.R)
            return []

    def toggle_cheat(self, key):
        if not self.active:
            return

        if not self.attached:
            if not self.attach():
                return

        name, vtype, default, lock_val, max_val = self.cheats[key]

        # If already active, disable
        if self.cheat_states.get(key, False):
            self.cheat_states[key] = False
            cp('[-] ' + name + ': DISABLED', C.Y)
            return

        # If we already have address, just lock
        if key in self.addresses and self.addresses[key] is not None:
            addr = self.addresses[key]
            if vtype == 'float':
                self.write_float(addr, lock_val)
            else:
                self.write_int(addr, lock_val)
            self.cheat_states[key] = True
            cp('[+] ' + name + ': ACTIVATED at ' + hex(addr) + ' (locked to ' + str(lock_val) + ')', C.G)
            return

        # Manual mode fallback
        if self.manual_pending == key:
            self.manual_pending = None
            try:
                new_val_raw = input('Enter the value you saw in-game: ').strip()
                new_val = float(new_val_raw) if vtype == 'float' else int(new_val_raw)
                candidates = self.first_scan.get(key, [])
                if not isinstance(candidates, list) or not candidates:
                    cp('[!] No candidates stored. Retry first scan.', C.R)
                    return
                if candidates and isinstance(candidates[0], tuple):
                    addrs = [c[0] for c in candidates]
                else:
                    addrs = candidates
                matches = []
                for a in addrs:
                    cur = self.read_float(a) if vtype == 'float' else self.read_int(a)
                    if cur is not None and abs(cur - new_val) < 0.01:
                        matches.append(a)
                if len(matches) == 1:
                    addr = matches[0]
                    self.addresses[key] = addr
                    if vtype == 'float':
                        self.write_float(addr, lock_val)
                    else:
                        self.write_int(addr, lock_val)
                    self.cheat_states[key] = True
                    cp('[+] ' + name + ': LOCKED at ' + hex(addr), C.G)
                elif len(matches) > 1:
                    cp('[!] ' + str(len(matches)) + ' matches. Need more action.', C.R)
                else:
                    cp('[!] No match. Wrong value typed?', C.R)
            except (EOFError, ValueError):
                cp('[!] Invalid input', C.R)
            return

        # First scan
        if key not in self.first_scan:
            cp('[?] ' + name + ': Scanning for value ' + str(default) + '...', C.C)
            results = self.scan(default, vtype)
            if not results:
                cp('[!] No candidates. Are you in a race?', C.R)
                return
            self.first_scan[key] = results[:3000]
            cp('[?] Found ' + str(len(results)) + ' candidates.', C.C)
            cp('    >>> DO THE ACTION IN-GAME <<<', C.Y)
            cp('    >>> Then press ' + key.upper() + ' again <<<', C.Y)
            if name == 'Infinite Nitro':
                cp('    (Press SHIFT in-game to use nitro)', C.K)
            return

        # Second press - narrow down by change
        candidates = self.first_scan[key]
        cp('[?] Re-reading ' + str(len(candidates)) + ' candidates...', C.C)

        changed = []
        for addr in candidates:
            if vtype == 'float':
                cur = self.read_float(addr)
            else:
                cur = self.read_int(addr)
            if cur is None:
                continue
            if vtype == 'float':
                if abs(cur - default) > 0.001:
                    changed.append((addr, cur))
            else:
                if cur != default:
                    changed.append((addr, cur))

        cp('[?] ' + str(len(changed)) + ' changed values found', C.C)

        if not changed:
            cp('[!] Nothing changed. Did you do the action?', C.R)
            cp('    Press ' + key.upper() + ' to retry', C.Y)
            del self.first_scan[key]
            return

        # Filter by reasonable range
        valid = []
        for addr, val in changed:
            if vtype == 'float':
                if 0.0 < val <= max_val:
                    valid.append((addr, val))
            else:
                if 0 <= val <= max_val:
                    valid.append((addr, val))

        cp('[?] ' + str(len(valid)) + ' candidates in valid range', C.C)

        if len(valid) == 1:
            addr, val = valid[0]
            self.addresses[key] = addr
            if vtype == 'float':
                self.write_float(addr, lock_val)
            else:
                self.write_int(addr, lock_val)
            self.cheat_states[key] = True
            cp('[+] ' + name + ': LOCKED at ' + hex(addr) + ' (was ' + str(val) + ')', C.G)
            return

        if len(valid) <= 10:
            cp('[?] Testing each candidate...', C.Y)
            for addr, val in valid:
                cp('    Test: ' + hex(addr) + ' (was ' + str(val) + ')', C.K)
                for _ in range(2):
                    if vtype == 'float':
                        self.write_float(addr, lock_val)
                    else:
                        self.write_int(addr, lock_val)
                    time.sleep(0.1)
                check = self.read_float(addr) if vtype == 'float' else self.read_int(addr)
                if check is not None and abs(check - lock_val) < 0.01:
                    self.addresses[key] = addr
                    self.cheat_states[key] = True
                    cp('[+] ' + name + ': LOCKED at ' + hex(addr), C.G)
                    return
            cp('[!] No candidate responded. Try again.', C.R)
            del self.first_scan[key]
            return

        # Too many - manual mode
        cp('[!] Too many candidates (' + str(len(valid)) + '). Need manual input.', C.R)
        cp('', C.E)
        cp('    Press ' + key.upper() + ' a 3rd time, then type the value you see in-game', C.C)
        self.first_scan[key] = valid
        self.manual_pending = key

    def disable_all(self):
        for key in list(self.cheat_states.keys()):
            self.cheat_states[key] = False
        cp('[-] ALL CHEATS DISABLED', C.Y)

    def start_freeze(self):
        self.freeze_running = True
        threading.Thread(target=self._freeze_loop, daemon=True).start()

    def _freeze_loop(self):
        while self.freeze_running:
            if not self.attached or not self.active:
                time.sleep(0.5)
                continue
            for key, active in self.cheat_states.items():
                if not active or key not in self.addresses:
                    continue
                addr = self.addresses[key]
                lock_val = self.cheats[key][3]
                vtype = self.cheats[key][1]
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
        cp('=' * 70, C.B)
        cp('  TRAINER STATUS', C.W)
        cp('=' * 70, C.B)
        print('  Process: ' + (self.process_name or 'Not Attached'))
        print('  Trainer: ' + ('ACTIVE' if self.active else 'INACTIVE') + ' (INSERT to toggle)')
        print()
        for key, (name, vtype, default, lock_val, _) in self.cheats.items():
            state = '[ON]' if self.cheat_states.get(key, False) else '[OFF]'
            addr = hex(self.addresses[key]) if key in self.addresses else '(scan needed)'
            color = C.G if state == '[ON]' else C.R
            line = '  ' + key.upper().ljust(4) + ' ' + state.ljust(5) + ' ' + name.ljust(22) + ' ' + addr.ljust(18) + ' -> ' + str(lock_val)
            cp(line, color)
        print()
        cp('=' * 70, C.B)


def main():
    cp('=' * 70, C.H)
    cp('  NFS THE RUN v1.1.0.0 - TRAINER v3.0', C.H)
    cp('  LinGon-Style Auto-Scanner', C.B)
    cp('  Works on ALL versions', C.G)
    cp('=' * 70, C.E)

    trainer = NFSTrainer()

    if not HAS_PYMEM:
        cp('[!] Install pymem: pip install pymem', C.R)
        return
    if not HAS_KEYBOARD:
        cp('[!] Install keyboard: pip install keyboard', C.R)
        return

    cp('[*] Waiting for NFS The Run...', C.Y)
    trainer.attach()
    trainer.print_status()
    trainer.start_freeze()

    cp('[*] Hotkeys ready. INSERT to activate. END to disable all.', C.G)
    print()

    try:
        keyboard.add_hotkey('insert', lambda: toggle(trainer))
        keyboard.add_hotkey('end', lambda: trainer.disable_all())
        for key in trainer.cheats:
            keyboard.add_hotkey(key, lambda k=key: trainer.toggle_cheat(k))

        while True:
            time.sleep(1)
            if not trainer.attached:
                time.sleep(4)
                trainer.attach()
    except KeyboardInterrupt:
        cp('[*] Shutting down...', C.Y)
        trainer.freeze_running = False
        if trainer.attached and trainer.pm:
            try:
                trainer.pm.close_process()
            except Exception:
                pass
        cp('[*] Bye!', C.G)


def toggle(trainer):
    trainer.active = not trainer.active
    if trainer.active:
        cp('[+] TRAINER ACTIVATED', C.G)
        if not trainer.attached:
            trainer.attach()
    else:
        cp('[-] TRAINER DEACTIVATED', C.Y)
        trainer.disable_all()
    trainer.print_status()


if __name__ == '__main__':
    main()
