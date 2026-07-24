"""
Diálogo de configurações do Brasil Torrent.

Inspirado no SettingsDialog do WinZapp: usa wx.Notebook com abas
e controles wx padrão para total acessibilidade com leitores de tela.
"""

import os
import wx
from config import settings


class SettingsDialog(wx.Dialog):
    """Configurações com abas: Geral, Conexão, Privacidade."""

    def __init__(self, parent):
        self.main_window = parent
        i18n = self.main_window.i18n
        super().__init__(
            parent,
            title=i18n.t("settings_title"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._build_ui()
        self._load_values()
        self.Fit()
        self.SetMinSize((460, 400))
        self.Centre()

    def _build_ui(self):
        i18n = self.main_window.i18n
        notebook = wx.Notebook(self)

        # ── Aba Geral ────────────────────────────────────────────────────────
        general = wx.Panel(notebook)
        gen_sizer = wx.BoxSizer(wx.VERTICAL)

        gen_sizer.Add(
            wx.StaticText(general, label=i18n.t("language_label")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._lang_combo = wx.ComboBox(general, style=wx.CB_READONLY)
        gen_sizer.Add(self._lang_combo, 0, wx.EXPAND | wx.ALL, 8)

        gen_sizer.Add(
            wx.StaticText(general, label=i18n.t("download_path_label")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._download_path_field = wx.TextCtrl(general, style=wx.TE_DONTWRAP)
        path_sizer.Add(self._download_path_field, 1, wx.EXPAND | wx.RIGHT, 5)
        browse_btn = wx.Button(general, label=i18n.t("browse"))
        browse_btn.Bind(wx.EVT_BUTTON, self._on_browse_download_path)
        path_sizer.Add(browse_btn, 0)
        gen_sizer.Add(path_sizer, 0, wx.EXPAND | wx.ALL, 8)

        gen_sizer.Add(
            wx.StaticText(general, label=i18n.t("max_active_downloads")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._max_downloads_spin = wx.SpinCtrl(general, min=1, max=50, initial=5)
        gen_sizer.Add(self._max_downloads_spin, 0, wx.ALL, 8)

        gen_sizer.Add(
            wx.StaticText(general, label=i18n.t("max_active_uploads")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._max_uploads_spin = wx.SpinCtrl(general, min=1, max=50, initial=5)
        gen_sizer.Add(self._max_uploads_spin, 0, wx.ALL, 8)

        gen_sizer.Add(
            wx.StaticText(general, label=i18n.t("min_ratio_label")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._min_ratio_spin = wx.SpinCtrl(general, min=0, max=100, initial=10)
        gen_sizer.Add(self._min_ratio_spin, 0, wx.ALL, 8)

        gen_sizer.Add(
            wx.StaticText(general, label=i18n.t("progress_announce_label")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._progress_announce_spin = wx.SpinCtrl(general, min=1, max=100, initial=10)
        gen_sizer.Add(self._progress_announce_spin, 0, wx.ALL, 8)

        self._auto_start_check = wx.CheckBox(general, label=i18n.t("auto_start"))
        gen_sizer.Add(self._auto_start_check, 0, wx.ALL, 8)

        self._minimize_tray_check = wx.CheckBox(general, label=i18n.t("minimize_to_tray"))
        gen_sizer.Add(self._minimize_tray_check, 0, wx.ALL, 8)

        self._notifications_check = wx.CheckBox(general, label=i18n.t("notifications_label"))
        gen_sizer.Add(self._notifications_check, 0, wx.ALL, 8)

        general.SetSizer(gen_sizer)
        notebook.AddPage(general, i18n.t("tab_general"))

        # ── Aba Conexão ──────────────────────────────────────────────────────
        conn = wx.Panel(notebook)
        conn_sizer = wx.BoxSizer(wx.VERTICAL)

        conn_sizer.Add(
            wx.StaticText(conn, label=i18n.t("max_upload_rate")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._max_upload_spin = wx.SpinCtrl(conn, min=0, max=100000, initial=0)
        conn_sizer.Add(self._max_upload_spin, 0, wx.ALL, 8)

        conn_sizer.Add(
            wx.StaticText(conn, label=i18n.t("max_download_rate")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._max_download_spin = wx.SpinCtrl(conn, min=0, max=100000, initial=0)
        conn_sizer.Add(self._max_download_spin, 0, wx.ALL, 8)

        conn_sizer.Add(
            wx.StaticText(conn, label=i18n.t("max_connections")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._max_conn_spin = wx.SpinCtrl(conn, min=10, max=500, initial=200)
        conn_sizer.Add(self._max_conn_spin, 0, wx.ALL, 8)

        conn_sizer.Add(
            wx.StaticText(conn, label=i18n.t("listen_port")),
            0, wx.LEFT | wx.TOP | wx.RIGHT, 8,
        )
        self._port_spin = wx.SpinCtrl(conn, min=1024, max=65535, initial=6881)
        conn_sizer.Add(self._port_spin, 0, wx.ALL, 8)

        self._dht_check = wx.CheckBox(conn, label=i18n.t("enable_dht"))
        conn_sizer.Add(self._dht_check, 0, wx.ALL, 8)

        self._upnp_check = wx.CheckBox(conn, label=i18n.t("enable_upnp"))
        conn_sizer.Add(self._upnp_check, 0, wx.ALL, 8)

        conn.SetSizer(conn_sizer)
        notebook.AddPage(conn, i18n.t("tab_connection"))

        # ── Aba Privacidade ─────────────────────────────────────────────────
        privacy = wx.Panel(notebook)
        priv_sizer = wx.BoxSizer(wx.VERTICAL)

        self._anonymous_check = wx.CheckBox(
            privacy, label=i18n.t("anonymous_mode")
        )
        priv_sizer.Add(self._anonymous_check, 0, wx.ALL, 8)

        privacy.SetSizer(priv_sizer)
        notebook.AddPage(privacy, i18n.t("tab_privacy"))

        # ── Botões ─────────────────────────────────────────────────────────
        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, label=i18n.t("ok"))
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label=i18n.t("cancel"))
        apply_btn = wx.Button(self, wx.ID_APPLY, label=i18n.t("apply"))
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.AddButton(apply_btn)
        btn_sizer.Realize()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.SetSizer(main_sizer)

        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        apply_btn.Bind(wx.EVT_BUTTON, self._on_apply)

    # ── Carregar / Salvar ────────────────────────────────────────────────────

    def _load_values(self):
        """Carrega valores atuais das configurações."""
        from core.i18n import LANGUAGE_NAMES
        self._lang_combo.Set(list(LANGUAGE_NAMES.values()))
        current_lang = settings.get_setting("general", "language", default="pt-BR")
        lang_labels = list(LANGUAGE_NAMES.values())
        lang_codes = list(LANGUAGE_NAMES.keys())
        if current_lang in lang_codes:
            idx = lang_codes.index(current_lang)
            self._lang_combo.SetSelection(idx)
        else:
            self._lang_combo.SetSelection(0)

        self._download_path_field.SetValue(
            settings.get_setting("general", "download_path", default="")
        )
        self._max_downloads_spin.SetValue(
            settings.get_setting("general", "max_active_downloads", default=5)
        )
        self._max_uploads_spin.SetValue(
            settings.get_setting("general", "max_active_uploads", default=5)
        )
        self._min_ratio_spin.SetValue(
            int(settings.get_setting("general", "min_ratio", default=1.0) * 10)
        )
        self._auto_start_check.SetValue(
            settings.get_setting("general", "auto_start", default=False)
        )
        self._minimize_tray_check.SetValue(
            settings.get_setting("general", "minimize_to_tray", default=True)
        )
        self._notifications_check.SetValue(
            settings.get_setting("general", "notifications_enabled", default=True)
        )
        self._progress_announce_spin.SetValue(
            settings.get_setting("general", "progress_announce_interval", default=10)
        )

        self._max_upload_spin.SetValue(
            settings.get_setting("connection", "max_upload_rate", default=0)
        )
        self._max_download_spin.SetValue(
            settings.get_setting("connection", "max_download_rate", default=0)
        )
        self._max_conn_spin.SetValue(
            settings.get_setting("connection", "max_connections", default=200)
        )
        self._port_spin.SetValue(
            settings.get_setting("connection", "listen_port", default=6881)
        )
        self._dht_check.SetValue(
            settings.get_setting("connection", "enable_dht", default=True)
        )
        self._upnp_check.SetValue(
            settings.get_setting("connection", "enable_upnp", default=True)
        )

        self._anonymous_check.SetValue(
            settings.get_setting("privacy", "anonymous_mode", default=False)
        )

    def _save_values(self):
        """Salva valores nos settings."""
        from core.i18n import LANGUAGE_NAMES
        lang_codes = list(LANGUAGE_NAMES.keys())
        sel = self._lang_combo.GetSelection()
        if 0 <= sel < len(lang_codes):
            settings["general"]["language"] = lang_codes[sel]

        settings["general"]["download_path"] = self._download_path_field.GetValue().strip()
        settings["general"]["max_active_downloads"] = self._max_downloads_spin.GetValue()
        settings["general"]["max_active_uploads"] = self._max_uploads_spin.GetValue()
        settings["general"]["min_ratio"] = self._min_ratio_spin.GetValue() / 10.0
        settings["general"]["auto_start"] = self._auto_start_check.GetValue()
        settings["general"]["minimize_to_tray"] = self._minimize_tray_check.GetValue()
        settings["general"]["notifications_enabled"] = self._notifications_check.GetValue()
        settings["general"]["progress_announce_interval"] = self._progress_announce_spin.GetValue()

        settings["connection"]["max_upload_rate"] = self._max_upload_spin.GetValue()
        settings["connection"]["max_download_rate"] = self._max_download_spin.GetValue()
        settings["connection"]["max_connections"] = self._max_conn_spin.GetValue()
        settings["connection"]["listen_port"] = self._port_spin.GetValue()
        settings["connection"]["enable_dht"] = self._dht_check.GetValue()
        settings["connection"]["enable_upnp"] = self._upnp_check.GetValue()

        settings["privacy"]["anonymous_mode"] = self._anonymous_check.GetValue()

        settings.save()

    def _on_browse_download_path(self, event):
        i18n = self.main_window.i18n
        dlg = wx.DirDialog(self, message=i18n.t("select_save_path"))
        if dlg.ShowModal() == wx.ID_OK:
            self._download_path_field.SetValue(dlg.GetPath())
        dlg.Destroy()

    def _on_apply(self, event):
        self._save_values()
        i18n = self.main_window.i18n
        wx.MessageBox(i18n.t("settings_saved"), i18n.t("settings_title"), wx.OK | wx.ICON_INFORMATION)

    def _on_ok(self, event):
        self._save_values()
        self.EndModal(wx.ID_OK)
