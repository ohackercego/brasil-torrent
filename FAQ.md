# Frequently Asked Questions

## General

### What is Brasil Torrent?
Brasil Torrent is a free, open-source BitTorrent client for Windows. It is designed to be fast, lightweight, and fully accessible for blind and visually impaired users.

### Does Brasil Torrent mine cryptocurrency?
**No.** Brasil Torrent does not mine cryptocurrency, show ads, track your activity, or include any hidden processes. It is a clean BitTorrent client focused on file sharing.

### Is Brasil Torrent free?
Yes, it is completely free and open-source under the MIT License.

### Where can I download it?
Visit the [Releases page](https://github.com/azurejoga/brasil-torrent/releases).

---

## Accessibility

### Which screen readers are supported?
Brasil Torrent works with **NVDA**, **JAWS**, **Windows Narrator**, and any SAPI5-compatible screen reader.

### Do I need a screen reader to use it?
No. The application is fully usable with keyboard and mouse. The screen reader integration simply enhances the experience for blind and visually impaired users.

### How do progress announcements work?
The application speaks progress updates at configurable intervals (default: every 10%). You can change this in **Settings → General → Announce progress every N%**.

---

## Usage

### How do I add a torrent?
Press `Ctrl+T` to open the add torrent dialog. You can enter a magnet link or browse for a `.torrent` file.

### What are the filter tabs?
The tabs above the torrent list let you filter by:
- **All** — Every torrent
- **Downloading** — Actively downloading
- **Seeding** — Complete and uploading
- **Paused** — Paused or stopped torrents
- **Finished** — Fully completed

### How do I stop a torrent?
Select the torrent and press `Ctrl+P` or click the Stop/Continue button. To fully stop (not just pause), use the same button.

### How do I remove a torrent?
Select it and press `Delete` or click the Remove button. You will be asked to confirm.

### Can I set download speed limits?
Yes. Press `Ctrl+L` or go to **Settings → Connection** to set global download and upload limits.

---

## Technical

### Where are settings stored?
Settings are saved to `data/config.json` in the application directory.

### Where are logs?
Logs are written to `data/brasil_torrent.log` and a `log.txt` file in the `client/` directory.

### How do I start Brasil Torrent with Windows?
Go to **Settings → General** and check **Start with Windows**. This adds an entry to the Windows Registry.

### How do I report a bug?
Open an issue on [GitHub Issues](https://github.com/azurejoga/brasil-torrent/issues). Include logs and steps to reproduce.

### How do I build from source?
```bash
git clone https://github.com/azurejoga/brasil-torrent.git
cd brasil-torrent
pip install -r requirements.txt
python client/main.py
```

---

## Troubleshooting

### The app doesn't start
- Make sure Python 3.12 or later is installed
- Run `pip install -r requirements.txt` to install dependencies
- Check `log.txt` in the `client/` directory for errors

### Screen reader is not speaking
- Make sure NVDA, JAWS, or Narrator is running
- Check that `accessible_output2` is installed (`pip install accessible_output2`)
- The app will work without a screen reader — output goes to the log

### Alt+F4 doesn't show exit dialog
This is a known issue with wxPython and modal dialogs. We use `EVT_CHAR_HOOK` to intercept Alt+F4 before the close event fires. If it still doesn't work, use **File → Exit** instead.

### Torrent stays at "awaiting metadata"
Magnet links may take time to resolve. Make sure DHT is enabled and the swarm has seeders.
