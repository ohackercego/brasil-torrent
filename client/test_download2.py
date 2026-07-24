"""Teste de download REAL com Big Buck Bunny (hash verificado)."""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import libtorrent as lt

# Big Buck Bunny - hash real amplamente seedeado
# Fonte: https://webtorrent.io/free-torrents
MAGNET = (
    "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
    "&dn=Big+Buck+Bunny"
    "&tr=udp://tracker.opentrackr.org:1337/announce"
    "&tr=udp://tracker.coppersurfer.tk:6969/announce"
    "&tr=udp://tracker.leechers-paradise.org:6969/announce"
    "&tr=https://tracker.opentrackr.org:443/announce"
    "&tr=udp://open.demonii.com:1337/announce"
    "&tr=http://tracker.ipv6tracker.ru:80/announce"
    "&tr=udp://tracker.moeking.me:6969/announce"
)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "downloads", "bbb_test")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

print("=" * 70)
print("libtorrent version:", lt.__version__)
print("Magnet:", MAGNET[:80] + "...")
print("Save path:", DOWNLOAD_DIR)
print("=" * 70)

# ── Criar sessão ──────────────────────────────────────────────────────────
print("\n1. Criando sessao...")
ses = lt.session()

# Settings
s = ses.get_settings()
s["listen_interfaces"] = "0.0.0.0:6881,[::]:6881"
s["enable_dht"] = True
s["enable_lsd"] = True
s["enable_upnp"] = True
s["enable_natpmp"] = True
s["active_downloads"] = 50
s["active_seeds"] = 50
s["active_limit"] = 100
s["alert_mask"] = int(
    lt.alert.category_t.error_notification
    | lt.alert.category_t.status_notification
    | lt.alert.category_t.storage_notification
    | lt.alert.category_t.performance_warning
    | lt.alert.category_t.tracker_notification
    | lt.alert.category_t.connect_notification
)
s["user_agent"] = "BrasilTorrent/0.1.0"
s["announce_to_all_trackers"] = True
s["announce_to_all_tiers"] = True
s["connection_speed"] = 500
s["max_queued_disk_bytes"] = 4 * 1024 * 1024
s["rate_limit_ip_overhead"] = False
s["no_connect_privileged_ports"] = False
ses.apply_settings(s)
print("   Settings OK")

# ── DHT ───────────────────────────────────────────────────────────────────
print("\n2. DHT...")
for host, port in [("router.bittorrent.com", 6881),
                   ("dht.transmissionbt.com", 6881),
                   ("dht.libtorrent.org", 25401)]:
    try:
        ses.add_dht_router(host, port)
        print(f"   add_dht_router({host},{port}) OK")
    except Exception as e:
        print(f"   add_dht_router({host},{port}) falhou: {e}")

ses.start_dht()
print("   start_dht() OK")

# ── Adicionar magnet ──────────────────────────────────────────────────────
print("\n3. Adicionando magnet...")
params = lt.add_torrent_params()
params.url = MAGNET
params.save_path = DOWNLOAD_DIR
params.storage_mode = lt.storage_mode_t.storage_mode_sparse
params.flags &= ~lt.torrent_flags.auto_managed
params.trackers = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.coppersurfer.tk:6969/announce",
    "udp://tracker.leechers-paradise.org:6969/announce",
    "https://tracker.opentrackr.org:443/announce",
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.moeking.me:6969/announce",
]

handle = ses.add_torrent(params)
print(f"   handle.is_valid(): {handle.is_valid()}")
time.sleep(1)

# ── Monitorar ─────────────────────────────────────────────────────────────
print("\n4. Monitorando (ate 180s)...")
print(f"{'T(s)':>4} {'Estado':<22} {'Progresso':>8} {'Down':>8} {'Up':>8} "
      f"{'Peers':>6} {'Seeds':>6} {'DHT':>6} {'Meta':<4} {'Evento':<30}")
print("-" * 110)

got_metadata = False
ts = None

