"""Maintain the existing local Kamatera SSH forward; never execute SQL."""
import argparse
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import time
from datetime import datetime, timezone


def ssh_process_running(state_file):
    """Watch the verified SSH process locally, without polling PostgreSQL."""
    try:
        state = json.loads(state_file.read_text(encoding='utf-8-sig'))
        if not isinstance(state, dict) or state.get('Host') != '74.113.234.180' or state.get('LocalPort') != 15432:
            return False
        expected_start = datetime.fromisoformat(state['CreatedAtUtc'].replace('Z', '+00:00')).timestamp()
        expected_image = shutil.which('ssh.exe')
        if not expected_image:
            return False
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x00100000 | 0x1000, False, int(state['ProcessId']))
        if not handle:
            return False
        try:
            if kernel.WaitForSingleObject(handle, 0) != 258:
                return False
            image, length = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length)):
                return False
            if os.path.normcase(image.value) != os.path.normcase(expected_image):
                return False
            created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
            if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)):
                return False
            actual_start = ((created.dwHighDateTime << 32) | created.dwLowDateTime) / 10_000_000 - 11_644_473_600
            return abs(actual_start - expected_start) < .01
        finally:
            kernel.CloseHandle(handle)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def repair_tunnel(script):
    """Reuse the strict owner/key/host checks of the existing one-shot helper."""
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
         'Bypass', '-File', str(script), '-Once'],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=35,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode:
        # No password, URL, caller token or raw PowerShell output in this log.
        logging.warning('Tunnel helper failed (exit %s); see its timestamped SSH log.', result.returncode)
    return result.returncode == 0


def monitor_loop(ready, repair, wait, report, stopped, *, interval=2, maximum=30):
    """Retry only a lost SSH process; bounded backoff and interruptible waits."""
    delay = interval
    while not stopped():
        if ready():
            report('ready')
            delay = interval
            if wait(interval):
                break
            continue
        report('reconnecting')
        try:
            repaired = repair()
        except (OSError, subprocess.TimeoutExpired):
            repaired = False
            logging.warning('Tunnel helper unavailable or timed out.')
        if repaired and ready():
            report('ready')
            delay = interval
        else:
            report('retrying')
        if wait(delay):
            break
        delay = min(delay * 2, maximum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop', action='store_true', help='Stop automatic retries; leave the active SSH tunnel alone.')
    args = parser.parse_args()
    state = Path(os.environ['LOCALAPPDATA']) / 'CampusHub/kamatera-tunnel'
    state.mkdir(parents=True, exist_ok=True)
    stop_file = state / 'monitor.stop'
    if args.stop:
        stop_file.write_text('stop\n', encoding='utf-8')
        print('Automatic tunnel retries will stop; the active SSH tunnel is unchanged.')
        return 0

    # A kernel-managed byte lock is released if this process exits or crashes.
    # It makes a second simultaneous launcher harmless without killing anyone.
    import msvcrt
    with (state / 'monitor.lock').open('a+b') as lock:
        lock.seek(0, os.SEEK_END)
        if not lock.tell():
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return 0
        if stop_file.exists():
            stop_file.unlink()
        logging.basicConfig(filename=state / 'monitor.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s')
        previous = None

        def report(status):
            nonlocal previous
            if status == previous:
                return
            previous = status
            logging.info('Tunnel state: %s', status)
            payload = {'ProcessId': os.getpid(), 'Script': str(Path(__file__).resolve()),
                       'State': status, 'UpdatedAtUtc': datetime.now(timezone.utc).isoformat()}
            temporary = state / 'monitor.json.tmp'
            temporary.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
            temporary.replace(state / 'monitor.json')

        def wait(seconds):
            deadline = time.monotonic() + seconds
            while not stop_file.exists() and time.monotonic() < deadline:
                time.sleep(min(.25, max(0, deadline - time.monotonic())))
            return stop_file.exists()

        script = Path(__file__).with_name('start_kamatera_db_tunnel.ps1')
        report('starting')
        try:
            monitor_loop(lambda: ssh_process_running(state / 'current.json'),
                         lambda: repair_tunnel(script), wait, report, stop_file.exists)
        finally:
            report('stopped')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
