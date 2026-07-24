"""
Diálogo de detalhes do torrent com TreeCtrl de arquivos
e informações completas.

Navegável totalmente por teclado (setas, Tab, Enter, Esc).
"""

import wx
import threading
from config import settings
from core.utils import format_size, format_speed, format_eta, format_percent, format_ratio


class TorrentDetailDialog(wx.Dialog):
    """Detalhes completos de um torrent com árvore de arquivos."""

    def __init__(self, parent, info_hash: str):
        self.main_window = parent
        self._info_hash = info_hash
        i18n = self.main_window.i18n
        super().__init__(
            parent,
            title=i18n.t("torrent_detail"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer_tick, self._update_timer)
        self._last_announced_pct = 0
        self._metadata_loaded = False
        self._build_ui()
        self._load_data()
        self.SetSize((600, 550))
        self.SetMinSize((400, 350))
        self.Centre()
        self._update_timer.Start(3000)

    def _build_ui(self):
        i18n = self.main_window.i18n
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ── Informações principais ──────────────────────────────────────────
        info_box = wx.StaticBox(panel, label=i18n.t("general_info"))
        info_sizer = wx.StaticBoxSizer(info_box, wx.VERTICAL)

        self._name_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._name_lbl, 0, wx.ALL, 4)

        self._hash_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._hash_lbl, 0, wx.ALL, 4)

        self._size_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._size_lbl, 0, wx.ALL, 4)

        self._progress_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._progress_lbl, 0, wx.ALL, 4)

        self._status_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._status_lbl, 0, wx.ALL, 4)

        speed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._down_lbl = wx.StaticText(info_box, label="")
        speed_sizer.Add(self._down_lbl, 0, wx.RIGHT, 15)
        self._up_lbl = wx.StaticText(info_box, label="")
        speed_sizer.Add(self._up_lbl, 0)
        info_sizer.Add(speed_sizer, 0, wx.ALL, 4)

        peers_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._seeds_lbl = wx.StaticText(info_box, label="")
        peers_sizer.Add(self._seeds_lbl, 0, wx.RIGHT, 15)
        self._peers_lbl = wx.StaticText(info_box, label="")
        peers_sizer.Add(self._peers_lbl, 0)
        info_sizer.Add(peers_sizer, 0, wx.ALL, 4)

        self._eta_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._eta_lbl, 0, wx.ALL, 4)

        self._ratio_lbl = wx.StaticText(info_box, label="")
        info_sizer.Add(self._ratio_lbl, 0, wx.ALL, 4)

        sizer.Add(info_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # ── TreeCtrl de arquivos ────────────────────────────────────────────
        files_box = wx.StaticBox(panel, label=i18n.t("file_info"))
        files_sizer = wx.StaticBoxSizer(files_box, wx.VERTICAL)

        self.files_tree = wx.TreeCtrl(
            files_box,
            style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT,
        )
        self.files_tree.SetMinSize((-1, 120))
        files_sizer.Add(self.files_tree, 1, wx.EXPAND | wx.ALL, 5)

        sizer.Add(files_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # ── Botões ──────────────────────────────────────────────────────────
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.open_folder_btn = wx.Button(panel, label=i18n.t("open_folder"))
        self.open_folder_btn.Bind(wx.EVT_BUTTON, self._on_open_folder)
        btn_sizer.Add(self.open_folder_btn, 0, wx.RIGHT, 5)

        self.action_btn = wx.Button(panel, label=i18n.t("action_stop"))
        self.action_btn.Bind(wx.EVT_BUTTON, self._on_stop_continue)
        btn_sizer.Add(self.action_btn, 0, wx.RIGHT, 5)

        self.remove_btn = wx.Button(panel, label=i18n.t("remove_torrent"))
        self.remove_btn.Bind(wx.EVT_BUTTON, self._on_remove)
        btn_sizer.Add(self.remove_btn, 0, wx.RIGHT, 5)

        close_btn = wx.Button(panel, wx.ID_CLOSE, label=i18n.t("close"))
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        btn_sizer.Add(close_btn, 0)

        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 8)

        panel.SetSizer(sizer)

        # Atalho: Esc fecha
        self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)
        close_btn.SetFocus()

    # ── Carregar dados ─────────────────────────────────────────────────────

    def _load_data(self):
        """Carrega dados do torrent e arquivos."""
        entry = self.main_window.engine.get_torrent(self._info_hash)
        if not entry:
            return
        self._update_info(entry)
        self._load_files(entry)

    def _update_info(self, entry):
        """Atualiza campos de texto."""
        i18n = self.main_window.i18n
        if not entry:
            return

        self._name_lbl.SetLabel(f"{entry.name}")
        self._hash_lbl.SetLabel(f"{i18n.t('torrent_hash')}: {entry.info_hash}")
        self._size_lbl.SetLabel(f"{i18n.t('torrent_size')}: {format_size(entry.size) if entry.size > 0 else '—'}")
        self._progress_lbl.SetLabel(
            f"{i18n.t('torrent_progress')}: {format_percent(entry.progress)} "
            f"({format_size(entry.total_download)} / {format_size(entry.size)})"
        )
        self._status_lbl.SetLabel(f"{i18n.t('torrent_status')}: {i18n.t(entry.state_str)}")
        self._down_lbl.SetLabel(f"↓ {format_speed(entry.download_rate)}")
        self._up_lbl.SetLabel(f"↑ {format_speed(entry.upload_rate)}")
        self._seeds_lbl.SetLabel(f"{i18n.t('torrent_seeds')}: {entry.num_seeds} ({i18n.t('total')}: {entry.total_seeds})")
        self._peers_lbl.SetLabel(f"{i18n.t('torrent_peers')}: {entry.num_peers} ({i18n.t('total')}: {entry.total_peers})")
        self._eta_lbl.SetLabel(f"{i18n.t('torrent_eta')}: {format_eta(entry.eta)}")
        self._ratio_lbl.SetLabel(
            f"{i18n.t('torrent_ratio')}: {format_ratio(entry.total_upload, entry.total_download)}"
        )

        # Anunciar progresso
        interval = settings.get_setting("general", "progress_announce_interval", default=10)
        current_pct = int(entry.progress * 100)
        current_bucket = current_pct // interval
        last_bucket = self._last_announced_pct // interval
        if current_bucket > last_bucket:
            self._last_announced_pct = current_pct
            self.main_window.output(
                f"{entry.name}: {format_percent(entry.progress)}",
                interrupt=True
            )

        # Texto do botão parar/continuar
        if entry.paused or entry.stopped:
            self.action_btn.SetLabel(i18n.t("action_continue"))
        else:
            self.action_btn.SetLabel(i18n.t("action_stop"))

    def _load_files(self, entry):
        """Carrega árvore de arquivos do torrent com nome, tamanho e progresso em nós separados."""
        import logging
        logger = logging.getLogger(__name__)
        self.files_tree.DeleteAllItems()
        root = self.files_tree.AddRoot("")

        handle_valid = entry.handle is not None and entry.handle.is_valid() if entry.handle else False
        logger.debug(f"_load_files: handle={entry.handle is not None}, is_valid={handle_valid}, "
                     f"metadata_loaded={self._metadata_loaded}")
        if not entry.handle or not entry.handle.is_valid():
            self.files_tree.AppendItem(root, self.main_window.i18n.t("file_metadata_pending"))
            self._metadata_loaded = False
            return

        try:
            ti = entry.handle.torrent_file()
            num_files = ti.num_files()
            if num_files == 0:
                self.files_tree.AppendItem(root, self.main_window.i18n.t("no_file_info"))
                self._metadata_loaded = True
            else:
                file_tree = {}
                for i in range(num_files):
                    f = ti.file_at(i)
                    path = ti.orig_files().file_path(i) if hasattr(ti, 'orig_files') else ti.file_at(i).path
                    file_path = path.replace("\\", "/")
                    fsize = f.size
                    file_tree[file_path] = fsize

                file_progress = {}
                try:
                    fp = entry.handle.file_progress()
                    for i, p in enumerate(fp):
                        file_path = list(file_tree.keys())[i]
                        file_progress[file_path] = p
                except Exception:
                    pass

                dir_nodes = []
                sorted_paths = sorted(file_tree.keys())
                tree_map = {}
                tree_map[""] = root
                i18n = self.main_window.i18n

                for fpath in sorted_paths:
                    parts = fpath.split("/")
                    current_path = ""
                    parent_node = root
                    for i, part in enumerate(parts):
                        if current_path:
                            current_path += "/" + part
                        else:
                            current_path = part

                        if current_path not in tree_map:
                            if i == len(parts) - 1:
                                fsize = file_tree.get(fpath, 0)
                                p = file_progress.get(fpath, 0)
                                pct = (p / fsize * 100) if fsize > 0 else 0
                                node = self.files_tree.AppendItem(parent_node, part)
                                self.files_tree.AppendItem(node, f"{i18n.t('torrent_size')}: {format_size(fsize)}")
                                self.files_tree.AppendItem(node, f"{i18n.t('torrent_progress')}: {pct:.1f}%")
                                self.files_tree.Expand(node)
                            else:
                                node = self.files_tree.AppendItem(parent_node, f"{part}")
                                dir_nodes.append(node)
                            tree_map[current_path] = node
                        parent_node = tree_map[current_path]

                for dnode in dir_nodes:
                    self.files_tree.Expand(dnode)

            self._metadata_loaded = True
            logger.debug(f"_load_files: loaded {num_files} files successfully")

        except Exception as e:
            logger.debug(f"_load_files: exception ({e}) — metadata still pending")
            self.files_tree.DeleteAllItems()
            self.files_tree.AppendItem(root, self.main_window.i18n.t("file_metadata_pending"))
            self._metadata_loaded = False

    # ── Handlers ──────────────────────────────────────────────────────────

    def _on_char_hook(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()

    def _on_open_folder(self, event):
        """Abre a pasta de destino no explorer."""
        entry = self.main_window.engine.get_torrent(self._info_hash)
        if entry and entry.save_path:
            import subprocess
            try:
                subprocess.Popen(["explorer", entry.save_path])
            except Exception:
                pass

    def _on_stop_continue(self, event):
        """Para ou continua o torrent."""
        entry = self.main_window.engine.get_torrent(self._info_hash)
        if entry:
            if entry.paused or entry.stopped:
                self.main_window.engine.resume_torrent(self._info_hash)
            else:
                self.main_window.engine.stop_torrent(self._info_hash)
            # Atualiza imediatamente o rótulo do botão e demais info
            self._update_info(self.main_window.engine.get_torrent(self._info_hash))

    def _on_remove(self, event):
        """Remove o torrent."""
        i18n = self.main_window.i18n
        entry = self.main_window.engine.get_torrent(self._info_hash)
        if not entry:
            return
        dlg = wx.MessageDialog(
            self,
            f"{i18n.t('confirm_remove_message')}\n\n{entry.name}",
            i18n.t("confirm_remove_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        if dlg.ShowModal() == wx.ID_YES:
            self.main_window.engine.remove_torrent(self._info_hash)
            self.Close()
        dlg.Destroy()

    # ── Timer ─────────────────────────────────────────────────────────────

    def _on_timer_tick(self, event):
        """Atualiza dados periodicamente."""
        entry = self.main_window.engine.get_torrent(self._info_hash)
        if entry:
            self._update_info(entry)
            if not self._metadata_loaded:
                self._load_files(entry)

    def Close(self, force=False):
        self._update_timer.Stop()
        try:
            self.EndModal(wx.ID_CLOSE)
        except Exception:
            pass
        super().Close(force)
