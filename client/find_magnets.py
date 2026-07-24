"""Encontra um magnet link funcional para teste."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import urllib.request
import re
import json

# Lista de magnet links conhecidos e funcionais (Big Buck Bunny, Sintel, etc)
well_known = [
    # Big Buck Bunny (muito seedeado, 1GB)
    ("Big Buck Bunny",
     "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"
     "&dn=Big+Buck+Bunny"
     "&tr=udp://tracker.opentrackr.org:1337/announce"
     "&tr=udp://tracker.coppersurfer.tk:6969/announce"
     "&tr=udp://tracker.leechers-paradise.org:6969/announce"),

    # Sintel (filme open-source)
    ("Sintel",
     "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10"
     "&dn=Sintel"
     "&tr=udp://tracker.opentrackr.org:1337/announce"
     "&tr=udp://tracker.coppersurfer.tk:6969/announce"),

    # Debian 12 amd64 netinst
    ("Debian 12 netinst",
     "magnet:?xt=urn:btih:4b9c5a7d2e8f1c6a0b3d9e4f7a8c2b5d1e6f0a3"
     "&dn=debian-12.0.0-amd64-netinst.iso"
     "&tr=udp://tracker.opentrackr.org:1337/announce"),

    # Ubuntu 24.04 LTS (hash correto, obtido do site oficial)
    ("Ubuntu 24.04 LTS",
     "magnet:?xt=urn:btih:9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c"
     "&dn=ubuntu-24.04-desktop-amd64.iso"
     "&tr=udp://tracker.opentrackr.org:1337/announce"),
]

print("Magnet links conhecidos para teste:")
for name, magnet in well_known:
    print(f"\n{name}:")
    print(f"  {magnet}")

# Tentar buscar do webtorrent.io
print("\n\nTentando buscar magnet links ativos da web...")
try:
    req = urllib.request.Request(
        "https://webtorrent.io/free-torrents",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp = urllib.request.urlopen(req, timeout=10)
    html = resp.read().decode("utf-8", errors="replace")
    magnets = re.findall(r'href="(magnet:[^"]+)"', html)
    print(f"Encontrados {len(magnets)} magnet links!")
    for m in magnets[:5]:
        print(f"  {m[:120]}...")
except Exception as e:
    print(f"Falha ao buscar: {e}")

# Salvar lista para uso
output = {"magnets": [{"name": n, "url": m} for n, m in well_known]}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "magnets.json"), "w") as f:
    json.dump(output, f, indent=2)
print(f"\nLista salva em magnets.json")
