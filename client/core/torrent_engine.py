"""
Motor BitTorrent baseado em libtorrent-rasterbar 2.0.x.

Gerencia a sessão libtorrent em uma thread separada e se comunica
com a UI via fila de eventos thread-safe (wx.CallAfter).

Inspirado na arquitetura two-process do WinZapp, mas mantendo tudo
num único processo com threading.

API libtorrent 2.0.x:
  - Session settings usam dict (NÃO lt.settings_pack)
  - session.get_settings() -> dict
  - session.apply_settings(dict)
  - lt.high_performance_seed() retorna dict
"""

import logging
import os
import threading
import time
import wx
from dataclasses import dataclass
from typing import Optional

import libtorrent as lt

from config import settings
from core.utils import bytes_to_int

logger = logging.getLogger(__name__)


# ── Alert categorias ─────────────────────────────────────────────────────────
_ALERT_MASK = (
    lt.alert.category_t.error_notification
    | lt.alert.category_t.status_notification
    | lt.alert.category_t.storage_notification
    | lt.alert.category_t.performance_warning
)


# ── Nós DHT padrão ──────────────────────────────────────────────────────────
_DHT_BOOTSTRAP_NODES = [
    ("dht.libtorrent.org", 25401),
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
    ("dht.aelitis.com", 6881),
]

# ── Trackers públicos padrão (usados quando não há trackers no .torrent/magnet) ──
_DEFAULT_TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "udp://tracker.open-internet.nl:6969/announce",
    "udp://open.demonii.com:1337/announce",
    "https://tracker.opentrackr.org:443/announce",
    "udp://p4p.arenabg.com:1337/announce",
    "udp://tracker.torrent.eu.org:451/announce",
]


@dataclass
class TorrentEntry:
    """Representação de um torrent no gerenciador."""

    info_hash: str
    name: str
    save_path: str
    size: int = 0
    progress: float = 0.0          # 0.0 – 1.0
    download_rate: int = 0         # bytes/s
    upload_rate: int = 0           # bytes/s
    total_download: int = 0
    total_upload: int = 0
    num_peers: int = 0
    num_seeds: int = 0
    total_peers: int = 0
    total_seeds: int = 0
    state: int = 0                 # lt.torrent_status.states
    eta: int = -1                  # segundos, -1 = desconhecido
    added_date: float = 0.0
    completed_date: float = 0.0
    error: str = ""
    paused: bool = False
    stopped: bool = False
    sequential: bool = False
    is_magnet: bool = False
    is_finished: bool = False
    handle: Optional['lt.torrent_handle'] = None

    @property
    def state_str(self) -> str:
        if self.stopped:
            return "state_parado"
        if self.paused:
            return "state_pausado"
        states = {
            lt.torrent_status.states.queued_for_checking: "state_aguardando_verificacao",
            lt.torrent_status.states.checking_files: "state_verificando",
            lt.torrent_status.states.downloading_metadata: "state_obtendo_metadados",
            lt.torrent_status.states.downloading: "state_baixando",
            lt.torrent_status.states.finished: "state_finalizado",
            lt.torrent_status.states.seeding: "state_distribuindo",
            lt.torrent_status.states.allocating: "state_alocando",
            lt.torrent_status.states.checking_resume_data: "state_verificando_retomada",
        }
        return states.get(self.state, "state_desconhecido")


