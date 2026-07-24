"""
Classes de acessibilidade para leitores de tela (NVDA, JAWS, Narrator).

Inspirado no WinZapp: usamos wx.Accessible customizado para expor
atalhos de teclado e nomes legíveis em controles que, de outra
forma, seriam anunciados genericamente pelo leitor de telas.

Regra de ouro: usar wx.ListCtrl padrão em vez de custom-drawn,
e Freeze()/Thaw() em atualizações de lista para evitar
sobrecarga de eventos de acessibilidade.
"""

import wx



class AccessibleAddTorrent(wx.Accessible):
    """Expõe Ctrl+T como atalho para adicionar torrent."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "Ctrl+T")


class AccessiblePauseTorrent(wx.Accessible):
    """Expõe Ctrl+P como atalho para pausar/retomar."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "Ctrl+P")


class AccessibleRemoveTorrent(wx.Accessible):
    """Expõe Delete como atalho para remover."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "Delete")


class AccessibleOpenFile(wx.Accessible):
    """Expõe Ctrl+O como atalho para abrir arquivo torrent."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "Ctrl+O")


class AccessibleSearchField(wx.Accessible):
    """Expõe Ctrl+F como atalho para buscar."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "Ctrl+F")


class AccessibleTorrentList(wx.Accessible):
    """
    Expõe um nome descritivo para a lista de torrents.
    Evita que o NVDA anuncie apenas 'SysListView32' genérico.
    """

    def __init__(self, label):
        super().__init__()
        self._label = label

    def GetName(self, childId):
        if childId == 0:
            return (wx.ACC_OK, self._label)
        return (wx.ACC_NOT_IMPLEMENTED, "")


class AccessibleNavList(wx.Accessible):
    """Expõe nome para a lista de navegação."""

    def __init__(self, label):
        super().__init__()
        self._label = label

    def GetName(self, childId):
        if childId == 0:
            return (wx.ACC_OK, self._label)
        return (wx.ACC_NOT_IMPLEMENTED, "")


class AccessibleSpeedLimit(wx.Accessible):
    """Expõe Ctrl+L como atalho para limitar velocidade."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "Ctrl+L")


class AccessibleRefreshTorrents(wx.Accessible):
    """Expõe F5 como atalho para atualizar."""

    def GetKeyboardShortcut(self, childId):
        return (wx.ACC_OK, "F5")


class AccessibleProgressGauge(wx.Accessible):
    """
    Barra de progresso acessível.

    Anuncia o valor atual e máximo para leitores de tela,
    permitindo que o NVDA/JAWS anunciem a porcentagem correta.
    Deve ser anexada a um wx.Gauge.
    """

    def __init__(self, label):
        super().__init__()
        self._label = label

    def GetName(self, childId):
        if childId == 0:
            return (wx.ACC_OK, self._label)
        return (wx.ACC_NOT_IMPLEMENTED, "")

    def GetValue(self, childId):
        """Retorna o valor atual da barra de progresso como string."""
        gauge = self.GetWindow()
        if gauge:
            return (wx.ACC_OK, str(gauge.GetValue()))
        return (wx.ACC_NOT_IMPLEMENTED, "0")

    def GetMaximum(self, childId):
        """Retorna o valor maximo da barra de progresso como string."""
        gauge = self.GetWindow()
        if gauge:
            return (wx.ACC_OK, str(gauge.GetRange()))
        return (wx.ACC_NOT_IMPLEMENTED, "100")

    def GetDescription(self, childId):
        if childId == 0:
            gauge = self.GetWindow()
            if gauge:
                pct = (gauge.GetValue() / max(gauge.GetRange(), 1)) * 100
                return (wx.ACC_OK, f"{self._label}: {pct:.0f}%")
            return (wx.ACC_OK, self._label)
        return (wx.ACC_NOT_IMPLEMENTED, "")