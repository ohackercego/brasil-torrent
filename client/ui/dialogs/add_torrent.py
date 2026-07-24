"""
Diálogo para adicionar torrent via arquivo .torrent ou magnet link.

Inspirado nos diálogos modais do WinZapp (Connect, Settings).
Usa wx.Dialog com wx.TextCtrl, wx.FilePicker, wx.Button padrão —
totalmente acessível a leitores de tela.
"""

import os
import wx


class AddTorrentDialog(wx.Dialog):
    """Diálogo modal para adicionar um novo torrent."""

    def __init__(self, parent):
        self.main_window = parent
        i18n = self.main_window.i18n
        super().__init__(
            parent,
            title=i18n.t("add_torrent_title"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._build_ui()
        self.SetSize((480, -1))
        self.Centre()
        self._magnet_field.SetFocus()

    def _build_ui(self):
        i18n = self.main_window.i18n
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # ── Abas ─────────────────────────────────────────────────────────────
        notebook = wx.Notebook(panel)

        # ── Aba Magnet Link ─────────────────────────────────────────────────
        magnet_page = wx.Panel(notebook)
        mag_sizer = wx.BoxSizer(wx.VERTICAL)

        mag_sizer.Add(
            wx.StaticText(magnet_page, label=i18n.t("magnet_instruction")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._magnet_field = wx.TextCtrl(
            magnet_page,
            style=wx.TE_MULTILINE | wx.TE_DONTWRAP,
        )
        mag_sizer.Add(self._magnet_field, 1, wx.EXPAND | wx.ALL, 8)

        magnet_page.SetSizer(mag_sizer)
        notebook.AddPage(magnet_page, i18n.t("tab_magnet"))

        # ── Aba Arquivo .torrent ───────────────────────────────────────────
        file_page = wx.Panel(notebook)
        file_sizer = wx.BoxSizer(wx.VERTICAL)

        file_sizer.Add(
            wx.StaticText(file_page, label=i18n.t("torrent_file_instruction")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )

        file_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._file_path_field = wx.TextCtrl(file_page, style=wx.TE_DONTWRAP | wx.TE_READONLY)
        file_btn_sizer.Add(self._file_path_field, 1, wx.EXPAND | wx.RIGHT, 5)

        self._browse_btn = wx.Button(file_page, label=i18n.t("browse"))
        self._browse_btn.Bind(wx.EVT_BUTTON, self._on_browse)
        file_btn_sizer.Add(self._browse_btn, 0)
        file_sizer.Add(file_btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

        file_page.SetSizer(file_sizer)
        notebook.AddPage(file_page, i18n.t("tab_file"))

        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)

        # ── Save path ──────────────────────────────────────────────────────
        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        path_sizer.Add(
            wx.StaticText(panel, label=i18n.t("save_path")),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5,
        )
        default_path = self.main_window.download_path
        self._save_path_field = wx.TextCtrl(
            panel, style=wx.TE_DONTWRAP,
            value=default_path,
        )
        path_sizer.Add(self._save_path_field, 1, wx.EXPAND | wx.RIGHT, 5)
        self._browse_path_btn = wx.Button(panel, label=i18n.t("browse"))
        self._browse_path_btn.Bind(wx.EVT_BUTTON, self._on_browse_save_path)
        path_sizer.Add(self._browse_path_btn, 0)
        sizer.Add(path_sizer, 0, wx.EXPAND | wx.ALL, 8)

        # ── Opções ─────────────────────────────────────────────────────────
        options_box = wx.StaticBox(panel, label=i18n.t("options"))
        options_sizer = wx.StaticBoxSizer(options_box, wx.VERTICAL)

        self._sequential_check = wx.CheckBox(
            options_box, label=i18n.t("sequential_download")
        )
        options_sizer.Add(self._sequential_check, 0, wx.ALL, 5)

        sizer.Add(options_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ── Botões ─────────────────────────────────────────────────────────
        btn_sizer = wx.StdDialogButtonSizer()
        self._ok_btn = wx.Button(panel, wx.ID_OK, label=i18n.t("add"))
        self._cancel_btn = wx.Button(panel, wx.ID_CANCEL, label=i18n.t("cancel"))
        btn_sizer.AddButton(self._ok_btn)
        btn_sizer.AddButton(self._cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        panel.SetSizer(sizer)

        self._ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        self._cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_browse(self, event):
        """Abre seletor de arquivo .torrent."""
        i18n = self.main_window.i18n
        wildcard = f"{i18n.t('torrent_files')} (*.torrent)|*.torrent|{i18n.t('all_files')} (*.*)|*.*"
        dlg = wx.FileDialog(
            self,
            message=i18n.t("select_torrent_file"),
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self._file_path_field.SetValue(dlg.GetPath())
        dlg.Destroy()

    def _on_browse_save_path(self, event):
        """Abre seletor de diretório para salvar."""
        i18n = self.main_window.i18n
        dlg = wx.DirDialog(
            self,
            message=i18n.t("select_save_path"),
            style=wx.DD_DEFAULT_STYLE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self._save_path_field.SetValue(dlg.GetPath())
        dlg.Destroy()

    def _on_ok(self, event):
        """Valida e adiciona o torrent."""
        magnet = self._magnet_field.GetValue().strip()
        filepath = self._file_path_field.GetValue().strip()
        save_path = self._save_path_field.GetValue().strip()

        if not magnet and not filepath:
            i18n = self.main_window.i18n
            wx.MessageBox(
                i18n.t("add_torrent_empty_error"),
                i18n.t("error_generic"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        if not save_path or not os.path.isdir(save_path):
            i18n = self.main_window.i18n
            wx.MessageBox(
                i18n.t("invalid_save_path"),
                i18n.t("error_generic"),
                wx.OK | wx.ICON_WARNING,
                self,
            )
            return

        self.EndModal(wx.ID_OK)

    # ── Propriedades ─────────────────────────────────────────────────────────

    @property
    def magnet_link(self) -> str:
        return self._magnet_field.GetValue().strip()

    @property
    def torrent_file(self) -> str:
        return self._file_path_field.GetValue().strip()

    @property
    def save_path(self) -> str:
        return self._save_path_field.GetValue().strip()

    @property
    def sequential_download(self) -> bool:
        return self._sequential_check.GetValue()
