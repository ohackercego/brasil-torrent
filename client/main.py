"""
Brasil Torrent — Cliente BitTorrent open-source com foco em acessibilidade.

Arquitetura inspirada no WinZapp (WhatsApp client):
- wxPython para interface totalmente acessível a leitores de tela
- libtorrent-rasterbar 2.0.x como motor BitTorrent
- accessible_output2 para saída de voz (NVDA, JAWS, Narrator)
- Lista unificada de torrents com ordenação por coluna

Ponto de entrada: python main.py
"""

import ctypes
import locale
import os
import sys
import threading
import winreg
import wx
import wx.adv
from accessible_output2.outputs.auto import Auto as _ScreenReaderOutput
from config import settings
from core.i18n import I18n, LANGUAGE_NAMES
from core.torrent_engine import TorrentEngine
from core.utils import is_magnet_link, is_torrent_file
from app_paths import data_path, download_path
from version import __version__, __app_name__

from ui.transfers import TorrentsPanel
from ui.tray_icon import BrasilTorrentTrayIcon
from ui.dialogs.add_torrent import AddTorrentDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.torrent_detail import TorrentDetailDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.terms_dialog import TermsDialog

import logging

log_dir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "log.txt"), mode="a", encoding="utf-8"),
        logging.FileHandler(os.path.join(data_path(), "brasil_torrent.log"), mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class MainWindow(wx.Frame):
    """Janela principal do Brasil Torrent.

    Layout simplificado — lista unificada de torrents sem navegação lateral.
    """

    def __init__(self):
        # ── Configurações iniciais ───────────────────────────────────────────
        self.settings = settings
        self.i18n = I18n(settings.get_setting("general", "language", default="pt-BR"))

        # ── Bandeja do sistema ───────────────────────────────────────────────
        self._tray_icon = None

        # ── Screen reader output ─────────────────────────────────────────────
        self._screen_reader = None
        try:
            self._screen_reader = _ScreenReaderOutput()
        except Exception:
            logger.warning("accessible_output2 não disponível — sem saída de voz.")

        # ── Motor BitTorrent ─────────────────────────────────────────────────
        self.engine = TorrentEngine()
        self.engine.on_torrent_finished = self._on_torrent_finished
        self.engine.on_torrent_error = self._on_torrent_error
        self.engine.on_torrent_added = self._on_torrent_added
        self.engine.on_torrent_removed = self._on_torrent_removed
        self.engine.on_session_stats = self._on_session_stats

        # ── Paths ────────────────────────────────────────────────────────────
        self.download_path = settings.get_setting("general", "download_path", default="") or download_path()
        self._restore_hotkey_id = None

        # ── wx.Frame ─────────────────────────────────────────────────────────
        super().__init__(
            None,
            title=f"{self.i18n.t('app_name')} {__version__}",
            size=(960, 640),
            style=wx.DEFAULT_FRAME_STYLE,
        )
        self.SetMinSize((640, 400))
        self._closing = False

        # ── UI ───────────────────────────────────────────────────────────────
        self._build_menu_bar()
        self._build_status_bar()
        self._build_ui()
        self._create_global_accelerators()

        # Eventos da janela
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_ICONIZE, self._on_iconize)
        self.Bind(wx.EVT_CHAR_HOOK, self._on_char_hook)

        # Centraliza e mostra
        self.Centre()
        self.Show()
        self._create_tray_icon()
        self._register_restore_hotkey()

        # ── Inicia o engine ──────────────────────────────────────────────────
        self.output(self.i18n.t("status_bar_connecting"), interrupt=True)
        threading.Thread(target=self._start_engine, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # Screen reader output (inspirado no WinZapp)
    # ══════════════════════════════════════════════════════════════════════════

    def output(self, text: str, interrupt: bool = False):
        """Envia texto para o leitor de telas (NVDA/JAWS/Narrator)."""
        if not text:
            return
        if self._screen_reader is not None:
            try:
                self._screen_reader.speak(text, interrupt=interrupt)
                logger.debug(f"output(): {text}")
            except Exception as e:
                logger.warning(f"output() falhou: {e}")
        else:
            logger.debug(f"output() ignorado (sem leitor de tela): {text}")

    # ══════════════════════════════════════════════════════════════════════════
    # Menu Bar
    # ══════════════════════════════════════════════════════════════════════════

    def _build_menu_bar(self):
        i18n = self.i18n
        menubar = wx.MenuBar()

        # ── Arquivo ──────────────────────────────────────────────────────────
        file_menu = wx.Menu()
        item_add_torrent = file_menu.Append(wx.ID_ANY, i18n.t("menu_file_add_torrent"))
        item_add_magnet = file_menu.Append(wx.ID_ANY, i18n.t("menu_file_add_magnet"))
        item_open_file = file_menu.Append(wx.ID_ANY, i18n.t("menu_file_open_torrent"))
        file_menu.AppendSeparator()
        item_exit = file_menu.Append(wx.ID_EXIT, i18n.t("menu_file_exit"))

        self.Bind(wx.EVT_MENU, lambda e: self.on_add_torrent(), item_add_torrent)
        self.Bind(wx.EVT_MENU, lambda e: self._on_add_magnet(), item_add_magnet)
        self.Bind(wx.EVT_MENU, lambda e: self.on_open_torrent_file(), item_open_file)
        self.Bind(wx.EVT_MENU, lambda e: self._on_close(None), item_exit)

        menubar.Append(file_menu, i18n.t("menu_file"))

        # ── Ferramentas ──────────────────────────────────────────────────────
        tools_menu = wx.Menu()
        item_settings = tools_menu.Append(wx.ID_ANY, i18n.t("menu_tools_settings"))
        item_limits = tools_menu.Append(wx.ID_ANY, i18n.t("menu_tools_limits"))
        tools_menu.AppendSeparator()
        item_about = tools_menu.Append(wx.ID_ANY, i18n.t("menu_help_about"))

        self.Bind(wx.EVT_MENU, lambda e: self.open_settings(), item_settings)
        self.Bind(wx.EVT_MENU, lambda e: self.on_speed_limits(), item_limits)
        self.Bind(wx.EVT_MENU, lambda e: self._show_about(), item_about)

        menubar.Append(tools_menu, i18n.t("menu_tools"))

        self.SetMenuBar(menubar)

    # ══════════════════════════════════════════════════════════════════════════
    # Status Bar
    # ══════════════════════════════════════════════════════════════════════════

    def _build_status_bar(self):
        """Cria a barra de status com 4 campos."""
        self.status_bar = self.CreateStatusBar(4)
        self.status_bar.SetStatusWidths([-2, -1, -1, -1])
        self.status_bar.SetStatusText(self.i18n.t("status_bar_ready"), 0)

    def _update_status_bar(self, download_rate=0, upload_rate=0, dht_nodes=0):
        """Atualiza as informações da barra de status."""
        from core.utils import format_speed
        if self.status_bar:
            self.status_bar.SetStatusText(f"↓ {format_speed(download_rate)}", 1)
            self.status_bar.SetStatusText(f"↑ {format_speed(upload_rate)}", 2)
            if dht_nodes > 0:
                self.status_bar.SetStatusText(f"DHT: {dht_nodes}", 3)
            else:
                self.status_bar.SetStatusText(self.i18n.t("status_bar_dht_off"), 3)

    # ══════════════════════════════════════════════════════════════════════════
    # UI Principal — Lista Única
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Painel único de torrents (sem navegação lateral)."""
        self.torrents_panel = TorrentsPanel(self, self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.torrents_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.torrents_panel.torrents_list.SetFocus()

    def _create_global_accelerators(self):
        """Atalhos globais da janela principal."""
        entries = [
            (wx.ACCEL_CTRL, ord("T"), wx.NewIdRef()),
            (wx.ACCEL_CTRL, ord("O"), wx.NewIdRef()),
            (wx.ACCEL_CTRL, ord("L"), wx.NewIdRef()),
            (wx.ACCEL_NORMAL, wx.WXK_F5, wx.NewIdRef()),
            (wx.ACCEL_ALT, ord("3"), wx.NewIdRef()),
            (wx.ACCEL_NORMAL, ord("D"), wx.NewIdRef()),
        ]

        self.Bind(wx.EVT_MENU, lambda e: self.on_add_torrent(), id=entries[0][2])
        self.Bind(wx.EVT_MENU, lambda e: self.on_open_torrent_file(), id=entries[1][2])
        self.Bind(wx.EVT_MENU, lambda e: self.on_speed_limits(), id=entries[2][2])
        self.Bind(wx.EVT_MENU, lambda e: self.refresh_torrents(), id=entries[3][2])
        self.Bind(wx.EVT_MENU, lambda e: self.open_settings(), id=entries[4][2])
        self.Bind(wx.EVT_MENU, lambda e: self._on_detail_shortcut(), id=entries[5][2])

        accel_tbl = wx.AcceleratorTable([
            (mod, key, id_ref.GetId()) for mod, key, id_ref in entries
        ])
        self.SetAcceleratorTable(accel_tbl)

    def _on_detail_shortcut(self):
        """Atalho 'd' — abre detalhes do torrent selecionado."""
        info_hash = self._get_selected_hash()
        if info_hash:
            self.show_torrent_detail(info_hash)

    # ══════════════════════════════════════════════════════════════════════════
    # Ações do usuário
    # ══════════════════════════════════════════════════════════════════════════

    def on_add_torrent(self):
        """Abre diálogo para adicionar torrent via aba magnet/file."""
        dlg = AddTorrentDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            magnet = dlg.magnet_link
            filepath = dlg.torrent_file
            save_path = dlg.save_path
            if magnet:
                threading.Thread(
                    target=self._add_torrent_bg,
                    args=(magnet, save_path, True),
                    daemon=True,
                ).start()
            elif filepath:
                threading.Thread(
                    target=self._add_torrent_bg,
                    args=(filepath, save_path, False),
                    daemon=True,
                ).start()
        dlg.Destroy()

    def _add_torrent_bg(self, uri_or_path: str, save_path: str, is_magnet: bool):
        """Adiciona torrent em background thread."""
        try:
            if is_magnet:
                self.engine.add_magnet(uri_or_path, save_path)
            else:
                self.engine.add_torrent_file(uri_or_path, save_path)
        except Exception as e:
            logger.error(f"Erro ao adicionar torrent: {e}")
            wx.CallAfter(
                wx.MessageBox,
                str(e),
                self.i18n.t("error_generic"),
                wx.OK | wx.ICON_ERROR,
            )

    def _on_add_magnet(self):
        """Adiciona magnet link rapidamente via caixa de diálogo simplificada."""
        i18n = self.i18n
        dlg = wx.TextEntryDialog(self, i18n.t("magnet_instruction"), i18n.t("add_torrent_title"))
        if dlg.ShowModal() == wx.ID_OK:
            magnet = dlg.GetValue().strip()
            if magnet and is_magnet_link(magnet):
                threading.Thread(
                    target=self.engine.add_magnet,
                    args=(magnet,),
                    daemon=True,
                ).start()
        dlg.Destroy()

    def on_open_torrent_file(self):
        """Abre seletor de arquivos para abrir .torrent."""
        i18n = self.i18n
        wildcard = f"{i18n.t('torrent_files')} (*.torrent)|*.torrent|{i18n.t('all_files')} (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message=i18n.t("select_torrent_file"),
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            for path in dlg.GetPaths():
                if is_torrent_file(path):
                    threading.Thread(
                        target=self.engine.add_torrent_file,
                        args=(path,),
                        daemon=True,
                    ).start()
        dlg.Destroy()

    def on_stop_continue_selected(self):
        """Para ou continua o torrent selecionado."""
        info_hash = self._get_selected_hash()
        if not info_hash:
            return
        entry = self.engine.get_torrent(info_hash)
        if entry:
            if entry.paused or entry.stopped:
                self.engine.resume_torrent(info_hash)
                self.output(f"{self.i18n.t('action_continue')}: {entry.name}")
            else:
                self.engine.stop_torrent(info_hash)
                self.output(f"{self.i18n.t('action_stop')}: {entry.name}")

    def on_remove_selected(self):
        """Remove o torrent selecionado com confirmação."""
        info_hash = self._get_selected_hash()
        if not info_hash:
            return
        entry = self.engine.get_torrent(info_hash)
        if not entry:
            return
        i18n = self.i18n
        dlg = wx.MessageDialog(
            self,
            f"{i18n.t('confirm_remove_message')}\n\n{entry.name}",
            i18n.t("confirm_remove_title"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        if dlg.ShowModal() == wx.ID_YES:
            self.engine.remove_torrent(info_hash)
            self.output(f"{entry.name} removido")
        dlg.Destroy()

    def show_torrent_detail(self, info_hash: str):
        """Abre diálogo de detalhes do torrent com TreeCtrl e barra de progresso."""
        dlg = TorrentDetailDialog(self, info_hash)
        dlg.ShowModal()
        dlg.Destroy()

    def on_speed_limits(self):
        """Diálogo simples para limites de velocidade."""
        i18n = self.i18n
        dlg = wx.Dialog(self, title=i18n.t("speed_limit_title"))
        panel = wx.Panel(dlg)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(panel, label=i18n.t("speed_limit_download")), 0, wx.ALL, 5)
        dl_spin = wx.SpinCtrl(panel, min=0, max=100000, initial=settings.get_setting("connection", "max_download_rate", default=0))
        sizer.Add(dl_spin, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        sizer.Add(wx.StaticText(panel, label=i18n.t("speed_limit_upload")), 0, wx.ALL, 5)
        ul_spin = wx.SpinCtrl(panel, min=0, max=100000, initial=settings.get_setting("connection", "max_upload_rate", default=0))
        sizer.Add(ul_spin, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(panel, wx.ID_OK, label=i18n.t("ok"))
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, label=i18n.t("cancel"))
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 8)

        panel.SetSizer(sizer)
        dlg.SetSize((300, 200))

        if dlg.ShowModal() == wx.ID_OK:
            dl_val = dl_spin.GetValue()
            ul_val = ul_spin.GetValue()
            settings["connection"]["max_download_rate"] = dl_val
            settings["connection"]["max_upload_rate"] = ul_val
            settings.save()
            if self.engine:
                self.engine.set_speed_limits(dl_val * 1024, ul_val * 1024)
            self.output(f"{i18n.t('speed_limit_download')} {dl_val} KB/s, {i18n.t('speed_limit_upload')} {ul_val} KB/s")
        dlg.Destroy()

    def open_settings(self):
        """Abre o diálogo de configurações."""
        dlg = SettingsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            new_lang = settings.get_setting("general", "language", default="pt-BR")
            if new_lang != self.i18n._language:
                self.i18n.load(new_lang)
                self._refresh_ui_language()
            self.output(self.i18n.t("settings_title"))
            sync_autostart()
        dlg.Destroy()

    def refresh_torrents(self):
        """Força atualização da lista de torrents."""
        self.torrents_panel.refresh()
        self.output(self.i18n.t("refresh"))

    def _create_tray_icon(self):
        """Cria o ícone na bandeja do sistema se configurado."""
        if settings.get_setting("appearance", "show_tray_icon", default=True):
            try:
                self._tray_icon = BrasilTorrentTrayIcon(self)
            except Exception:
                self._tray_icon = None

    def _remove_tray_icon(self):
        """Remove o ícone da bandeja."""
        if self._tray_icon:
            try:
                self._tray_icon.RemoveIcon()
                self._tray_icon = None
            except Exception:
                pass

    def _on_torrent_notification(self, title: str, message: str):
        """Mostra notificação do sistema se habilitado."""
        if not settings.get_setting("general", "notifications_enabled", default=True):
            return
        try:
            notification = wx.adv.NotificationMessage(
                title, message,
                flags=wx.ICON_INFORMATION,
            )
            notification.Show(timeout=5)
        except Exception:
            pass

    def _show_about(self):
        """Mostra o diálogo Sobre."""
        dlg = AboutDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def _get_selected_hash(self) -> str:
        """Retorna o info_hash do torrent selecionado na lista.

        Usa _selected_hash em vez de GetFocusedItem() para preservar
        a seleção mesmo quando o foco está em outro controle (botões).
        """
        return self.torrents_panel._selected_hash

    def _refresh_ui_language(self):
        """Recarrega textos de todos os painéis após mudança de idioma."""
        self.SetTitle(f"{self.i18n.t('app_name')} {__version__}")
        self._build_menu_bar()
        self.torrents_panel.refresh()

    # ══════════════════════════════════════════════════════════════════════════
    # Eventos do Motor
    # ══════════════════════════════════════════════════════════════════════════

    def _start_engine(self):
        """Inicia o motor BitTorrent em background."""
        try:
            self.engine.start()
            wx.CallAfter(self._on_engine_started)
        except Exception as e:
            logger.error(f"Falha ao iniciar engine: {e}")
            wx.CallAfter(
                wx.MessageBox,
                str(e),
                self.i18n.t("error_generic"),
                wx.OK | wx.ICON_ERROR,
            )

    def _on_engine_started(self):
        self.output(self.i18n.t("status_bar_engine_started"), interrupt=True)
        self.status_bar.SetStatusText(self.i18n.t("status_bar_ready"), 0)
        self.torrents_panel.refresh()
        sync_autostart()

    def _on_torrent_finished(self, info_hash: str):
        """Callback quando um torrent finaliza."""
        entry = self.engine.get_torrent(info_hash)
        if entry:
            self.output(f"{entry.name}: {self.i18n.t('state_finalizado')}", interrupt=True)
            self._on_torrent_notification(
                self.i18n.t("state_finalizado"),
                f"{entry.name}: {self.i18n.t('state_finalizado')}",
            )

    def _on_torrent_error(self, info_hash: str, error_msg: str):
        """Callback quando ocorre um erro."""
        logger.error(f"Torrent error [{info_hash}]: {error_msg}")

    def _on_torrent_added(self, info_hash: str):
        """Callback quando um torrent é adicionado."""
        self.torrents_panel.refresh()
        entry = self.engine.get_torrent(info_hash)
        if entry:
            self._on_torrent_notification(
                self.i18n.t("add_torrent"),
                f"{entry.name}",
            )

    def _on_torrent_removed(self, info_hash: str):
        """Callback quando um torrent é removido."""
        self.torrents_panel.refresh()
        self._on_torrent_notification(
            self.i18n.t("remove_torrent"),
            info_hash,
        )

    def _on_session_stats(self, download_rate: int, upload_rate: int, dht_nodes: int):
        """Callback com estatísticas da sessão."""
        self._update_status_bar(download_rate, upload_rate, dht_nodes)

    # ══════════════════════════════════════════════════════════════════════════
    # Eventos da Janela
    # ══════════════════════════════════════════════════════════════════════════

    def _on_char_hook(self, event):
        """Intercepta Alt+F4 antes de virar EVT_CLOSE."""
        key = event.GetKeyCode()
        if key == wx.WXK_F4 and event.AltDown():
            self._show_exit_dialog()
            return
        event.Skip()

    def _on_close(self, event):
        """Manipula fechamento por botão X / sistema.

        File > Sair: sempre fecha de fato.
        Alt+F4 é interceptado por _on_char_hook.
        """
        if event is None:
            self._do_exit()
            return

        if getattr(self, "_closing", False):
            event.Skip()
            return

        if settings.get_setting("general", "minimize_to_tray", default=True):
            self.Show(False)
            event.Veto()
        else:
            self._closing = True
            self._unregister_restore_hotkey()
            self._remove_tray_icon()
            logger.info("Parando motor BitTorrent...")
            self.engine.stop()
            self.output(self.i18n.t("status_bar_engine_stopped"))
            settings.save()
            event.Skip()

    def _show_exit_dialog(self):
        """Diálogo de saída: Minimizar para bandeja / Sair / Cancelar."""
        i18n = self.i18n
        choices = [i18n.t("minimize_to_tray"), i18n.t("exit")]
        dlg = wx.SingleChoiceDialog(
            self,
            i18n.t("confirm_exit_message"),
            i18n.t("confirm_exit_title"),
            choices,
        )
        dlg.SetSelection(0 if settings.get_setting("general", "minimize_to_tray", default=True) else 1)
        result = dlg.ShowModal()
        selection = dlg.GetSelection()
        dlg.Destroy()

        if result == wx.ID_OK:
            if selection == 0:
                self.Show(False)
            else:
                self._closing = True
                self._unregister_restore_hotkey()
                self._remove_tray_icon()
                logger.info("Parando motor BitTorrent...")
                self.engine.stop()
                self.output(self.i18n.t("status_bar_engine_stopped"))
                settings.save()
                self.Close()

    def _do_exit(self):
        """Fecha o aplicativo completamente."""
        self._unregister_restore_hotkey()
        self._remove_tray_icon()
        logger.info("Parando motor BitTorrent...")
        self.engine.stop()
        self.output(self.i18n.t("status_bar_engine_stopped"))
        settings.save()
        self.Destroy()

    def _on_iconize(self, event):
        """Minimiza para a bandeja se configurado."""
        if settings.get_setting("general", "minimize_to_tray", default=True):
            self.Show(False)
        else:
            event.Skip()

    def _register_restore_hotkey(self):
        """Registra Ctrl+Shift+B como atalho global para restaurar a janela."""
        try:
            self._restore_hotkey_id = wx.NewIdRef()
            mod = wx.MOD_CONTROL | wx.MOD_SHIFT
            ok = self.RegisterHotKey(self._restore_hotkey_id.GetId(), mod, ord("B"))
            if ok:
                self.Bind(wx.EVT_HOTKEY, self._on_global_restore, id=self._restore_hotkey_id.GetId())
                logger.debug("Hotkey Ctrl+Shift+B registrado para restaurar janela")
            else:
                logger.warning("Falha ao registrar hotkey Ctrl+Shift+B")
                self._restore_hotkey_id = None
        except Exception:
            logger.exception("Erro ao registrar hotkey")
            self._restore_hotkey_id = None

    def _unregister_restore_hotkey(self):
        """Remove o atalho global."""
        if self._restore_hotkey_id is not None:
            try:
                self.UnregisterHotKey(self._restore_hotkey_id.GetId())
            except Exception:
                pass
            self._restore_hotkey_id = None

    def _on_global_restore(self, event):
        """Restaura a janela minimizada para a bandeja."""
        self.Show(True)
        self.Raise()
        self.SetFocus()
        self.output(self.i18n.t("app_name"))


# ══════════════════════════════════════════════════════════════════════════════
# Detecção de idioma do sistema
# ══════════════════════════════════════════════════════════════════════════════

def detect_system_language() -> str:
    """Detecta o idioma do sistema operacional.

    Se o idioma for português (qualquer variante: pt-BR, pt-PT, pt-AO, etc),
    retorna 'pt-BR'. Caso contrário, retorna 'en-US'.
    """
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary_lang = lang_id & 0x3FF
        if primary_lang == 22:
            return "pt-BR"
    except Exception:
        pass
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.lower().startswith("pt"):
            return "pt-BR"
    except Exception:
        pass
    return "en-US"


def sync_autostart():
    """Sincroniza a configuração 'auto_start' com o registro do Windows."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "BrasilTorrent"
    exe_path = sys.executable
    if getattr(sys, 'frozen', False):
        cmd = f'"{exe_path}"'
    else:
        cmd = f'"{exe_path}" "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")}"'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
    except Exception:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

    try:
        if settings.get_setting("general", "auto_start", default=False):
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except Exception:
                pass
    finally:
        winreg.CloseKey(key)


# ══════════════════════════════════════════════════════════════════════════════
# Ponto de entrada
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Inicializa e executa o Brasil Torrent."""
    from ui.dialogs.terms_dialog import TermsDialog

    app = wx.App(False)
    app.SetAppName("BrasilTorrent")

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("BrasilTorrent")
    except Exception:
        pass

    # Detecta idioma do sistema na primeira execução
    if not settings.get_setting("general", "terms_accepted", default=False):
        detected = detect_system_language()
        settings["general"]["language"] = detected

    # Diálogo de termos (mostra antes de criar a MainWindow)
    dummy = wx.Frame(None)
    dummy.Hide()
    from core.i18n import I18n as _I18n
    _i18n = _I18n(settings.get_setting("general", "language", default="pt-BR"))
    if not settings.get_setting("general", "terms_accepted", default=False):
        dlg = TermsDialog(dummy, _i18n)
        result = dlg.ShowModal()
        accepted = dlg.accepted
        dlg.Destroy()
        dummy.Destroy()
        if not accepted:
            return
        settings["general"]["terms_accepted"] = True
        settings.save()
    else:
        dummy.Destroy()

    MainWindow()
    app.MainLoop()


if __name__ == "__main__":
    main()
