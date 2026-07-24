import wx
import wx.adv


class BrasilTorrentTrayIcon(wx.adv.TaskBarIcon):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        icon = self._create_icon()
        self.SetIcon(icon, main_window.i18n.t("app_name"))
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self._on_restore)
        self.Bind(wx.adv.EVT_TASKBAR_RIGHT_UP, self._on_menu)

    def _create_icon(self):
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_OTHER, (16, 16)))
        return icon

    def _on_restore(self, event):
        self.main_window.Show(True)
        self.main_window.Raise()
        self.main_window.SetFocus()

    def _on_menu(self, event):
        i18n = self.main_window.i18n
        menu = wx.Menu()
        restore = menu.Append(wx.ID_ANY, i18n.t("restore"))
        menu.AppendSeparator()
        exit_item = menu.Append(wx.ID_ANY, i18n.t("menu_file_exit"))
        self.Bind(wx.EVT_MENU, lambda e: self._on_restore(None), restore)
        self.Bind(wx.EVT_MENU, lambda e: self._on_exit(), exit_item)
        self.PopupMenu(menu)
        menu.Destroy()

    def _on_exit(self):
        self.main_window.Close()

    def __del__(self):
        self.RemoveIcon()
