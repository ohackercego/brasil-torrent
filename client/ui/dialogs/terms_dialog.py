"""
Diálogo de Termos de Uso e Aviso de Responsabilidade.

Exibido na primeira execução do aplicativo.
O usuário deve aceitar os termos para continuar usando o programa.
"""

import wx


class TermsDialog(wx.Dialog):
    """Aviso inicial — isenção de responsabilidade sobre torrents baixados."""

    def __init__(self, parent, i18n):
        super().__init__(
            parent,
            title=i18n.t("terms_title"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._accepted = False
        self._build_ui(i18n)
        self.SetSize((520, 420))
        self.Centre()
        self._aceitar_btn.SetFocus()

    def _build_ui(self, i18n):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Título em destaque
        title = wx.StaticText(panel, label=i18n.t("terms_title"))
        font = title.GetFont()
        font.SetPointSize(font.GetPointSize() + 4)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        # Texto do aviso
        terms_text = i18n.t("terms_body")
        text_ctrl = wx.TextCtrl(
            panel,
            value=terms_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.BORDER_SUNKEN,
        )
        sizer.Add(text_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Botões
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddStretchSpacer()

        self._recusar_btn = wx.Button(panel, wx.ID_ANY, label=i18n.t("terms_decline"))
        self._recusar_btn.Bind(wx.EVT_BUTTON, self._on_decline)
        btn_sizer.Add(self._recusar_btn, 0, wx.RIGHT, 10)

        self._aceitar_btn = wx.Button(panel, wx.ID_ANY, label=i18n.t("terms_accept"))
        self._aceitar_btn.Bind(wx.EVT_BUTTON, self._on_accept)
        btn_sizer.Add(self._aceitar_btn, 0)

        sizer.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(sizer)

    def _on_accept(self, event):
        self._accepted = True
        self.EndModal(wx.ID_OK)

    def _on_decline(self, event):
        self._accepted = False
        self.EndModal(wx.ID_CANCEL)

    @property
    def accepted(self) -> bool:
        return self._accepted
