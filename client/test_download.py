"""
Teste real do motor BitTorrent com um magnet link.

Verifica se:
1. Sessão libtorrent inicia corretamente
2. DHT se conecta
3. Magnet link obtém metadados
4. Conecta a peers e baixa dados
"""

import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("test_download")

import libtorrent as lt

print("=" * 60)
print("libtorrent version:", lt.__version__)
print("=" * 60)

# ── 1. high_performance_seed ──────────────────────────────────────────────
print("\n1. Testando high_performance_seed()...")
try:
    hp = lt.high_performance_seed()
    print(f"   Tipo: {type(hp)}")
    if isinstance(hp, dict):
        print(f"   É dict com {len(hp)} chaves")
        # Mostra algumas chaves importantes
        for key in ["download_rate_limit", "upload_rate_limit", "connections_limit",
                     "active_downloads", "active_seeds", "enable_dht"]:
            print(f"   {key} = {hp.get(key, 'N/A')}")
    else:
        print(f"   NÃO é dict! É {type(hp)}")
except Exception as e:
    print(f"   FALHOU: {e}")

# ── 2. Criar sessão ──────────────────────────────────────────────────────
print("\n2. Criando sessão libtorrent...")
ses = lt.session()

# Aplica settings
s = lt.high_performance_seed()
s["listen_interfaces"] = "0.0.0.0:6881,[::]:6881"
s["enable_dht"] = True
s["enable_lsd"] = True
s["enable_upnp"] = True
s["enable_natpmp"] = True
s["active_downloads"] = 30
s["active_seeds"] = 30
s["active_limit"] = 60
s["alert_mask"] = int(
    lt.alert.category_t.error_notification
    | lt.alert.category_t.status_notification
    | lt.alert.category_t.storage_notification
    | lt.alert.category_t.performance_warning
)
s["user_agent"] = "BrasilTorrent/0.1.0"
ses.apply_settings(s)
print("   Settings aplicados.")

# ── 3. DHT ────────────────────────────────────────────────────────────────
print("\n3. Configurando DHT...")
dht_nodes = [
    ("dht.libtorrent.org", 25401),
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
]
for host, port in dht_nodes:
    try:
        ses.add_dht_router(host, port)
        print(f"   add_dht_router({host}, {port}) OK")
    except Exception as e:
        print(f"   add_dht_router({host}, {port}) falhou: {e}")

try:
    ses.start_dht()
    print("   start_dht() OK")
except Exception as e:
    print(f"   start_dht() falhou: {e}")

# ── 4. Adicionar magnet ─────────────────────────────────────────────────
print("\n4. Adicionando magnet link (Ubuntu 24.10)...")

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
print(f"   Download dir: {DOWNLOAD_DIR}")

params = lt.add_torrent_params()
params.url = (
    "magnet:?xt=urn:btih:2c16fc21ab0c37aebeef7df0f08deb9b7a9c2942"
    "&dn=ubuntu-24.10-desktop-amd64.iso"
    "&tr=udp://tracker.opentrackr.org:1337/announce"
    "&tr=udp://tracker.coppersurfer.tk:6969/announce"
    "&tr=udp://tracker.leechers-paradise.org:6969/announce"
    "&tr=https://tracker.opentrackr.org:443/announce"
)
params.save_path = DOWNLOAD_DIR
params.storage_mode = lt.storage_mode_t.storage_mode_sparse
params.flags &= ~lt.torrent_flags.auto_managed  # force-start

try:
    handle = ses.add_torrent(params)
    print(f"   handle.is_valid() imediatamente: {handle.is_valid()}")
