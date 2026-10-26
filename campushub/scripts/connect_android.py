"""Restore CampusHub development ports on a connected physical Android phone."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess


def find_adb():
    """Return an installed ADB path; never install or download anything."""
    on_path = shutil.which("adb")
    if on_path:
        return on_path
    sdk_adb = Path(os.environ.get("LOCALAPPDATA", "")) / "Android/Sdk/platform-tools/adb.exe"
    return str(sdk_adb) if sdk_adb.is_file() else None


def adb_command(adb, *arguments):
    """Run a bounded command with literal arguments, without invoking a shell."""
    return subprocess.run(
        [adb, *arguments], check=True, capture_output=True, text=True, timeout=12,
    ).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", help="Explicit connected ADB serial when multiple phones are attached")
    args = parser.parse_args()
    adb = find_adb()
    if not adb:
        print("ADB not found; skipping Android forwarding. Install/configure the Android SDK for phone development.")
        return 0
    try:
        devices = [
            fields[0]
            for line in adb_command(adb, "devices").splitlines()
            if len(fields := line.split()) >= 2 and fields[1] == "device"
            and not fields[0].startswith("emulator-")
        ]
        if args.device:
            if args.device not in devices:
                print("The requested phone is not connected/authorized. Check adb devices.")
                return 1
            serial = args.device
        elif len(devices) == 1:
            serial = devices[0]
        else:
            print("No single authorized physical phone; skipping forwarding. For multiple phones, run with --device <serial>.")
            return 0
        for port in (8000, 8001):
            adb_command(adb, "-s", serial, "reverse", f"tcp:{port}", f"tcp:{port}")
        print(f"CampusHub phone connection restored for {serial}: Django 8000 / chat 8001.")
        print("Keep Django running. In the app, tap Retry or pull to refresh.")
        return 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"Unable to restore Android forwarding: {error}. Reconnect/authorize the phone and retry.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
