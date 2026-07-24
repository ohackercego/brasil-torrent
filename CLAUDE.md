# Brasil Torrent — Claude Code Instructions

## Project
Brasil Torrent — wxPython + libtorrent 2.0.x BitTorrent client, accessibility-first for screen readers.

## Commands
- **Run app:** `python client/main.py`
- **Run tests:** `pytest client/tests/ -v`
- **Single test:** `pytest client/tests/test_FILE.py::TEST_CLASS::test_NAME -v`

## Architecture (key files)
- `client/main.py` — MainFrame (wx.Frame), engine init, menu, close handling, global hotkey
- `client/core/torrent_engine.py` — TorrentEngine (libtorrent session), TorrentEntry dataclass
- `client/ui/transfers.py` — TorrentsPanel with ListCtrl, filter buttons, action buttons
- `client/ui/dialogs/torrent_detail.py` — TorrentDetailDialog with TreeCtrl + progress announcer
- `client/ui/dialogs/settings_dialog.py` — SettingsDialog with notebook (General/Connection/Privacy)
- `client/ui/tray_icon.py` — BrasilTorrentTrayIcon (TaskBarIcon)
- `client/core/i18n.py` — I18n class (JSON-based)
- `client/config.py` — Settings manager (json file in data/)

## Key Patterns
- All user strings: `self.i18n.t("key")` — add to both `languages/pt-BR.json` and `en-US.json`
- Screen reader output: `self.main_window.output(text, interrupt=True)`
- EVT_CHAR_HOOK for Alt+F4 (not EVT_CLOSE)
- Global hotkey via `RegisterHotKey` (Ctrl+Shift+B restores from tray)
- TorrentEntry.`paused` / `stopped` flags control state; `state_str` is i18n key
- Settings: `settings["section"]["key"]` or `settings.get_setting("section", "key", default=val)`
- TreeCtrl uses `TR_HIDE_ROOT` — use `AppendItem(root, ...)` not `AddChild`

## Testing
- 105 tests, all in `client/tests/`
- Test entry state via TorrentEntry dataclass directly
- Always run full suite before committing

## Common Bugs to Check
- Missing i18n keys in one language file but not the other
- `event.Veto()` vs `event.Skip()` in close/exit handlers
- `GetFocusedItem()` can fail after button click — use `_selected_hash`
- `SpinCtrlDouble` accessibility issues — prefer `SpinCtrl` with ×10 scaling
