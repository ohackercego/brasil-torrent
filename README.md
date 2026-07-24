# Brasil Torrent

**The fast, lightweight BitTorrent client that doesn't mine cryptocurrency on your PC.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/azurejoga/brasil-torrent)](https://github.com/azurejoga/brasil-torrent/releases)
[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)

Brasil Torrent is a full-featured BitTorrent client built with **wxPython** and **libtorrent 2.0.x**, designed from the ground up to be **fully accessible** for blind and visually impaired users. It works seamlessly with **NVDA**, **JAWS**, and **Narrator** screen readers.

---

## ✨ Features

- **♿ Full Screen Reader Support** — Works flawlessly with NVDA, JAWS, and Windows Narrator. Every control, progress update, and notification is spoken aloud.
- **⚡ Fast & Lightweight** — No bloat, no background processes, no hidden miners. Built on libtorrent 2.0.x for maximum performance.
- **🔊 Voice Progress Announcements** — Configurable interval announcements via SAPI5 or your screen reader. No need to stare at progress bars.
- **🖥️ Complete BitTorrent Support** — Magnet links, `.torrent` files, DHT, PEX, UPnP/NAT-PMP, encryption.
- **📁 Multi-torrent Management** — Tabbed filtering (All / Downloading / Seeding / Paused / Finished), sortable columns, context menus.
- **🌐 Bilingual Interface** — Portuguese (Brazil) and English, auto-detected from your system language on first launch.
- **🔄 Sequential Download** — Stream files in order, useful for media playback.
- **🚦 Speed Limits** — Set global download and upload limits.
- **🖱️ System Tray** — Minimize to tray with accessible tray icon. Ctrl+Shift+B restores the window.
- **💾 Session Persistence** — Resumes unfinished downloads across restarts.
- **🔒 Privacy Focused** — No tracking, no analytics, no crypto mining. Ever.

---

## 📥 Installation

### From Releases (Recommended)

1. Go to the [Releases page](https://github.com/azurejoga/brasil-torrent/releases)
2. Download the latest version (`brasil-torrent-1.0.0.exe`)
3. Verify the file integrity:

   ```
   SHA256: `fd450bd10cf80388b38ce7c372c9473eb754e21b79fe71f64cfe73a349498f91`
   MD5: `2979741cdd6dfac58208c49c01de8dc7`
   ```

4. Run the executable

### From Source

```bash
git clone https://github.com/azurejoga/brasil-torrent.git
cd brasil-torrent
pip install -r requirements.txt
python client/main.py
```

**Requirements:** Python 3.12+, wxPython 4.x, libtorrent 2.0.x, accessible_output2.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Add torrent |
| `Ctrl+O` | Open .torrent file |
| `Ctrl+L` | Speed limits |
| `Ctrl+P` | Stop / Continue torrent |
| `Delete` | Remove selected torrent |
| `F5` | Refresh list |
| `D` | Show torrent details |
| `Enter` | Open selected torrent details |
| `Alt+3` | Open settings |
| `Ctrl+Shift+B` | Restore window from tray |
| `Alt+F4` | Exit dialog (Minimize / Exit / Cancel) |

---

## ♿ Accessibility

Brasil Torrent was built with accessibility as a core principle, not an afterthought.

- **Screen Reader Native** — Uses `accessible_output2` for direct NVDA/JAWS/Narrator output, plus wxPython's built-in accessibility layer for all controls.
- **Progress by Voice** — Progress announcements at configurable intervals (default every 10%). No need to read visual gauges.
- **Full Keyboard Navigation** — Every function is accessible via keyboard shortcuts. No mouse required.
- **Descriptive Labels** — All controls, columns, and status changes are announced. Focus is managed carefully to avoid confusion.
- **High Contrast Compatible** — Works with Windows High Contrast themes.

---

## 🛠️ Build from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python client/main.py
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This software is a tool for file sharing using the BitTorrent protocol. The authors do not endorse, encourage, or take responsibility for:

- Downloading copyrighted material without authorization
- Sharing illegal or pirated content
- Using the software in violation of local, national, or international laws

**Users are solely responsible** for verifying the legality of the content they download or share and for complying with applicable laws.

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a pull request.

---

## 🆘 Support

- **Issues & Bug Reports:** [GitHub Issues](https://github.com/azurejoga/brasil-torrent/issues)
- **Security Vulnerabilities:** See [SECURITY.md](SECURITY.md)

---

<p align="center">
Made with ❤️ by the <strong>Eternal Legend Team</strong>
</p>
