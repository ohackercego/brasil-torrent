"""
Brasil Torrent — Build Script (PyInstaller)

Usage:
    python build.py                       # one-dir build
    python build.py --onefile             # single exe build
    python build.py --no-console          # hide console window
    python build.py --version-file        # include version info
    python build.py --clean               # clean build artifacts
    python build.py --onefile --clean     # single exe, clean first

Requires: pip install pyinstaller
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLIENT = ROOT / "client"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
SPEC = ROOT / "brasil-torrent.spec"
VERSION_FILE = ROOT / "version_info.txt"
LOG_FILE = ROOT / "build.log"
README = ROOT / "README.md"


def parse_args():
    parser = argparse.ArgumentParser(description="Build Brasil Torrent with PyInstaller")
    parser.add_argument("--onefile", action="store_true", help="Build single executable")
    parser.add_argument("--no-console", action="store_true", help="Hide console window (Windows GUI mode)")
    parser.add_argument("--version-file", action="store_true", help="Include Windows version info")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts before building")
    parser.add_argument("--debug", action="store_true", help="Build with debug symbols")
    parser.add_argument("--upx-dir", type=str, default="", help="Path to UPX compression tool directory")
    return parser.parse_args()


def clean():
    """Remove previous build artifacts."""
    for path in [DIST, BUILD, SPEC, VERSION_FILE, LOG_FILE]:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)
    print("Build artifacts cleaned.")


def create_version_file():
    """Generate Windows version info for the executable."""
    from client.version import __version__, __app_name__, __author__, __description__, __url__

    parts = __version__.split(".")
    major = parts[0] if len(parts) > 0 else "1"
    minor = parts[1] if len(parts) > 1 else "0"
    patch = parts[2] if len(parts) > 2 else "0"

    content = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# https://pyinstaller.org/en/stable/feature-notes.html#windows-version-information
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', '{__author__}'),
          StringStruct('FileDescription', '{__description__}'),
          StringStruct('FileVersion', '{__version__}'),
          StringStruct('InternalName', '{__app_name__}'),
          StringStruct('LegalCopyright', 'MIT License'),
          StringStruct('OriginalFilename', 'brasil-torrent.exe'),
          StringStruct('ProductName', '{__app_name__}'),
          StringStruct('ProductVersion', '{__version__}'),
          StringStruct('SupportUrl', '{__url__}')])
      ]),
    VarFileInfo([VarStruct('Translation', 0x0409, 1200)])
  ]
)
"""
    VERSION_FILE.write_text(content, encoding="utf-8")
    print(f"Version file created: {VERSION_FILE}")
    return VERSION_FILE


def file_hash(path: Path, algo: str) -> str:
    """Return hex digest of a file."""
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _get_version() -> str:
    """Reads version from client/version.py without importing it."""
    vf = CLIENT / "version.py"
    if vf.is_file():
        m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', vf.read_text(encoding="utf-8"))
        if m:
            return m.group(1)
    return "0.0.0"


def update_readme(sha256: str, md5: str):
    """Updates the SHA256 and MD5 inside the download section of README.md."""
    if not README.is_file():
        print("README.md not found, skipping hash update.")
        return

    text = README.read_text(encoding="utf-8")
    version = _get_version()

    new = re.sub(
        r"SHA256: `[a-f0-9]+`",
        f"SHA256: `{sha256}`",
        text,
    )
    new = re.sub(
        r"MD5: `[a-f0-9]+`",
        f"MD5: `{md5}`",
        new,
    )
    new = re.sub(
        r"brasil-torrent-[\w.]+\.exe",
        f"brasil-torrent-{version}.exe",
        new,
    )

    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README.md updated with new hashes.")
    else:
        print("No changes needed in README.md.")


def build(args):
    """Run PyInstaller with the configured options."""
    pyinstaller = shutil.which("pyinstaller")
    if not pyinstaller:
        print("PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)

    # Base command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "brasil-torrent",
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        "--specpath", str(ROOT),
        "--paths", str(CLIENT),
        "--add-data", f"{CLIENT / 'languages'}{os.pathsep}client/languages",
        "--add-data", f"{CLIENT / 'sounds'}{os.pathsep}client/sounds",
        "--hidden-import", "wx",
        "--hidden-import", "wx.adv",
        "--hidden-import", "wx.html2",
        "--hidden-import", "libtorrent",
        "--hidden-import", "accessible_output2",
        "--hidden-import", "accessible_output2.outputs.auto",
        "--hidden-import", "accessible_output2.outputs.nvda",
        "--hidden-import", "accessible_output2.outputs.jaws",
        "--hidden-import", "accessible_output2.outputs.sapi5",
        "--collect-all", "accessible_output2",
        "--collect-all", "wx",
        "--collect-submodules", "libtorrent",
    ]

    if args.onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if args.no_console:
        cmd.append("--noconsole")
        cmd.append("--windowed")

    if args.version_file:
        vf = create_version_file()
        cmd.extend(["--version-file", str(vf)])

    if args.upx_dir:
        cmd.extend(["--upx-dir", args.upx_dir])

    if args.debug:
        cmd.append("--debug")

    cmd.append(str(CLIENT / "main.py"))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=False)

    if result.returncode != 0:
        print(f"\n[FAIL] Build failed (exit code {result.returncode})")
        sys.exit(1)

    print("\n[OK] Build successful!")

    if args.onefile:
        exe = DIST / "brasil-torrent.exe"
        if exe.exists():
            size = exe.stat().st_size / (1024 * 1024)
            print(f"   Output: {exe} ({size:.1f} MB)")
            sha256 = file_hash(exe, "sha256")
            md5 = file_hash(exe, "md5")
            print(f"   SHA256: {sha256}")
            print(f"   MD5:    {md5}")
            update_readme(sha256, md5)
    else:
        out = DIST / "brasil-torrent" / "brasil-torrent.exe"
        if out.exists():
            size = out.stat().st_size / (1024 * 1024)
            print(f"   Output: {out} ({size:.1f} MB)")


def main():
    args = parse_args()

    print("=" * 56)
    print("  Brasil Torrent - Build Script")
    print("=" * 56)
    print()

    if args.clean:
        clean()

    build(args)


if __name__ == "__main__":
    main()
