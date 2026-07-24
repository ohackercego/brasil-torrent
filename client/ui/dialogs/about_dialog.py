import datetime
import wx
from version import __version__, __app_name__, __author__, __description__, __url__, __license__


class AboutDialog(wx.Dialog):
    """Informações sobre o Brasil Torrent."""

    def __init__(self, parent):
        super().__init__(
            parent,
            title=f"Sobre {__app_name__}",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._build_ui()
        self.Fit()
        self.SetMinSize((400, 350))
        self.Centre()

    def _build_ui(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Nome do app
        name_label = wx.StaticText(
            panel, label=__app_name__,
            style=wx.ALIGN_CENTER,
        )
        font = name_label.GetFont()
        font.SetPointSize(font.GetPointSize() + 4)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        name_label.SetFont(font)
        sizer.Add(name_label, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        sizer.Add(
            wx.StaticText(panel, label=f"Versão {__version__}", style=wx.ALIGN_CENTER),
            0, wx.ALL | wx.ALIGN_CENTER, 5,
        )

        sizer.Add(
            wx.StaticText(panel, label=__description__, style=wx.ALIGN_CENTER),
            0, wx.ALL | wx.ALIGN_CENTER, 5,
        )

        sizer.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.ALL, 10)

        sizer.Add(
            wx.StaticText(panel, label=f"Criado por {__author__}", style=wx.ALIGN_CENTER),
            0, wx.ALL | wx.ALIGN_CENTER, 5,
        )

        sizer.Add(
            wx.StaticText(panel, label=__url__, style=wx.ALIGN_CENTER),
            0, wx.ALL | wx.ALIGN_CENTER, 5,
        )

        year = datetime.datetime.now().year
        sizer.Add(
            wx.StaticText(panel, label=f"© {year} {__author__}. Licença {__license__}.", style=wx.ALIGN_CENTER),
            0, wx.ALL | wx.ALIGN_CENTER, 5,
        )

        btn_sizer = wx.StdDialogButtonSizer()
        close_btn = wx.Button(panel, wx.ID_CLOSE, label="Fechar")
        btn_sizer.AddButton(close_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer)
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
