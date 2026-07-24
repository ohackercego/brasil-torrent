import os
import re
import math


def format_size(size_bytes: int) -> str:
    """Formata bytes em formato legível (KB, MB, GB, TB)."""
    if size_bytes <= 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    magnitude = int(math.floor(math.log(size_bytes, 1024)))
    if magnitude >= len(units):
        magnitude = len(units) - 1
    value = size_bytes / (1024 ** magnitude)
    return f"{value:.2f} {units[magnitude]}"


def format_speed(bytes_per_sec: int) -> str:
    """Formata velocidade em formato legível."""
    if bytes_per_sec <= 0:
        return "0 B/s"
    return format_size(bytes_per_sec) + "/s"


def format_duration(seconds: int) -> str:
    """Formata duração em formato legível."""
    if seconds < 0:
        seconds = 0
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    elif minutes > 0:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def format_eta(seconds: int) -> str:
    """Formata ETA."""
    if seconds < 0 or seconds == 8640000:  # libtorrent indefinite
        return "—"
    return format_duration(seconds)


def format_ratio(uploaded: int, downloaded: int) -> str:
    """Calcula e formata a taxa de compartilhamento."""
    if downloaded <= 0:
        return "—"
    ratio = uploaded / downloaded
    return f"{ratio:.2f}"


def format_percent(progress: float) -> str:
    """Formata progresso como porcentagem."""
    return f"{progress * 100:.1f}%"


def is_magnet_link(text: str) -> bool:
    """Verifica se o texto é um magnet link válido."""
    return text.strip().startswith("magnet:?")


def is_torrent_file(path: str) -> bool:
    """Verifica se o caminho é um arquivo .torrent."""
    return os.path.isfile(path) and path.lower().endswith(".torrent")


def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nomes de arquivo no Windows."""
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def bytes_to_int(value) -> int:
    """Converte valor para int com segurança."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