except Exception as e:
    print(f"   add_torrent FALHOU: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ── 5. Aguardar info hash ───────────────────────────────────────────────
print("\n5. Aguardando handle ficar válido...")
for i in range(60):
    if handle.is_valid():
        break
    time.sleep(0.5)
else:
    print("   TIMEOUT: handle nunca ficou válido!")
    sys.exit(1)

info_hash = str(handle.info_hash())
print(f"   Info hash: {info_hash}")

# ── 6. Monitorar por 60 segundos ────────────────────────────────────────
print("\n6. Monitorando por 60 segundos...")
print(f"{'T(s)':>4} {'Estado':<25} {'Progresso':>8} {'Down':>8} {'Up':>8} "
      f"{'Peers':>6} {'Seeds':>6} {'DHT':>6} {'Metadados':<12}")
print("-" * 90)

got_metadata = False
last_alert_info = ""

for i in range(60):
    time.sleep(1)

    # Alerts
    for a in ses.pop_alerts():
        try:
            msg = a.message() if hasattr(a, 'message') else str(a)
            if isinstance(a, lt.metadata_received_alert):
                got_metadata = True
                print(f"\n   >>> Metadados recebidos!")
                try:
                    ti = handle.torrent_file()
                    print(f"   >>> Nome: {ti.name()}")
                    print(f"   >>> Tamanho: {ti.total_size() // (1024*1024)} MB")
                    print(f"   >>> Arquivos: {ti.num_files()}")
                except Exception:
                    pass
            elif isinstance(a, lt.torrent_error_alert):
                print(f"\n   >>> ERRO: {msg}")
            elif isinstance(a, lt.peer_connect_alert):
                if i % 10 == 0:
                    last_alert_info = f"peer_connect:{msg[:50]}"
            elif isinstance(a, lt.add_torrent_alert):
                print(f"\n   >>> Torrent adicionado: {a.handle.info_hash()}")
        except Exception:
            pass

    # Status
    try:
        st = ses.status()
        dht_nodes_count = st.dht_nodes if hasattr(st, 'dht_nodes') else 0
    except Exception:
        dht_nodes_count = 0

    try:
        ts = handle.status()
        state_map = {
            0: "queued_for_checking",
            1: "checking_files",
            2: "downloading_metadata",
            3: "downloading",
            4: "finished",
            5: "seeding",
            6: "allocating",
            7: "checking_resume_data",
        }
        state_str = state_map.get(ts.state, str(ts.state))
        progress = ts.progress * 100
        down_rate = ts.download_rate // 1024
        up_rate = ts.upload_rate // 1024
        peers = ts.num_peers
        seeds = ts.num_seeds
        has_meta = "SIM" if (got_metadata or ts.has_metadata) else "NÃO"
        total_dl = ts.total_downloaded // 1024
    except Exception:
        state_str = "ERRO"
        progress = 0
        down_rate = 0
        up_rate = 0
        peers = 0
        seeds = 0
        has_meta = "N/A"
        total_dl = 0

    suffix = ""
    if total_dl > 0:
        suffix = f" DL:{total_dl}K"
    if last_alert_info and i % 10 == 0:
        suffix += f" [{last_alert_info}]"

    print(f"{i+1:>4d} {state_str:<25s} {progress:>7.1f}% "
          f"{down_rate:>7d}K {up_rate:>7d}K "
          f"{peers:>5d} {seeds:>5d} {dht_nodes_count:>5d} {has_meta:<12s}{suffix}")

    # Se já temos metadados, mostra info adicional
    if got_metadata or ts.has_metadata:
        try:
            if not got_metadata:
                got_metadata = True
                ti = handle.torrent_file()
                print(f"   --- Nome: {ti.name()}, Tamanho: {ti.total_size() // (1024*1024)} MB")
        except Exception:
            pass

print("\n" + "=" * 60)
print("Teste concluído!")
print(f"Metadados obtidos: {'SIM' if got_metadata else 'NÃO'}")
print(f"Peers conectados: {peers}")
print(f"Progresso final: {progress:.1f}%")
print(f"DHT nodes: {dht_nodes_count}")
print("=" * 60)

# ── 7. Limpeza ───────────────────────────────────────────────────────────
print("\n7. Limpando...")
try:
    ses.remove_torrent(handle)
    print("   Torrent removido.")
except Exception:
    pass
ses = None
print("   Sessão destruída.")
