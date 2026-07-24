"""Teste para verificar o tipo e comportamento dos estados libtorrent."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import libtorrent as lt
import time

# Verificar a classe states
st_enum = lt.torrent_status.states
print("torrent_status.states members:")
for name in dir(st_enum):
    if not name.startswith("_"):
        val = getattr(st_enum, name)
        try:
            int_val = int(val)
            print(f"  {name}: {val!r} -> str={str(val)} -> int={int_val}")
        except (TypeError, ValueError):
            print(f"  {name}: {val!r} (nao enum val)")

# Agora testar com handle.status()
print("\nCriando sessao e adicionando magnet...")
ses = lt.session()
s = ses.get_settings()
s["alert_mask"] = int(lt.alert.category_t.error_notification | lt.alert.category_t.status_notification)
ses.apply_settings(s)
ses.add_dht_router("router.bittorrent.com", 6881)
ses.start_dht()

params = lt.add_torrent_params()
params.url = "magnet:?xt=urn:btih:2c16fc21ab0c37aebeef7df0f08deb9b7a9c2942&dn=ubuntu"
params.save_path = "."
params.flags &= ~lt.torrent_flags.auto_managed
handle = ses.add_torrent(params)
time.sleep(1)

ts = handle.status()
print("\nhandle.status() fields:")
print(f"  state: {ts.state!r}")
print(f"  str(state): {str(ts.state)}")
print(f"  int(state): {int(ts.state)}")
print(f"  progress: {ts.progress}")
print(f"  has_metadata: {ts.has_metadata}")
print(f"  type(state): {type(ts.state)}")

# Comparação com enum
print("\nComparacoes:")
print(f"  state == downloading_metadata: {ts.state == lt.torrent_status.states.downloading_metadata}")
print(f"  state == downloading: {ts.state == lt.torrent_status.states.downloading}")

# Dict de estados
print("\nState map:")
for name in ["queued_for_checking", "checking_files", "downloading_metadata",
             "downloading", "finished", "seeding", "allocating", "checking_resume_data"]:
    val = getattr(lt.torrent_status.states, name)
    print(f'  state_map["{name}"] = "{str(val)}"  (int: {int(val)})')

# Como usar como chave de tradução
state_key = str(ts.state)
print(f"\n  str(state) = '{state_key}'")
print(f"  Isso pode ser usado como chave de traducao")
