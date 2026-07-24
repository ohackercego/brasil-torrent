"""
Painel único de torrents com filtros, barra de progresso acessível
e painel de detalhes.

Filtros: Todos | Baixando | Semeando | Parados | Finalizados
Ao selecionar um torrent, mostra barra de progresso + informações abaixo.
Enter ou 'd' abre diálogo de detalhes com TreeCtrl de arquivos.
"""

import wx
from config import settings
from core.utils import format_size, format_speed, format_eta, format_percent, format_ratio
from ui.accessible import (
    AccessibleTorrentList,
    AccessibleRefreshTorrents,
)

# Índices de coluna
COL_NAME = 0
COL_SIZE = 1
COL_PROGRESS = 2
COL_STATUS = 3
COL_DOWNLOAD = 4
COL_UPLOAD = 5
COL_ETA = 6
COL_SEEDS = 7
COL_PEERS = 8
COL_RATIO = 9

COLUMN_LABELS = [
    "torrent_name",
    "torrent_size",
    "torrent_progress",
    "torrent_status",
    "torrent_download",
    "torrent_upload",
    "torrent_eta",
    "torrent_seeds",
    "torrent_peers",
    "torrent_ratio",
]

_COL_SORT_TYPES = {
    COL_NAME: str,
    COL_SIZE: int,
    COL_PROGRESS: float,
    COL_STATUS: str,
    COL_DOWNLOAD: int,
    COL_UPLOAD: int,
    COL_ETA: int,
    COL_SEEDS: int,
    COL_PEERS: int,
    COL_RATIO: float,
}


class TorrentRow:
    """Dados de uma linha da lista, para ordenação e filtro."""

    def __init__(self, info_hash, name, size, progress, status, download_rate,
                 upload_rate, eta, seeds, peers, ratio, state, paused, stopped, is_finished):
        self.info_hash = info_hash
        self.name = name
        self.size = size
        self.progress = progress
        self.status = status
        self.download_rate = download_rate
        self.upload_rate = upload_rate
        self.eta = eta
        self.seeds = seeds
        self.peers = peers
        self.ratio = ratio
        self.state = state
        self.paused = paused
        self.stopped = stopped
        self.is_finished = is_finished

    def get_sort_value(self, col):
        m = {
            COL_NAME: self.name.lower(),
            COL_SIZE: self.size,
            COL_PROGRESS: self.progress,
            COL_STATUS: self.status,
            COL_DOWNLOAD: self.download_rate,
            COL_UPLOAD: self.upload_rate,
            COL_ETA: self.eta if self.eta >= 0 else 999999999,
            COL_SEEDS: self.seeds,
            COL_PEERS: self.peers,
            COL_RATIO: self.ratio,
        }
        return m.get(col, self.name.lower())


# ── Filtros ─────────────────────────────────────────────────────────────────
FILTER_ALL = 0
FILTER_DOWNLOADING = 1
FILTER_SEEDING = 2
FILTER_PAUSED = 3
FILTER_FINISHED = 4

FILTER_KEYS = ["filter_all", "filter_downloading", "filter_seeding",
               "filter_paused", "filter_finished"]


