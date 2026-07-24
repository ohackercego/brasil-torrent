"""Teste MINIMO para verificar se o download funciona."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import libtorrent as lt

MAGNET = ("magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
          "&dn=Big+Buck+Bunny"
          "&tr=udp://tracker.opentrackr.org:1337/announce")
SAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "downloads", "bbb_min")
os.makedirs(SAVE, exist_ok=True)

print("libtorrent:", lt.__version__)

ses = lt.session()
s = ses.get_settings()
s["enable_dht"] = True
s["enable_lsd"] = True
s["enable_upnp"] = True
s["listen_interfaces"] = "0.0.0.0:6881,[::]:6881"
s["alert_mask"] = int(lt.alert.category_t.error_notification |
                      lt.alert.category_t.status_notification |
                      lt.alert.category_t.tracker_notification)
ses.apply_settings(s)
ses.add_dht_router("router.bittorrent.com", 6881)
ses.start_dht()

# FORCE-START: remover auto_managed E paused
params = lt.add_torrent_params()
params.url = MAGNET
params.save_path = SAVE
params.flags = 0  # NENHUM flag = force-start
handle = ses.add_torrent(params)
print("handle valido:", handle.is_valid())

# Monitorar
print("\nMonitorando 60s...")
print(f"{'T':>4} {'Estado':<22} {'Progresso':>8} {'Down':>8} {'Peers':>6} {'Seeds':>6} {'DHT':>6}")
print("-" * 65)

max_wait = 60
for i in range(max_wait):
    time.sleep(1)
    alerts = ses.pop_alerts()
    for a in alerts:
        if isinstance(a, lt.metadata_received_alert):
            print(f"\n>>> METADADOS RECEBIDOS!")
            ti = handle.torrent_file()
            print(f">>> {ti.name()} - {ti.total_size()//(1024*1024)}MB - {ti.num_files()} arquivos")
        elif isinstance(a, lt.torrent_error_alert):
            print(f">>> ERRO: {a.message()}")
        elif isinstance(a, lt.tracker_reply_alert):
            pass

    ts = handle.status()
    st = ses.status()
    dht_n = st.dht_nodes if hasattr(st, "dht_nodes") else 0

    if i % 2 == 0 or ts.has_metadata or ts.num_peers > 0:
        print(f"{i+1:>4d} {str(ts.state):<22s} {ts.progress*100:>7.1f}% "
              f"{ts.download_rate//1024:>7d}K "
              f"{ts.num_peers:>5d} {ts.num_seeds:>5d} {dht_n:>5d}")

    if ts.has_metadata and ts.num_peers > 0:
        print(f"\n*** CONECTADO! {ts.num_peers} peers, {ts.num_seeds} seeds ***")
        if ts.download_rate > 0:
            print(f"*** BAIXANDO! {ts.download_rate//1024} KB/s ***")
            break

print(f"\nResultado final:")
print(f"  Metadados: {'SIM' if ts.has_metadata else 'NAO'}")
print(f"  Estado: {ts.state}")
print(f"  Progresso: {ts.progress*100:.1f}%")
print(f"  Donwload rate: {ts.download_rate//1024} KB/s")
print(f"  Peers: {ts.num_peers}")
print(f"  Seeds: {ts.num_seeds}")
print(f"  DHT nodes: {dht_n}")

ses.remove_torrent(handle)
print("OK")