class TorrentEngine:
    """Gerenciador de sessão BitTorrent thread-safe.

    Roda a sessão libtorrent numa thread dedicada e notifica a UI
    através de callbacks agendados com wx.CallAfter.
    """

    def __init__(self):
        self._session: Optional[lt.session] = None
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._lock = threading.Lock()
        self._torrents: dict[str, TorrentEntry] = {}
        self._resume_dir: str = ""
        self._last_stats_time: float = 0.0

        # Callbacks registrados pela UI
        self.on_torrent_added = None       # callable(info_hash)
        self.on_torrent_removed = None     # callable(info_hash)
        self.on_torrent_finished = None    # callable(info_hash)
        self.on_torrent_error = None       # callable(info_hash, error_msg)
        self.on_state_updated = None       # callable(info_hash, TorrentEntry)
        self.on_session_stats = None       # callable(download_rate, upload_rate, dht_nodes)

    # ── Ciclo de vida ─────────────────────────────────────────────────────────

    def start(self):
        """Inicializa a sessão libtorrent e a thread de processamento."""
        if self._running.is_set():
            return

        self._session = lt.session()

        # Aplica settings (dict, NÃO settings_pack)
        _apply_settings(self._session)

        # Adiciona nós bootstrap DHT e inicia DHT
        if settings.get_setting("connection", "enable_dht", default=True):
            for host, port in _DHT_BOOTSTRAP_NODES:
                try:
                    self._session.add_dht_router(host, port)
                    logger.debug("DHT router adicionado: %s:%d", host, port)
                except Exception as e:
                    logger.warning("Falha ao adicionar DHT router %s:%d: %s", host, port, e)
            try:
                self._session.start_dht()
            except Exception:
                pass
            logger.info("DHT inicializado com %d nós bootstrap", len(_DHT_BOOTSTRAP_NODES))

        # Define diretório de resume data
        self._resume_dir = os.path.join(
            settings.get_setting("general", "download_path", default="."),
            ".resume",
        )
        os.makedirs(self._resume_dir, exist_ok=True)

        self._running.set()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("TorrentEngine iniciado.")

    def stop(self):
        """Para a sessão e salva resume data."""
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=5)
        self._save_all_resume_data()
        if self._session:
            # Remove todos os torrents
            for entry in list(self._torrents.values()):
                if entry.handle and entry.handle.is_valid():
                    try:
                        self._session.remove_torrent(entry.handle)
                    except Exception:
                        pass
            self._session = None
        logger.info("TorrentEngine parado.")

    # ── Gerenciamento de torrents ─────────────────────────────────────────────

    def add_magnet(self, uri: str, save_path: str = "") -> Optional[str]:
        """Adiciona um magnet link à sessão."""
        if not save_path:
            save_path = settings.get_setting("general", "download_path", default="")
        if not save_path:
            save_path = os.path.join(os.path.expanduser("~"), "Downloads")

        params = lt.add_torrent_params()
        params.url = uri.strip()
        params.save_path = save_path
        params.storage_mode = lt.storage_mode_t.storage_mode_sparse

        # Force-start: flags=0 remove paused+auto_managed, torrent começa ativo
        params.flags = 0

        # Adiciona trackers públicos padrão
        params.trackers = _DEFAULT_TRACKERS

        try:
            handle = self._session.add_torrent(params)
            # Aguarda o info hash ser gerado
            timeout = 60
            while not handle.is_valid() and timeout > 0:
                time.sleep(0.1)
                timeout -= 1
            if not handle.is_valid():
                logger.error("Timeout aguardando info_hash do magnet")
                return None

            info_hash = str(handle.info_hash())

            # Aplica limites de velocidade individuais (0 = ilimitado)
            handle.set_upload_limit(0)
            handle.set_download_limit(0)

            entry = TorrentEntry(
                info_hash=info_hash,
                name="Obtendo metadados...",
                save_path=save_path,
                is_magnet=True,
                added_date=time.time(),
                handle=handle,
            )
            with self._lock:
                self._torrents[info_hash] = entry
            logger.info(f"Magnet adicionado: {info_hash}")
            if self.on_torrent_added:
                wx.CallAfter(self.on_torrent_added, info_hash)
            return info_hash
        except Exception as e:
            logger.error(f"Erro ao adicionar magnet: {e}")
            if self.on_torrent_error:
                wx.CallAfter(self.on_torrent_error, "", str(e))
            return None

    def add_torrent_file(self, filepath: str, save_path: str = "") -> Optional[str]:
        """Adiciona um arquivo .torrent à sessão."""
        if not os.path.isfile(filepath):
            logger.error(f"Arquivo não encontrado: {filepath}")
            return None

        if not save_path:
            save_path = settings.get_setting("general", "download_path", default="")
        if not save_path:
            save_path = os.path.join(os.path.expanduser("~"), "Downloads")

        try:
            info = lt.torrent_info(filepath)
            params = lt.add_torrent_params()
            params.ti = info
            params.save_path = save_path
            params.storage_mode = lt.storage_mode_t.storage_mode_sparse

            # Force-start: flags=0 remove paused+auto_managed, torrent começa ativo
            params.flags = 0

            # Adiciona trackers públicos se o torrent tiver poucos trackers
            try:
                existing = info.trackers()
                num_trackers = len(existing) if existing else 0
            except Exception:
                num_trackers = 0
            if num_trackers < 3:
                params.trackers = list(set(list(params.trackers or []) + list(_DEFAULT_TRACKERS)))

            handle = self._session.add_torrent(params)
            info_hash = str(handle.info_hash())

            entry = TorrentEntry(
                info_hash=info_hash,
                name=info.name(),
                save_path=save_path,
                size=info.total_size(),
                added_date=time.time(),
                handle=handle,
            )
            with self._lock:
                self._torrents[info_hash] = entry
            logger.info(f"Torrent adicionado: {info_hash} - {info.name()}")
            if self.on_torrent_added:
                wx.CallAfter(self.on_torrent_added, info_hash)
            return info_hash
        except Exception as e:
            logger.error(f"Erro ao adicionar torrent: {e}")
            if self.on_torrent_error:
                wx.CallAfter(self.on_torrent_error, "", str(e))
            return None

    def remove_torrent(self, info_hash: str, delete_files: bool = False):
        """Remove um torrent da sessão."""
        with self._lock:
            entry = self._torrents.get(info_hash)
            if entry is None or entry.handle is None:
                return
            try:
                self._session.remove_torrent(entry.handle, delete_files)
            except Exception:
                pass
            del self._torrents[info_hash]

        if self.on_torrent_removed:
            wx.CallAfter(self.on_torrent_removed, info_hash)

    def pause_torrent(self, info_hash: str):
        """Pausa um torrent."""
        with self._lock:
            entry = self._torrents.get(info_hash)
            if entry and entry.handle:
                entry.handle.pause()
                entry.paused = True
                entry.stopped = False

    def resume_torrent(self, info_hash: str):
        """Retoma um torrent pausado ou parado."""
        with self._lock:
            entry = self._torrents.get(info_hash)
            if entry and entry.handle:
                entry.handle.auto_managed(False)
                entry.handle.resume()
                entry.paused = False
                entry.stopped = False

    def stop_torrent(self, info_hash: str):
        """Para um torrent completamente (pausa + desativa auto_managed)."""
        with self._lock:
            entry = self._torrents.get(info_hash)
            if entry and entry.handle:
                entry.handle.auto_managed(False)
                entry.handle.pause()
                entry.stopped = True
                entry.paused = False

    def set_speed_limits(self, download_rate: int, upload_rate: int):
        """Aplica limites de velocidade na sessão (bytes/s)."""
        if not self._session:
            return
        s = self._session.get_settings()
        s["download_rate_limit"] = download_rate
        s["upload_rate_limit"] = upload_rate
        self._session.apply_settings(s)

    def get_torrents(self) -> list[TorrentEntry]:
        """Retorna uma cópia da lista de torrents."""
        with self._lock:
            return list(self._torrents.values())

    def get_torrent(self, info_hash: str) -> Optional[TorrentEntry]:
        """Retorna um torrent específico."""
        with self._lock:
            entry = self._torrents.get(info_hash)
            if entry:
                h = entry.handle
                handle_ok = h is not None and h.is_valid() if h else False
                return TorrentEntry(
                    info_hash=entry.info_hash,
                    name=entry.name,
                    save_path=entry.save_path,
                    size=entry.size,
                    progress=entry.progress,
                    download_rate=entry.download_rate,
                    upload_rate=entry.upload_rate,
                    total_download=entry.total_download,
                    total_upload=entry.total_upload,
                    num_peers=entry.num_peers,
                    num_seeds=entry.num_seeds,
                    total_peers=entry.total_peers,
                    total_seeds=entry.total_seeds,
                    state=entry.state,
                    eta=entry.eta,
                    added_date=entry.added_date,
                    completed_date=entry.completed_date,
                    error=entry.error,
                    paused=entry.paused,
                    stopped=entry.stopped,
                    sequential=entry.sequential,
                    is_magnet=entry.is_magnet,
                    is_finished=entry.is_finished,
                    handle=entry.handle,
                )
            return None

    # ── Loop interno da thread ────────────────────────────────────────────────

    def _run_loop(self):
        """Loop principal: processa alerts e atualiza status (1 Hz)."""
        while self._running.is_set():
            try:
                self._process_alerts()
                self._update_stats()
            except Exception as e:
                logger.error(f"Erro no loop do engine: {e}", exc_info=True)
            time.sleep(0.5)  # 500ms para resposta mais rápida

    def _process_alerts(self):
        """Processa alerts da sessão libtorrent."""
        if not self._session:
            return
        alerts = self._session.pop_alerts()
        for alert in alerts:
            try:
                self._handle_alert(alert)
            except Exception as e:
                logger.error(f"Erro ao processar alert: {e}")

    def _handle_alert(self, alert):
        """Roteia um alerta para o handler apropriado."""
        if isinstance(alert, lt.torrent_finished_alert):
            info_hash = str(alert.handle.info_hash())
            with self._lock:
                entry = self._torrents.get(info_hash)
                if entry:
                    entry.is_finished = True
                    entry.completed_date = time.time()
            if self.on_torrent_finished:
                wx.CallAfter(self.on_torrent_finished, info_hash)

        elif isinstance(alert, lt.torrent_error_alert):
            info_hash = str(alert.handle.info_hash())
            try:
                error_msg = alert.error.message() if hasattr(alert.error, 'message') else str(alert.error)
            except Exception:
                error_msg = "Erro desconhecido"
            with self._lock:
                entry = self._torrents.get(info_hash)
                if entry:
                    entry.error = error_msg
            if self.on_torrent_error:
                wx.CallAfter(self.on_torrent_error, info_hash, error_msg)

        elif isinstance(alert, lt.metadata_received_alert):
            info_hash = str(alert.handle.info_hash())
            with self._lock:
                entry = self._torrents.get(info_hash)
                if entry and entry.handle:
                    try:
                        ti = entry.handle.torrent_file()
                        if ti:
                            entry.name = ti.name()
                            entry.size = ti.total_size()
                    except Exception:
                        pass

        elif isinstance(alert, lt.save_resume_data_alert):
            try:
                data = alert.params
                info_hash = str(alert.handle.info_hash())
                self._write_resume_data(info_hash, data)
            except Exception:
                pass

        elif isinstance(alert, lt.add_torrent_alert):
            info_hash = str(alert.handle.info_hash())
            logger.info(f"Torrent adicionado com sucesso: {info_hash}")

    def _update_stats(self):
        """Atualiza estatísticas de todos os torrents."""
        if not self._session:
            return

        with self._lock:
            for info_hash, entry in list(self._torrents.items()):
                if entry.handle is None or not entry.handle.is_valid():
                    continue
                try:
                    status = entry.handle.status()
                    entry.state = int(status.state)
                    entry.progress = status.progress
                    entry.download_rate = status.download_rate
                    entry.upload_rate = status.upload_rate
                    entry.total_download = status.total_download
                    entry.total_upload = status.total_upload
                    entry.num_peers = status.num_peers
                    entry.num_seeds = status.num_seeds
                    entry.total_peers = status.list_peers
                    entry.total_seeds = status.list_seeds
                    # Calcula ETA manualmente (libtorrent 2.0.13 não tem field eta)
                    if entry.download_rate > 0 and entry.size > 0 and entry.progress > 0:
                        remaining = entry.size - (entry.size * entry.progress)
                        entry.eta = int(remaining / entry.download_rate)
                    else:
                        entry.eta = -1
                    entry.is_finished = status.is_finished
                except Exception:
                    continue

                if self.on_state_updated:
                    wx.CallAfter(self.on_state_updated, info_hash, entry)

        # Estatísticas globais da sessão (a cada 2s)
        now = time.time()
        if now - self._last_stats_time >= 2.0 and self.on_session_stats:
            self._last_stats_time = now
            try:
                status = self._session.status()
                wx.CallAfter(
                    self.on_session_stats,
                    status.download_rate,
                    status.upload_rate,
                    status.dht_nodes,
                )
            except Exception:
                pass

    # ── Resume data ───────────────────────────────────────────────────────────

    def _save_all_resume_data(self):
        """Salva resume data de todos os torrents."""
        if not self._session:
            return
        for entry in self._torrents.values():
            if entry.handle and entry.handle.is_valid():
                try:
                    entry.handle.save_resume_data()
                except Exception:
                    pass

    def _write_resume_data(self, info_hash: str, data):
        """Escreve resume data no disco."""
        try:
            path = os.path.join(self._resume_dir, f"{info_hash}.resume")
            with open(path, "wb") as f:
                f.write(lt.bencode(data))
        except Exception:
            pass