class TorrentsPanel(wx.Panel):
    """Painel único de torrents com filtros e barra de progresso."""

    def __init__(self, main_window, parent):
        super().__init__(parent)
        self.main_window = main_window
        self.parent = parent
        self._rows = []
        self._filtered_rows = []
        self._selected_hash = ""
        self._last_announced_pct = 0
        self._sort_col = COL_NAME
        self._sort_asc = True
        self._filter = FILTER_ALL
        self._update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer_tick, self._update_timer)

        self.init_ui()
        self.create_accelerators()

    def init_ui(self):
        i18n = self.main_window.i18n
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ── Barra de ferramentas ──────────────────────────────────────────────
        toolbar = wx.BoxSizer(wx.HORIZONTAL)

        self.add_torrent_btn = wx.Button(self, label=i18n.t("add_torrent"))
        self.add_torrent_btn.Bind(wx.EVT_BUTTON, lambda e: self.main_window.on_add_torrent())
        toolbar.Add(self.add_torrent_btn, 0, wx.RIGHT, 5)

        self.action_btn = wx.Button(self, label=i18n.t("action_stop"))
        self.action_btn.Bind(wx.EVT_BUTTON, lambda e: self.main_window.on_stop_continue_selected())
        toolbar.Add(self.action_btn, 0, wx.RIGHT, 5)

        self.remove_btn = wx.Button(self, label=i18n.t("remove_selected"))
        self.remove_btn.Bind(wx.EVT_BUTTON, lambda e: self.main_window.on_remove_selected())
        toolbar.Add(self.remove_btn, 0, wx.RIGHT, 5)

        self.refresh_btn = wx.Button(self, label=i18n.t("refresh"))
        self.refresh_btn.SetAccessible(AccessibleRefreshTorrents())
        self.refresh_btn.Bind(wx.EVT_BUTTON, lambda e: self.main_window.refresh_torrents())
        toolbar.Add(self.refresh_btn, 0)

        sizer.Add(toolbar, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 5)

        # ── Filtros ──────────────────────────────────────────────────────────
        self.filter_label = wx.StaticText(self, label=i18n.t("filter_label"))
        sizer.Add(self.filter_label, 0, wx.LEFT | wx.TOP, 5)

        filter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.filter_buttons = []
        filter_labels = [
            i18n.t("filter_all"),
            i18n.t("filter_downloading"),
            i18n.t("filter_seeding"),
            i18n.t("filter_paused"),
            i18n.t("filter_finished"),
        ]
        self._filter_rb = wx.RadioBox(
            self,
            label="",
            choices=filter_labels,
            style=wx.RA_HORIZONTAL,
        )
        self._filter_rb.SetSelection(0)
        self._filter_rb.Bind(wx.EVT_RADIOBOX, self._on_filter_changed)
        sizer.Add(self._filter_rb, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        # ── Lista de torrents ─────────────────────────────────────────────────
        self.list_label = wx.StaticText(self, label=i18n.t("torrent_list_label"))
        sizer.Add(self.list_label, 0, wx.LEFT | wx.TOP, 5)

        self.torrents_list = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL
        )
        self.torrents_list.SetAccessible(
            AccessibleTorrentList(i18n.t("torrent_list_label"))
        )

        col_widths = [250, 80, 70, 110, 80, 80, 70, 60, 60, 60]
        for col_idx, (key, width) in enumerate(zip(COLUMN_LABELS, col_widths)):
            self.torrents_list.InsertColumn(col_idx, i18n.t(key), width=width)

        self.torrents_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_torrent_activated)
        self.torrents_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_torrent_selected)
        self.torrents_list.Bind(wx.EVT_LIST_ITEM_FOCUSED, self._on_torrent_focused)
        self.torrents_list.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)
        self.torrents_list.Bind(wx.EVT_KEY_DOWN, self._on_list_key_down)
        self.torrents_list.Bind(wx.EVT_LIST_COL_CLICK, self._on_col_click)

        sizer.Add(self.torrents_list, 2, wx.EXPAND | wx.ALL, 5)

        # ── Painel de detalhes (info) ────────────────────────────────────────
        detail_box = wx.StaticBox(self, label=i18n.t("selected_torrent_info"))
        detail_sizer = wx.StaticBoxSizer(detail_box, wx.VERTICAL)

        # Info label
        self.info_label = wx.StaticText(detail_box, label="")
        detail_sizer.Add(self.info_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Botão Detalhes / Fechar
        detail_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detail_btn = wx.Button(detail_box, label=i18n.t("torrent_detail"))
        self.detail_btn.Bind(wx.EVT_BUTTON, self._on_detail_button)
        detail_btn_sizer.Add(self.detail_btn, 0, wx.RIGHT, 5)

        self.deselect_btn = wx.Button(detail_box, label=i18n.t("deselect"))
        self.deselect_btn.Bind(wx.EVT_BUTTON, self._on_deselect)
        detail_btn_sizer.Add(self.deselect_btn, 0)

        detail_sizer.Add(detail_btn_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        sizer.Add(detail_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.SetSizer(sizer)
        self._update_timer.Start(2000)

    def create_accelerators(self):
        """Atalhos de teclado."""
        ids = {
            "CTRL_T": wx.NewIdRef(),
            "DELETE": wx.NewIdRef(),
            "CTRL_P": wx.NewIdRef(),
            "F5": wx.NewIdRef(),
            "CTRL_O": wx.NewIdRef(),
            "CTRL_L": wx.NewIdRef(),
            "D": wx.NewIdRef(),
        }
        entries = [
            (wx.ACCEL_CTRL, ord("T"), ids["CTRL_T"]),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ids["DELETE"]),
            (wx.ACCEL_CTRL, ord("P"), ids["CTRL_P"]),
            (wx.ACCEL_NORMAL, wx.WXK_F5, ids["F5"]),
            (wx.ACCEL_CTRL, ord("O"), ids["CTRL_O"]),
            (wx.ACCEL_CTRL, ord("L"), ids["CTRL_L"]),
            (wx.ACCEL_NORMAL, ord("D"), ids["D"]),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

        self.Bind(wx.EVT_MENU, lambda e: self.main_window.on_add_torrent(), ids["CTRL_T"])
        self.Bind(wx.EVT_MENU, lambda e: self.main_window.on_remove_selected(), ids["DELETE"])
        self.Bind(wx.EVT_MENU, lambda e: self.main_window.on_stop_continue_selected(), ids["CTRL_P"])
        self.Bind(wx.EVT_MENU, lambda e: self.main_window.refresh_torrents(), ids["F5"])
        self.Bind(wx.EVT_MENU, lambda e: self.main_window.on_open_torrent_file(), ids["CTRL_O"])
        self.Bind(wx.EVT_MENU, lambda e: self.main_window.on_speed_limits(), ids["CTRL_L"])
        self.Bind(wx.EVT_MENU, lambda e: self._on_detail_shortcut(), ids["D"])

    # ── Filtro ──────────────────────────────────────────────────────────────

    def _on_filter_changed(self, event):
        self._filter = self._filter_rb.GetSelection()
        self._rebuild_list()

    def _filter_rows(self):
        """Aplica o filtro atual na lista de rows."""
        if self._filter == FILTER_ALL:
            return list(self._rows)

        filtered = []
        for r in self._rows:
            if self._filter == FILTER_DOWNLOADING:
                # Baixando: estado downloading, não paused, não stopped, não finished, não seeding
                if r.state == 3 and not r.paused and not r.stopped and not r.is_finished:
                    filtered.append(r)
            elif self._filter == FILTER_SEEDING:
                # Semeando: estado seeding
                if r.state == 5:
                    filtered.append(r)
            elif self._filter == FILTER_PAUSED:
                # Parados: paused ou stopped
                if r.paused or r.stopped:
                    filtered.append(r)
            elif self._filter == FILTER_FINISHED:
                # Finalizados: is_finished
                if r.is_finished:
                    filtered.append(r)
        return filtered

    # ── Ordenação ──────────────────────────────────────────────────────────

    def _on_col_click(self, event):
        col = event.GetColumn()
        if col == self._sort_col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._rebuild_list()

    def _rebuild_list(self):
        """Reconstrói a lista com filtro + ordenação."""
        filtered = self._filter_rows()
        reverse = not self._sort_asc
        filtered.sort(
            key=lambda r: r.get_sort_value(self._sort_col),
            reverse=reverse,
        )
        self._filtered_rows = filtered

        i18n = self.main_window.i18n

        self.torrents_list.Freeze()
        self.torrents_list.DeleteAllItems()

        for row in filtered:
            self.torrents_list.Append([
                row.name,
                format_size(row.size) if row.size > 0 else "—",
                format_percent(row.progress),
                i18n.t(row.status),
                format_speed(row.download_rate),
                format_speed(row.upload_rate),
                format_eta(row.eta),
                str(row.seeds),
                str(row.peers),
                format_ratio(row.upload_rate, row.download_rate) if row.download_rate > 0 else "—",
            ])

        self.torrents_list.Thaw()

        # Atualiza painel de detalhes se tinha algo selecionado
        if self._selected_hash:
            found = any(r.info_hash == self._selected_hash for r in filtered)
            if not found:
                self._selected_hash = ""
                self._clear_detail_panel()

    # ── Eventos da lista ────────────────────────────────────────────────────

    def _on_torrent_activated(self, event):
        """Enter / duplo clique → abre detalhes."""
        idx = event.GetIndex()
        info_hash = self._get_hash_at(idx)
        if info_hash:
            self.main_window.show_torrent_detail(info_hash)

    def _on_torrent_selected(self, event):
        """Selecionou um torrent → atualiza painel de detalhes e botão."""
        idx = event.GetIndex()
        info_hash = self._get_hash_at(idx)
        if info_hash:
            self._selected_hash = info_hash
            entry = self.main_window.engine.get_torrent(info_hash)
            if entry:
                self._last_announced_pct = int(entry.progress * 100)
                # Anuncia progresso inicial
                self.main_window.output(
                    f"{entry.name}: {format_percent(entry.progress)} — "
                    f"{format_speed(entry.download_rate)} / {format_speed(entry.upload_rate)}",
                    interrupt=True
                )
            else:
                self._last_announced_pct = 0
            self._update_detail_panel(info_hash)
            self._update_action_btn_label(info_hash)

    def _on_torrent_focused(self, event):
        """Foco por teclado → anuncia para leitor de tela."""
        idx = event.GetIndex()
        info_hash = self._get_hash_at(idx)
        if info_hash and self.main_window.output:
            entry = self.main_window.engine.get_torrent(info_hash)
            if entry:
                self.main_window.output(
                    f"{entry.name}: {format_percent(entry.progress)} — "
                    f"{format_speed(entry.download_rate)} / {format_speed(entry.upload_rate)}",
                    interrupt=False,
                )

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
        item_action = menu.Append(wx.ID_ANY, i18n.t("stop_continue"))
        item_remove = menu.Append(wx.ID_ANY, i18n.t("remove_torrent"))

        menu.Bind(wx.EVT_MENU, lambda e: self.main_window.show_torrent_detail(info_hash), id=item_detail.GetId())
        menu.Bind(wx.EVT_MENU, lambda e: self.main_window.on_stop_continue_selected(), id=item_action.GetId())
        menu.Bind(wx.EVT_MENU, lambda e: self.main_window.on_remove_selected(), id=item_remove.GetId())

        self.PopupMenu(menu)
        menu.Destroy()

    def _on_list_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            idx = self.torrents_list.GetFocusedItem()
            if idx >= 0:
                class _M:
                    def GetIndex(self): return idx
                self._on_torrent_activated(_M())
        elif event.GetKeyCode() == ord("D"):
            self._on_detail_shortcut()
        else:
            event.Skip()

    def _on_detail_button(self, event):
        """Botão detalhes → abre diálogo."""
        if self._selected_hash:
            self.main_window.show_torrent_detail(self._selected_hash)

    def _on_detail_shortcut(self):
        """Atalho 'd' → abre detalhes do selecionado."""
        if self._selected_hash:
            self.main_window.show_torrent_detail(self._selected_hash)
        else:
            # Pega o primeiro item focado
            idx = self.torrents_list.GetFocusedItem()
            if idx >= 0:
                info_hash = self._get_hash_at(idx)
                if info_hash:
                    self.main_window.show_torrent_detail(info_hash)

    def _on_deselect(self, event):
        """Limpa seleção."""
        self._selected_hash = ""
        self._last_announced_pct = 0
        self._clear_detail_panel()
        self.action_btn.SetLabel(self.main_window.i18n.t("action_stop"))
        self.torrents_list.Select(-1, on=0)

    # ── Painel de detalhes ─────────────────────────────────────────────────

    def _update_action_btn_label(self, info_hash):
        """Atualiza o rótulo do botão parar/continuar conforme o estado."""
        entry = self.main_window.engine.get_torrent(info_hash)
        if entry:
            i18n = self.main_window.i18n
            if entry.paused or entry.stopped:
                self.action_btn.SetLabel(i18n.t("action_continue"))
            else:
                self.action_btn.SetLabel(i18n.t("action_stop"))

    def _clear_detail_panel(self):
        """Limpa o painel de detalhes inferior."""
        self.info_label.SetLabel("")

    def _update_detail_panel(self, info_hash):
        """Atualiza info label e anuncia progresso."""
        entry = self.main_window.engine.get_torrent(info_hash)
        if not entry:
            self._clear_detail_panel()
            return

        i18n = self.main_window.i18n

        # Anunciar progresso
        interval = settings.get_setting("general", "progress_announce_interval", default=10)
        current_pct = int(entry.progress * 100)
        current_bucket = current_pct // interval
        last_bucket = self._last_announced_pct // interval
        if current_bucket > last_bucket:
            self._last_announced_pct = current_pct
            text = f"{entry.name}: {format_percent(entry.progress)}"
            self.main_window.output(text, interrupt=True)

        # Info label — formato limpo para leitores de tela
        text = (
            f"{entry.name}; "
            f"{i18n.t('torrent_size')}: {format_size(entry.size) if entry.size > 0 else '—'}; "
            f"{i18n.t('torrent_progress')}: {format_percent(entry.progress)}; "
            f"{i18n.t('torrent_status')}: {i18n.t(entry.state_str)}; "
            f"{i18n.t('torrent_download')}: {format_speed(entry.download_rate)}; "
            f"{i18n.t('torrent_upload')}: {format_speed(entry.upload_rate)}; "
            f"{i18n.t('torrent_eta')}: {format_eta(entry.eta)}; "
            f"{i18n.t('torrent_seeds')}: {entry.num_seeds}/{entry.total_seeds}; "
            f"{i18n.t('torrent_peers')}: {entry.num_peers}/{entry.total_peers}; "
            f"{i18n.t('torrent_ratio')}: {format_ratio(entry.total_upload, entry.total_download)}"
        )
        self.info_label.SetLabel(text)

    # ── Refresh ────────────────────────────────────────────────────────────

    def refresh(self):
        """Atualiza dados do engine e reconstrói a lista."""
        engine = self.main_window.engine
        if not engine:
            return

        torrents = engine.get_torrents()
        i18n = self.main_window.i18n

        self._rows = []
        for entry in torrents:
            row = TorrentRow(
                info_hash=entry.info_hash,
                name=entry.name,
                size=entry.size,
                progress=entry.progress,
                status=entry.state_str,
                download_rate=entry.download_rate,
                upload_rate=entry.upload_rate,
                eta=entry.eta if entry.eta >= 0 else -1,
                seeds=entry.num_seeds,
                peers=entry.num_peers,
                ratio=(entry.total_upload / max(entry.total_download, 1)),
                state=entry.state,
                paused=entry.paused,
                stopped=entry.stopped,
                is_finished=entry.is_finished,
            )
            self._rows.append(row)

        self._rebuild_list()

        # Atualiza painel de detalhes e botão se ainda existe
        if self._selected_hash:
            found = any(True for r in self._filtered_rows if r.info_hash == self._selected_hash)
            if found:
                self._update_detail_panel(self._selected_hash)
                self._update_action_btn_label(self._selected_hash)
            else:
                self._selected_hash = ""
                self._clear_detail_panel()

    def _get_hash_at(self, row):
        if 0 <= row < len(self._filtered_rows):
            return self._filtered_rows[row].info_hash
        return ""

    def _on_timer_tick(self, event):
        if self.IsShown():
            self.refresh()
