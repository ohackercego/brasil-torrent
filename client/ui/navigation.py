"""
Painel de navegação principal do Brasil Torrent.

Inspirado no NavigationPanel do WinZapp: usa wx.ListCtrl puro para
garantir acessibilidade total com NVDA/JAWS/Narrator.

Itens de navegação:
  0 - Transferências (Alt+1)
  1 - Concluídos
  2 - Configurações (Alt+3)
"""

import wx
from ui.accessible import AccessibleNavList


class NavigationPanel(wx.Panel):
    """Painel lateral de navegação entre as seções do aplicativo."""

    def __init__(self, main_window, parent):
        super().__init__(parent)
        self.main_window = main_window
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Rótulo
        self.nav_label = wx.StaticText(
            self, label=self.main_window.i18n.t("main_nav")
        )
        sizer.Add(self.nav_label, 0, wx.LEFT | wx.TOP, 5)

        # Lista de navegação
        i18n = self.main_window.i18n
        self.nav_list = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.nav_list.InsertColumn(0, i18n.t("main_nav"), width=180)
        self.nav_list.SetAccessible(AccessibleNavList(i18n.t("main_nav")))

        # Índice 0: Transferências  |  Índice 1: Concluídos  |  Índice 2: Configurações
        self.nav_list.Append([f"{i18n.t('nav_transfers')} Alt+1"])
        self.nav_list.Append([i18n.t("nav_completed")])
        self.nav_list.Append([f"{i18n.t('nav_settings')} Alt+3"])

        self.nav_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_nav_item_activated)
        self.nav_list.Bind(wx.EVT_KEY_DOWN, self._on_nav_key_down)
        self.nav_list.Focus(0)
        self.nav_list.Select(0)

        sizer.Add(self.nav_list, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

    def refresh_labels(self):
        """Atualiza os textos após mudança de idioma."""
        i18n = self.main_window.i18n
        self.nav_label.SetLabel(i18n.t("main_nav"))
        col = wx.ListItem()
        col.SetText(i18n.t("main_nav"))
        self.nav_list.SetColumn(0, col)
        self.nav_list.SetItemText(0, f"{i18n.t('nav_transfers')} Alt+1")
        self.nav_list.SetItemText(1, i18n.t("nav_completed"))
        self.nav_list.SetItemText(2, f"{i18n.t('nav_settings')} Alt+3")

    def _on_nav_key_down(self, event):
        """Espaço ativa o item focado (igual ao Enter)."""
        if event.GetKeyCode() == wx.WXK_SPACE:
            idx = self.nav_list.GetFocusedItem()
            if idx >= 0:
                self.nav_list.Select(idx)
                class _MockEvent:
                    def GetIndex(self):
                        return idx
                self.on_nav_item_activated(_MockEvent())
        else:
            event.Skip()

    def on_nav_item_activated(self, event):
        """Manipula a seleção de um item de navegação."""
        index = event.GetIndex()
        mw = self.main_window

        if index == 2:  # Configurações
            mw.open_settings()
            return

        # Mostra/esconde painéis
        mw.transfers_panel.Hide()
        if hasattr(mw, "completed_panel"):
            mw.completed_panel.Hide()

        if index == 0:  # Transferências
            mw.transfers_panel.Show()
            mw.content_panel.Layout()
            mw.transfers_panel.torrents_list.SetFocus()
            mw.announce_focused_torrent()

        elif index == 1:  # Concluídos
            if hasattr(mw, "completed_panel"):
                mw.completed_panel.Show()
                mw.content_panel.Layout()
                mw.completed_panel.torrents_list.SetFocus()