for i in range(180):
    time.sleep(1)

    # Alerts
    evento = ""
    for a in ses.pop_alerts():
        try:
            if isinstance(a, lt.metadata_received_alert):
                got_metadata = True
                evento = "METADADOS!"
            elif isinstance(a, lt.torrent_error_alert):
                evento = f"ERRO:{str(a.message())[:40]}"
            elif isinstance(a, lt.peer_connect_alert):
                if not evento:
                    evento = "peer_connect"
            elif isinstance(a, lt.tracker_reply_alert):
                evento = f"tracker:{a.num_peers}p"
            elif isinstance(a, lt.tracker_warning_alert):
                if not evento:
                    evento = f"trak_warn:{str(a.message())[:30]}"
            elif isinstance(a, lt.tracker_error_alert):
                if not evento:
                    evento = f"trak_err:{a.status_code}"
            elif isinstance(a, lt.dht_reply_alert):
                if not evento:
                    evento = f"dht_reply:{a.num_peers}p"
            elif isinstance(a, lt.external_ip_alert):
                if not evento:
                    evento = f"ext_ip:{a.external_ip}"
            elif isinstance(a, lt.dht_bootstrap_alert):
                if not evento:
                    evento = "dht_bootstrapped"
        except Exception:
            pass

    # Status sessão
    try:
        st = ses.status()
        dht_n = st.dht_nodes if hasattr(st, "dht_nodes") else 0
        dht_peers = st.dht_global_nodes if hasattr(st, "dht_global_nodes") else 0
    except Exception:
        dht_n = 0
        dht_peers = 0

    # Status torrent
    try:
        ts = handle.status()
        state_str = str(ts.state)
        progress = ts.progress * 100
        down_rate = ts.download_rate // 1024
        up_rate = ts.upload_rate // 1024
        peers = ts.num_peers
        seeds = ts.num_seeds
        has_meta = "S" if (got_metadata or ts.has_metadata) else "N"
        tot_dl = ts.total_downloaded // 1024
        tot_up = ts.total_uploaded // 1024
        extra = ""
        if tot_dl > 0:
            extra = f" DL:{tot_dl}K UL:{tot_up}K"
        if evento:
            extra = f" [{evento}]" + extra
    except Exception as e:
        print(f"   ERRO status: {e}")
        continue

    # Mostra a cada 2 segundos para não floodar
    if i < 30 or i % 2 == 0 or got_metadata or evento:
        print(f"{i+1:>4d}s {state_str:<22s} {progress:>7.1f}% "
              f"{down_rate:>7d}K {up_rate:>7d}K "
              f"{peers:>5d} {seeds:>5d} {dht_n:>5d} {has_meta:<4s} {extra:<40s}")

    if got_metadata:
        try:
            ti = handle.torrent_file()
            name = ti.name()
            size_mb = ti.total_size() // (1024 * 1024)
            n_files = ti.num_files()
        except Exception:
            name = "?"
            size_mb = 0
            n_files = 0
        if i < 5 or i % 10 == 0:
            print(f"   >>> {name} - {size_mb}MB - {n_files} arquivos")
        if progress > 0.1 and progress < 1.0:
            pass  # baixando!
        if ts.has_metadata and progress >= 100.0:
            print(f"\n   >>> DOWNLOAD COMPLETO! <<<")
            break

print(f"\n{'='*70}")
print(f"RESULTADO FINAL:")
print(f"  Metadados: {'SIM' if got_metadata else 'NAO'}")
print(f"  Progresso: {ts.progress*100:.1f}%" if ts else "N/A")
print(f"  Peers: {ts.num_peers if ts else 0}")
print(f"  DHT nodes: {dht_n}")
print(f"  Download: {ts.download_rate//1024 if ts else 0} KB/s")
print(f"{'='*70}")

# ── Limpeza ───────────────────────────────────────────────────────────────
print("\n5. Limpando...")
try:
    ses.remove_torrent(handle)
except Exception:
    pass
print("   OK")
