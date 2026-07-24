"""
Painel de torrents concluídos.

Exibe torrents que já finalizaram o download.
Estrutura similar ao TransfersPanel, mas filtrando apenas finished.
"""

import wx
from core.utils import format_size, format_ratio, format_speed
from ui.accessible import AccessibleTorrentList


class CompletedPanel(wx.Panel):
    """Lista de torrents concluídos."""

    COL_NAME = 0
    COL_SIZE = 1
    COL_UPLOAD = 2
    COL_RATIO = 3
    COL_SEEDS = 4

    def __init__(self, main_window, parent):
        super().__init__(parent)
        self.main_window = main_window
        self.parent = parent
        self._torrent_handles: dict = {}
        self._update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer_tick, self._update_timer)
        self.init_ui()

    def init_ui(self):
        i18n = self.main_window.i18n
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.list_label = wx.StaticText(self, label=i18n.t("nav_completed"))
        sizer.Add(self.list_label, 0, wx.LEFT | wx.TOP, 5)

        self.torrents_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.torrents_list.SetAccessible(
            AccessibleTorrentList(i18n.t("nav_completed"))
        )

        col_config = [
            (self.COL_NAME, "torrent_name", 250),
            (self.COL_SIZE, "torrent_size", 80),
            (self.COL_UPLOAD, "torrent_upload", 80),
            (self.COL_RATIO, "torrent_ratio", 80),
            (self.COL_SEEDS, "torrent_seeds", 60),
        ]
        for col_idx, key, width in col_config:
            self.torrents_list.InsertColumn(col_idx, i18n.t(key), width=width)

        self.torrents_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_activated)
        self.torrents_list.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

        sizer.Add(self.torrents_list, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)
        self._update_timer.Start(5000)

    def refresh(self):
        """Atualiza lista com torrents finalizados."""
        engine = self.main_window.engine
        if not engine:
            return

        torrents = engine.get_torrents()
        completed = [t for t in torrents if t.is_finished]
        i18n = self.main_window.i18n

        self.torrents_list.Freeze()
        self.torrents_list.DeleteAllItems()
        self._torrent_handles.clear()

        for entry in sorted(completed, key=lambda t: t.completed_date, reverse=True):
            row = self.torrents_list.GetItemCount()
            self.torrents_list.Append([
                entry.name,
                format_size(entry.size),
                format_speed(entry.upload_rate),
                format_ratio(entry.total_upload, entry.total_download),
                str(entry.num_seeds),
            ])
            self._torrent_handles[entry.info_hash] = row

        self.torrents_list.Thaw()

    def _get_hash_at(self, row: int) -> str:
        for h, r in self._torrent_handles.items():
            if r == row:
                return h
        return ""

    def _on_item_activated(self, event):
        idx = event.GetIndex()
        info_hash = self._get_hash_at(idx)
        if info_hash:
            self.main_window.show_torrent_detail(info_hash)

    def _on_context_menu(self, event):
        idx = self.torrents_list.GetFocusedItem()
        if idx < 0:
            return
        info_hash = self._get_hash_at(idx)
        if not info_hash:
            return

        i18n = self.main_window.i18n
        menu = wx.Menu()
        item_detail = menu.Append(wx.ID_ANY, i18n.t("torrent_detail"))
        item_remove = menu.Append(wx.ID_ANY, i18n.t("remove_torrent"))

        menu.Bind(wx.EVT_MENU, lambda e: self.main_window.show_torrent_detail(info_hash), item_detail)
        menu.Bind(wx.EVT_MENU, lambda e: self.main_window.on_remove_selected(), item_remove)

        self.PopupMenu(menu)
        menu.Destroy()

    def _on_timer_tick(self, event):
        if self.IsShown():
            self.refresh()