def _apply_settings(session: lt.session):
    """Aplica as configurações usando o formato dict do libtorrent 2.0.x.

    NOTA: lt.settings_pack não existe nesta versão.
    Usamos session.get_settings() -> dict, modificamos e aplicamos.
    """
    # Começa com preset de seed de alta performance
    s = lt.high_performance_seed()

    # ── Limites de velocidade ───────────────────────────────────────────────
    max_up = settings.get_setting("connection", "max_upload_rate", default=0)
    max_dl = settings.get_setting("connection", "max_download_rate", default=0)
    if max_up > 0:
        s["upload_rate_limit"] = max_up * 1024  # KB/s -> bytes/s
    if max_dl > 0:
        s["download_rate_limit"] = max_dl * 1024

    # ── Conexões ────────────────────────────────────────────────────────────
    s["connections_limit"] = settings.get_setting("connection", "max_connections", default=200)

    # ── Limites de active (aplica-se a auto_managed; force-start ignora) ──
    s["active_downloads"] = 30
    s["active_seeds"] = 30
    s["active_limit"] = 60
    s["active_tracker_limit"] = 30
    s["active_dht_limit"] = 30
    s["active_lsd_limit"] = 10

    # ── DHT / LSD / UPnP / NAT-PMP ─────────────────────────────────────────
    s["enable_dht"] = settings.get_setting("connection", "enable_dht", default=True)
    s["enable_lsd"] = settings.get_setting("connection", "enable_lsd", default=True)
    s["enable_upnp"] = settings.get_setting("connection", "enable_upnp", default=True)
    s["enable_natpmp"] = settings.get_setting("connection", "enable_natpmp", default=True)

    # ── Porta de escuta ─────────────────────────────────────────────────────
    port = settings.get_setting("connection", "listen_port", default=6881)
    s["listen_interfaces"] = f"0.0.0.0:{port},[::]:{port}"

    # ── Proxy ───────────────────────────────────────────────────────────────
    proxy_type = settings.get_setting("connection", "proxy_type", default="none")
    proxy_map = {
        "none": lt.proxy_type_t.none,
        "socks5": lt.proxy_type_t.socks5,
        "socks5_pw": lt.proxy_type_t.socks5_pw,
        "http": lt.proxy_type_t.http,
        "http_pw": lt.proxy_type_t.http_pw,
    }
    s["proxy_type"] = int(proxy_map.get(proxy_type, lt.proxy_type_t.none))
    if proxy_type != "none":
        s["proxy_hostname"] = settings.get_setting("connection", "proxy_hostname", default="")
        s["proxy_port"] = settings.get_setting("connection", "proxy_port", default=0)
        s["proxy_username"] = settings.get_setting("connection", "proxy_username", default="")
        s["proxy_password"] = settings.get_setting("connection", "proxy_password", default="")

    # ── Modo anônimo ────────────────────────────────────────────────────────
    if settings.get_setting("privacy", "anonymous_mode", default=False):
        s["anonymous_mode"] = True

    # ── User Agent ──────────────────────────────────────────────────────────
    s["user_agent"] = "BrasilTorrent/0.1.0 libtorrent"

    # ── Alerta mask ─────────────────────────────────────────────────────────
    s["alert_mask"] = int(_ALERT_MASK)

    # ── Aplica ──────────────────────────────────────────────────────────────
    session.apply_settings(s)
